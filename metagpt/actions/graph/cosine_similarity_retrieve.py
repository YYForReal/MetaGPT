import asyncio
from typing import List, Dict, Any
from langchain_community.graphs import Neo4jGraph
from metagpt.actions import Action

class CosineSimilarityRetrieve(Action):
    """基于 Neo4j 和嵌入向量的余弦相似度检索操作。"""

    name: str = "CosineSimilarityRetrieve"
    graph: Neo4jGraph
    embedding_model: Any
    k: int = 50  # 要检索的前 k 个结果
    language: str = 'en'
    threshold: float = 0.8  # 余弦相似度阈值

    def get_query_embedding(self, query_text: str) -> List[float]:
        """生成用户查询的嵌入向量。"""
        return self.embedding_model.embed_query(query_text)

    def build_query(self, query_embedding: List[float], embed_key: str, desc_key: str) -> str:
        """构建基于 Neo4j 的查询语句，使用余弦相似度进行检索。"""
        query_embedding_str = str(query_embedding)
        query = f"""
        MATCH (n:KnowledgePoint)
        WHERE n.{embed_key} IS NOT NULL
        WITH n, gds.similarity.cosine(
            {query_embedding_str}, 
            n.{embed_key}
        ) AS score
        WHERE score > {self.threshold}
        RETURN n, n.{desc_key} as description, score
        ORDER BY score DESC
        LIMIT {self.k}
        """
        return query

    async def run(self, query_text: str, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        执行基于嵌入向量的余弦相似度检索操作。

        参数:
            query_text: 用户查询的文本。

        返回:
            包含节点 ID、描述信息以及相似度得分的前 k 个检索结果的列表。
        """
        embed_key = "embedding_en" if self.language == 'en' else "embedding"
        desc_key = "description_en" if self.language == 'en' else "description"

        # 获取查询文本的嵌入向量
        query_embedding = self.get_query_embedding(query_text)

        # 构建查询语句
        query = self.build_query(query_embedding, embed_key, desc_key)

        # 执行查询
        response = self.graph.query(query)
        if len(response) == 0:
            print(f"查询无果，尝试降低阈值...当前阈值：{self.threshold}")
            self.threshold -= 0.1
            response = self.graph.query(query)
            self.threshold += 0.1

        # 处理并返回结果
        results = []
        for record in response:
            node = record['n']
            score = record['score']
            results.append({
                "node_id": node['id'],
                "description": record['description'],
                "score": score
            })
        
        return results

# 测试函数
# async def main():
#     # 模拟的 Neo4j 图数据库实例
#     mock_graph = Neo4jGraph()
    
#     # 初始化嵌入模型
#     # from embeddings.azure_embedding import get_embedding_model
#     # embedding = get_embedding_model()
    
#     # 创建余弦相似度检索器实例
#     # cosine_retriever = CosineSimilarityRetrieve(graph=mock_graph, embedding_model=embedding, k=5)
    
#     # 模拟用户查询
#     user_query = "What's the HTML tag for adding a hyperlink?"
    
#     # 执行检索操作
#     cosine_results = await cosine_retriever.run(user_query)
    
#     # 打印结果
#     print("========== 检索结果 ==========")
#     for result in cosine_results:
#         print(f"Node ID: {result['node_id']}")
#         print(f"Score: {result['score']}")
#         show_desc = input("Show description? (y/n): ")
#         if show_desc == 'y':
#             print(result['description'])
#         print("-------------------------------")

# if __name__ == "__main__":
#     asyncio.run(main())
