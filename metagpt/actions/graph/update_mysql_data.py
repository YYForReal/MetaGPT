#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   update_graph_from_mysql.py
@Time    :   2024/09/02 10:00:00
@Author  :   YYForReal
@Email   :   2572082773@qq.com
@description: Update the knowledge graph with new data from MySQL database.
'''

from typing import Any
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

            # 1. 更新用户数据
            print("Updating user data...")
            last_synced_user_id = self.get_last_synced_id('Person')
            print(f"Last synced user ID: {last_synced_user_id}")
            cursor.execute(
                "SELECT user_id, username, semester, description, type FROM users WHERE user_id > %s",
                (last_synced_user_id,))
            users = cursor.fetchall()
            print(f"Fetched {len(users)} users from MySQL.")
            for user in users:
                user_type = "Student" if user['type'] == 0 else "Teacher"
                print(f"Updating user: {user['user_id']} - {user['username']}")
                user_query = """
                MERGE (p:Person {id: $user_id})
                SET p.name = $username,
                    p.semester = $semester,
                    p.description = $description,
                    p.type = $type
                """
                self.graph.query(user_query, {
                    "user_id": user['user_id'],
                    "username": user['username'],
                    "semester": user['semester'],
                    "description": user['description'],
                    "type": user_type
                })
                self.set_last_synced_id('Person', user['user_id'])
                print(f"User {user['user_id']} updated.")

            # 2. 更新实验数据
            print("Updating experiment data...")
            last_synced_question_id = self.get_last_synced_id('Experiment')
            print(f"Last synced question ID: {last_synced_question_id}")
            cursor.execute(
                "SELECT question_id, title, description, html FROM question WHERE question_id > %s",
                (last_synced_question_id,))
            questions = cursor.fetchall()
            print(f"Fetched {len(questions)} questions from MySQL.")
            for question in questions:
                print(f"Updating experiment: {question['question_id']} - {question['title']}")
                question_query = """
                MERGE (e:Experiment {id: $question_id})
                SET e.title = $title,
                    e.description = $description,
                    e.html = $html
                """
                self.graph.query(question_query, {
                    "question_id": question['question_id'],
                    "title": question['title'],
                    "description": question['description'],
                    "html": question['html']
                })
                self.set_last_synced_id('Experiment', question['question_id'])
                print(f"Experiment {question['question_id']} updated.")

            # 3. 更新答案数据并创建关系
            print("Updating answer data and creating relationships...")
            last_synced_answer_time = self.get_last_synced_time('Answer')
            print(f"Last synced answer time: {last_synced_answer_time}")
            cursor.execute(
                "SELECT answer_id, question_id, user_id, content, description, score, submit_times, update_time, release_time "
                "FROM answers WHERE update_time > %s", (last_synced_answer_time,))
            answers = cursor.fetchall()
            print(f"Fetched {len(answers)} answers from MySQL.")
            for answer in answers:
                print(f"Updating answer: {answer['answer_id']} for question {answer['question_id']}, user {answer['user_id']}")
                answer_query = """
                MATCH (p:Person {id: $user_id})
                MATCH (e:Experiment {id: $question_id})
                MERGE (p)-[r:SUBMITTED_ANSWER {id: $answer_id}]->(e)
                SET r.content = $content,
                    r.description = $description,
                    r.score = $score,
                    r.submit_times = $submit_times,
                    r.update_time = datetime($update_time),
                    r.release_time = datetime($release_time)
                """
                self.graph.query(answer_query, {
                    "answer_id": answer['answer_id'],
                    "question_id": answer['question_id'],
                    "user_id": answer['user_id'],
                    "content": answer['content'],
                    "description": answer['description'],
                    "score": answer['score'],
                    "submit_times": answer['submit_times'],
                    "update_time": answer['update_time'].isoformat(),
                    "release_time": answer['release_time'].isoformat()
                })
                self.set_last_synced_time('Answer', answer['update_time'])
                print(f"Answer {answer['answer_id']} updated.")

            cursor.close()
            cnx.close()
            print("Graph updated successfully from MySQL data.")

        except Exception as e:
            print(f"Error updating graph from MySQL: {e}")
            return f"Error updating graph from MySQL: {e}"

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

    def get_last_synced_time(self, entity_type: str) -> datetime:
        print(f"Fetching last synced time for {entity_type}...")
        query = f"MATCH (s:SyncStatus {{type: '{entity_type}'}}) RETURN s.last_synced_time AS last_synced_time"
        result = self.graph.query(query)
        last_synced_time = result[0]['last_synced_time'] if result else datetime(1970, 1, 1)
        print(f"Last synced time for {entity_type}: {last_synced_time}")
        return last_synced_time

    def set_last_synced_time(self, entity_type: str, last_synced_time: datetime):
        print(f"Setting last synced time for {entity_type} to {last_synced_time}...")
        query = f"""
        MERGE (s:SyncStatus {{type: '{entity_type}'}})
        SET s.last_synced_time = datetime($last_synced_time)
        """
        self.graph.query(query, {"last_synced_time": last_synced_time.isoformat()})
        print(f"Last synced time for {entity_type} set to {last_synced_time}.")

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
