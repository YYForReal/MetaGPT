import os
from dotenv import load_dotenv
import networkx as nx
from pyvis.network import Network
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from metagpt.tools.tool_registry import register_tool
from graphdatascience import GraphDataScience

# 加载.env文件中的环境变量
load_dotenv()


@register_tool(
    tags=["graph", "neo4j graph"],
    include_functions=[
        "__init__",
        "add_documents_to_graph",
        "show_graph",
        "get_schema",
        "get_subgraph",
        "custom_query",
        "update_entity_labels",  # 注册新的函数
    ],
)
class GraphController:
    """A controller for managing and visualizing graphs using Neo4j."""

    def __init__(self):
        """Initialize the GraphController with Neo4j connection."""
        self.graph = Neo4jGraph()

    def add_documents_to_graph(self, graph_documents, llm):
        """Add documents to the graph.

        Args:
            graph_documents (list): List of documents to add to the graph.
            llm (LLM): Language model instance for transformation.
        """
        llm_transformer = LLMGraphTransformer(llm=llm)
        graph_documents = llm_transformer.convert_to_graph_documents(
            graph_documents)
        self.graph.add_graph_documents(
            graph_documents, base_entity_label=True, include_source=True
        )

    def get_schema(self):
        """Get the schema of the graph."""
        self.graph.refresh_schema()
        return self.graph.get_schema

    def get_subgraph(self, node_id: str, depth: int = 1, output_html: str = ""):
        """Get the subgraph of a node up to a certain depth.

        Args:
            node_id (str): The ID of the starting node.
            depth (int): The depth of the subgraph to retrieve. Default is 1.
            output_html (str): The path to save the visualized subgraph as an HTML file. Default is an empty string.

        Returns:
            list: List of relationships in the subgraph.
        """
        cypher = f"""
        MATCH (n {{id: '{node_id}'}})-[r*1..{depth}]-(m)
        RETURN n, r, m
        """
        result = self.graph.query(cypher)

        relationships = []
        G = nx.MultiDiGraph()

        for record in result:
            source = record["n"]
            target = record["m"]
            rels = record["r"]

            for rel in rels:
                relationships.append(rel)
                G.add_edge(source["id"], target["id"], label=rel)

        # Visualize the graph and save to HTML if specified
        if output_html:
            if not output_html.endswith(".html"):
                raise ValueError("Output file must be an HTML file")
            net = Network(notebook=False, directed=True)
            net.from_nx(G)
            net.show(output_html)

        return relationships

    def custom_query(self, cypher: str):
        """Execute a custom Cypher query and return the results.

        Args:
            cypher (str): The custom Cypher query to execute.

        Returns:
            list: List of query results.
        """
        result = self.graph.query(cypher)
        return result

    def update_entity_labels(self):
        """Update the labels of nodes in the graph to include __Entity__."""
        try:
            add_label_query = """
            MATCH (n)
            WHERE any(label in labels(n) WHERE label IN ['KnowledgePoint', 'Example', 'Image', 'URL', 'Attribute', 'Method'])
            SET n:__Entity__
            """
            self.graph.query(add_label_query)
            self.graph.query(
                "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")
        except Exception as e:
            print(f"Error updating labels: {e}")

    def find_potential_duplicates_by_edit_distance(self, distance: int = 3):
        """Find potential duplicate nodes based on text edit distance.

        Args:
            distance (int): The maximum text edit distance to consider nodes as potential duplicates. default is 3.

        Returns:
            list: List of potential duplicate node groups.
        """

        gds = GraphDataScience(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
        )
        graph_name = "entities"

        # 检查图是否存在
        graph_exists = gds.graph.exists(graph_name)
        if graph_exists['exists']:
            # 删除现有图
            gds.graph.drop(graph_name)
            print(f"Graph '{graph_name}' dropped.")
        else:
            print(f"Graph '{graph_name}' does not exist.")

        G, result = gds.graph.project(
            graph_name,  # Graph name
            "KnowledgePoint",  # Node projection
            "*",  # Relationship projection
            nodeProperties=["embedding"]  # Configuration parameters
        )

        similarity_threshold = 0.95

        gds.knn.mutate(
            G,
            nodeProperties=['embedding'],
            mutateRelationshipType='SIMILAR',
            mutateProperty='score',
            similarityCutoff=similarity_threshold
        )

        # Weakly Connected Components
        gds.wcc.write(
            G,
            writeProperty="wcc",
            relationshipTypes=["SIMILAR"]
        )

        cypher = """
MATCH (e:`KnowledgePoint`)
WHERE size(toString(e.id)) > 4 // longer than 4 characters
WITH e.wcc AS community, collect(e) AS nodes, count(*) AS count
WHERE count > 1
UNWIND nodes AS node
// Add text distance
WITH distinct
    [n IN nodes WHERE apoc.text.distance(toLower(node.id), toLower(n.id)) < $distance | n.id] AS intermediate_results
WHERE size(intermediate_results) > 1
WITH collect(intermediate_results) AS results
// combine groups together if they share elements
UNWIND range(0, size(results)-1, 1) as index
WITH results, index, results[index] as result
WITH apoc.coll.sort(reduce(acc = result, index2 IN range(0, size(results)-1, 1) |
    CASE WHEN index <> index2 AND
        size(apoc.coll.intersection(acc, results[index2])) > 0
        THEN apoc.coll.union(acc, results[index2])
        ELSE acc
    END
)) as combinedResult
WITH distinct(combinedResult) as combinedResult
// extra filtering
WITH collect(combinedResult) as allCombinedResults
UNWIND range(0, size(allCombinedResults)-1, 1) as combinedResultIndex
WITH allCombinedResults[combinedResultIndex] as combinedResult, combinedResultIndex, allCombinedResults
WHERE NOT any(x IN range(0,size(allCombinedResults)-1,1)
    WHERE x <> combinedResultIndex
    AND apoc.coll.containsAll(allCombinedResults[x], combinedResult)
)
RETURN combinedResult
        """
        result = self.graph.query(cypher, params={'distance': distance})
        return result


# Example usage
if __name__ == "__main__":
    graph_controller = GraphController()
    graph_controller.update_entity_labels()
