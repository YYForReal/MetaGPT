#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   update_graph_from_mysql.py
@Time    :   2024/09/02 10:00:00
@Author  :   YYForReal
@Email   :   2572082773@qq.com
@description: Update the knowledge graph with new data from MySQL database and generate tags using LLM.
'''

from typing import Any, List
from langchain_community.graphs import Neo4jGraph
from metagpt.actions.action import Action
import asyncio
import mysql.connector
from datetime import datetime

class UpdateGraphFromMySQLAction(Action):
    def __init__(self, graph: Neo4jGraph, mysql_config: dict):
        super().__init__()
        self.graph = graph
        self.mysql_config = mysql_config

    async def run(self):
        try:
            # 连接 MySQL 数据库
            print("Connecting to MySQL database...")
            cnx = mysql.connector.connect(**self.mysql_config)
            cursor = cnx.cursor(dictionary=True)
            print("Connected to MySQL database.")

            # 更新实验数据并生成标签
            print("Updating experiment data and generating tags...")
            last_synced_question_id = self.get_last_synced_id('Experiment')
            print(f"Last synced question ID: {last_synced_question_id}")
            # cursor.execute(
                # "SELECT question_id, title, description FROM question WHERE question_id > %s",
                # (last_synced_question_id,))

            cursor.execute(
                "SELECT question_id, title, description,html FROM question ")


            questions = cursor.fetchall()
            print(f"Fetched {len(questions)} questions from MySQL.")

            for question in questions:
                print(f"Processing experiment: {question['question_id']} - {question['title']}")
                
                # 调用 LLM 生成标签
                tags = await self.generate_tags(question['title'], question['description'])
                print(f"Generated tags for question {question['question_id']}: {tags}")

                # 更新数据库中的标签字段
                cursor.execute(
                    "UPDATE question SET tag = %s WHERE question_id = %s",
                    (str(tags), question['question_id'])
                )
                cnx.commit()  # 提交更改
                print(f"Tags for question {question['question_id']} updated in MySQL.")

                # 更新知识图谱
                question_query = """
                MERGE (e:Experiment {id: $question_id})
                SET e.title = $title,
                    e.description = $description,
                    e.tags = $tags
                """
                self.graph.query(question_query, {
                    "question_id": question['question_id'],
                    "title": question['title'],
                    "description": question['description'],
                    "tags": tags
                })
                self.set_last_synced_id('Experiment', question['question_id'])
                print(f"Experiment {question['question_id']} updated in graph.")

            cursor.close()
            cnx.close()
            print("Graph and MySQL updated successfully from MySQL data.")

        except Exception as e:
            print(f"Error updating graph from MySQL: {e}")
            return f"Error updating graph from MySQL: {e}"

    async def generate_tags(self, title: str, description: str = "", html: str = '') -> List[str]:
        """
        调用 LLM 生成实验的知识点标签。
        
        参数:
        - title: 实验标题。
        - description: 实验描述。
        
        返回:
        - 标签列表。
        """
        # 构造 prompt
        prompt = f"""基于以下实验的标题、描述、参考答案，生成实验考察到的相关知识点标签列表：
        
        示例标签1: ['HTML','<hr>','<h1>']
        示例标签2: ['CSS','CSS 浮动','CSS 动画']
        示例标签3: ['CSS','flex','CSS 选择器']
        示例标签4: ['Javascript','DOM','JS 事件']
        
        
        ## 标题: {title}\n
        
        ## 描述: {'无描述' if description == '' else description}\n
        
        ## 参考答案: {'无参考答案' if html == '' else html}

        ## 标签:"""
        # 使用 self._ask 调用 LLM
        tags_response = await self._aask(prompt)

        # 解析 LLM 返回的标签（假设返回的是一个 JSON 格式的字符串列表）
        try:
            tags = eval(tags_response) if isinstance(tags_response, str) else tags_response
            if not isinstance(tags, list):
                raise ValueError("LLM 返回的标签格式不正确")
            return tags
        except Exception as e:
            print(f"Error parsing tags from LLM response: {e}")
            return []

    def get_last_synced_id(self, entity_type: str) -> int:
        print(f"Fetching last synced ID for {entity_type}...")
        query = f"MATCH (s:SyncStatus {{type: '{entity_type}'}}) RETURN s.last_synced_id AS last_synced_id"
        result = self.graph.query(query)
        last_synced_id = result[0]['last_synced_id'] if result else 0
        print(f"Last synced ID for {entity_type}: {last_synced_id}")
        return last_synced_id

    def set_last_synced_id(self, entity_type: str, last_synced_id: int):
        print(f"Setting last synced ID for {entity_type} to {last_synced_id}...")
        query = f"""
        MERGE (s:SyncStatus {{type: '{entity_type}'}})
        SET s.last_synced_id = $last_synced_id
        """
        self.graph.query(query, {"last_synced_id": last_synced_id})
        print(f"Last synced ID for {entity_type} set to {last_synced_id}.")

# Example usage
if __name__ == "__main__":
    mysql_config = {
        'host': '172.31.73.236',
        'database': 'web',
        'user': 'web_user',
        'password': 'web123.'
    }
    graph = Neo4jGraph()
    action = UpdateGraphFromMySQLAction(graph, mysql_config)
    asyncio.run(action.run())
