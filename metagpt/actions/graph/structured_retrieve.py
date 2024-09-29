from typing import List
from metagpt.actions import Action
import asyncio
from langchain_community.graphs import Neo4jGraph


MAX_CONTENT_LENGTH = 80000

def remove_lucene_chars(text: str) -> str:
    """Remove Lucene special characters except ^ """
    special_chars = [
        "+",
        "&",
        "|",
        "!",
        "(",
        ")",
        "{",
        "}",
        "[",
        "]",
        '"',
        "~",
        "*",
        "?",
        ":",
        "\\",
    ]
    for char in special_chars:
        if char in text:
            text = text.replace(char, " ")
    return text.strip()


class StructuredRetrieve(Action):
    """Action class for structured retrieval of entity neighborhoods."""

    name: str = "StructuredRetrieve"
    entities: List[str] = []
    graph: Neo4jGraph
    language: str = 'en'
    k: int = 2  # Default value for limit

    def update_index(self) -> None:
        """
        Update the index of the graph with a list of entities.
        """
        add_label_query = """
        MATCH (n)
        WHERE any(label in labels(n) WHERE label IN ['KnowledgePoint', 'Example', 'Image', 'URL', 'Attribute', 'Method'])
        SET n:__Entity__
        """
        self.graph.query(add_label_query)

        self.graph.query(
            "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id, e.description]"
        )

    def generate_query(self, query: str) -> str:
        """
        Generate a Neo4j query string based on the provided entity query.
        """
        desc_key = "description_en" if self.language == 'en' else "description"
        query_template = f"""
        CALL db.index.fulltext.queryNodes('entity', $query, {{limit:{self.k}}})
        YIELD node, score
        WITH node, score, COALESCE(node.{desc_key}, '') AS {desc_key}
        CALL {{
            WITH node, score
            MATCH (n)-[r]->(neighbor)
            WHERE n.id = node.id
            RETURN n.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
            UNION
            WITH node, score
            MATCH (n)<-[r]-(neighbor)
            WHERE n.id = node.id
            RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  n.id AS output
        }}
        RETURN node, {desc_key}, output, score LIMIT 50
        """
        return query_template

    async def run(self, entities: List[str] = [], *args, **kwargs) -> str:
        """
        Execute the action to collect the neighborhood of entities mentioned in the question.
        """
        self.update_index()
        result = ""
        all_ids = []
        all_rels = []

        nodes = []
        for entity in entities:
            print("search entity:", entity)

            query = remove_lucene_chars(entity)
            query_str = self.generate_query(query)
            desc_title = "description_en" if self.language == 'en' else "description"
            relationship_title = 'output'

            response = self.graph.query(query_str, {"query": query})
            # ids = sorted(list(set([
            #     f"**{el['node']['id']}**  (score:{el['score']}) {desc_title}: {el[desc_title]}" if el[desc_title] else '' for el in response
            # ])))

            # 先根据score进行排序，再生成带有ID和描述的字符串列表
            sorted_response = sorted(response, key=lambda el: el['score'], reverse=True)

            # 生成排序后的字符串列表
            ids = [
                f"**{el['node']['id']}**  (score:{el['score']:2f}) {desc_title}: {el[desc_title]}" 
                for el in sorted_response if el[desc_title]
            ]

            # 去重并保留排序后的结果
            ids = list(dict.fromkeys(ids))
            nodes.extend([el['node']['id']  for el in sorted_response if el['node']['id']  ])

            neighbor_relationships = sorted(list(
                set([el[relationship_title] if el[relationship_title] else '' for el in response])
            ))
            
            neighbor_relationships = [el for el in neighbor_relationships if el != '']

            if len(ids) > 0:
                result += "\n\n**entities**:\n"
                result += "\n\n".join(ids) 
            if len(neighbor_relationships) > 0:
                result += "\n\n**relationships**:\n"
                result += "\n".join(neighbor_relationships)

            all_ids.extend(ids)
            all_rels.extend(neighbor_relationships)

        return result, all_ids, all_rels , nodes 


# Example usage
async def main():
    entities = ["查找字符串中特定文本首次和最后出现位置的方法"]
    retriever_action = StructuredRetrieve(graph=Neo4jGraph(), k=3,language="")  # Set k=3 for the limit
    structured_result, ids, all_rels = await retriever_action.run(entities=entities)
    print("==========")
    print(structured_result)
    print("==========")
    print("ids", ids)
    print("==========")
    print("all_rels", all_rels)


if __name__ == "__main__":
    asyncio.run(main())
