from typing import List
from metagpt.actions import Action
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
import asyncio
from langchain_community.graphs import Neo4jGraph


MAX_CONTENT_LENGTH = 80000

def generate_full_text_query(input: str) -> str:
    """
    Generate a full-text search query for a given input string.

    This function constructs a query string suitable for a full-text search.
    It processes the input string by splitting it into words and appending a
    similarity threshold (~2 changed characters) to each word, then combines
    them using the AND operator. Useful for mapping entities from user questions
    to database values, and allows for some misspellings.
    """
    full_text_query = ""
    # words = [el for el in remove_lucene_chars(input).split() if el]
    words = [el for el in input.split() if el]


    # mohu = min(len(words)//2, 2)
    for word in words[:-1]:
        full_text_query += f" {word} OR "
    full_text_query += f" {words[-1]}"

    #     full_text_query += f" {word}~{mohu} OR "
    # full_text_query += f" {words[-1]}~{mohu}"


    print("full text query ",full_text_query)
    return full_text_query.strip()

class StructuredRetrieve(Action):
    """Action class for structured retrieval of entity neighborhoods."""

    name: str = "StructuredRetrieve"
    entities:List[str] = []
    graph: Neo4jGraph

    def update_index(self) -> None:
        """
        Update the index of the graph with a list of entities.
        """
        # 添加 __Entity__ 标签
        add_label_query = """
        MATCH (n)
        WHERE any(label in labels(n) WHERE label IN ['KnowledgePoint', 'Example', 'Image', 'URL', 'Attribute', 'Method'])
        SET n:__Entity__
        """
        self.graph.query(add_label_query)

        # 创建全文索引
        self.graph.query(
            "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]"
        )



    async def run(self, *args, **kwargs) -> str:
        """
        Execute the action to collect the neighborhood of entities mentioned in the question.

        Args:
            entities: A list of entities extracted from the question.

        Returns:
            The collected neighborhood of entities.
        """
        self.update_index()
        result = ""
        entity_desc = []

        for entity in self.entities:
            print("sr entity:", entity)

            query = generate_full_text_query(entity) if len(entity)>5 else 'property CONTAINS "'+entity+'"'
            print("sr query:", query)
            
            # response = self.graph.query(
            #     """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
            #     YIELD node,score
            #     WITH node, score
            #     CALL {
            #       MATCH (node)-[r]->(neighbor)
            #       RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
            #       UNION
            #       MATCH (node)<-[r]-(neighbor)
            #       RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
            #     }
            #     RETURN output LIMIT 50
            #     """,
            #     {"query": query},
            # )
            response = self.graph.query(
"""CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
YIELD node,score
WITH node, score, COALESCE(node.description, '') AS description
CALL {
    WITH node
    MATCH (n)-[r]->(neighbor)
    WHERE n.id = node.id
    RETURN n.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
    UNION
    WITH node
    MATCH (n)<-[r]-(neighbor)
    WHERE n.id = node.id
    RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  n.id AS output
}
RETURN node, description, output  LIMIT 50
""",
{"query": query},
)


            # print("==============")
            # print("response:", response)
            key = 'id'

            ids = list(set([("\n**"+el['node']['id'] + ' description**: ' + el['description']) if el['description'] else '' for el in response]))
            ids = sorted(ids)            
            
            key = 'output'
            response = list(set([el[key] if el[key] else '' for el in response]))
            response = sorted(response)            
            result += "\n\n".join(ids) + "\n============\n图关系：" + "\n".join(response)

        return result


# Example usage
async def main():
    entities = ["HTML p标签"]
    retriever_action = StructuredRetrieve(entities=entities,graph=Neo4jGraph())
    structured_result = await retriever_action.run()
    print("==========")
    print(structured_result)



if __name__ == "__main__":
    asyncio.run(main())




# embedding 相似度 demo （待测试）
# response = self.graph.query(
#     f"""
#     CALL apoc.periodic.iterate(
#       'MATCH (n:__Entity__) RETURN n',
#       'WITH n, gds.alpha.similarity.cosine({{node1: {query_embedding_str}, node2: n.embedding}}) AS score
#        WHERE score > 0.8
#        RETURN n, score',
#       {{batchSize: 1000, iterateList: true}}
#     ) YIELD batches, total
#     RETURN n, score
#     ORDER BY score DESC
#     LIMIT 50
#     """
# )

# for record in response:
#     print(record)
