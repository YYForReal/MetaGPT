import asyncio
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from langchain_community.graphs import Neo4jGraph
from metagpt.actions import Action

def remove_lucene_chars(text: str) -> str:
    """移除 Lucene 特殊字符，保留 ^"""
    special_chars = [
        "+", "&", "|", "!", "(", ")", "{", "}", "[", "]", '"', "~", "*", "?", ":", "\\"
    ]
    for char in special_chars:
        if char in text:
            text = text.replace(char, " ")
    return text.strip()

class BM25Retrieve(Action):
    """基于 BM25 算法的检索操作，用于检索 Neo4j 图节点的描述信息。"""

    name: str = "BM25Retrieve"
    graph: Neo4jGraph
    language: str = 'en'
    k: int = 5  # 要检索的前k个结果
    corpus: List[str] = []  # 文档语料库
    bm25: BM25Okapi = None  # BM25 实例
    node_descriptions: Dict[str, str] = {}  # 节点描述

    def preprocess_text(self, text: str) -> str:
        """文本预处理，如分词和去除特殊字符。"""
        print(f"预处理文本: {text}")
        processed_text = remove_lucene_chars(text)
        print(f"预处理后: {processed_text}")
        return processed_text

    def build_corpus(self):
        """从 Neo4j 图节点描述中构建 BM25 的语料库。"""
        print("正在构建 BM25 语料库...")
        desc_title = "description_en" if self.language == 'en' else "description"
        query = f"MATCH (n) RETURN n.id AS id, n.{desc_title} AS description"
        results = self.graph.query(query)

        for record in results:
            node_id = record['id']
            description = record['description']
            if description:
                preprocessed_description = self.preprocess_text(description)
                self.corpus.append(preprocessed_description)
                self.node_descriptions[node_id] = preprocessed_description

        print(f"总计添加 {len(self.corpus)} 个文档到语料库中。")
        self.bm25 = BM25Okapi([doc.split(" ") for doc in self.corpus])
        print("BM25 语料库构建完成。")

    async def run(self, question: str, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        执行 BM25 检索操作。

        参数:
            question: 用户查询的问题。

        返回:
            包含节点 ID、描述信息以及 BM25 分数的前 k 个检索结果的列表。
        """
        if not self.bm25:
            self.build_corpus()

        # 预处理用户查询问题
        print(f"用户查询: {question}")
        preprocessed_question = self.preprocess_text(question)

        # 获取 BM25 得分
        print("计算 BM25 得分...")
        scores = self.bm25.get_scores(preprocessed_question.split(" "))
        print(f"BM25 得分: {scores}")

        # 根据得分检索前 k 个结果
        top_k_indices = scores.argsort()[-self.k:][::-1]
        print(f"前 {self.k} 个结果的索引: {top_k_indices}")

        top_k_results = [
            {"node_id": node_id, "description": self.corpus[idx], "score": scores[idx]}
            for idx, node_id in enumerate(self.node_descriptions) if idx in top_k_indices
        ]

        # 排序结果
        top_k_results.sort(key=lambda x: x['score'], reverse=True)
        # 打印前 k 个结果及其 BM25 得分
        print("前 k 个结果及其 BM25 分数：")
        for result in top_k_results:
            print(f"节点ID: {result['node_id']}, 描述: {result['description']}, 分数: {result['score']}")

        return top_k_results


# 测试函数
async def main():
    # 模拟的 Neo4j 图数据库实例
    mock_graph = Neo4jGraph()
    
    # 创建 BM25 检索器实例
    bm25_retriever = BM25Retrieve(graph=mock_graph, k=5)
    
    # 模拟用户查询
    user_query = "JavaScript objects are containers for named values."
    
    # 执行检索操作
    bm25_results = await bm25_retriever.run(user_query)
    
    # 打印结果
    print("========== 检索结果 ==========")
    for result in bm25_results:
        print(f"Node ID: {result['node_id']}")
        print(f"Description: {result['description']}")
        print("-------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
