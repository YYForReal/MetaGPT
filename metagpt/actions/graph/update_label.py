#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   update_label_action.py
@Time    :   2024/07/31 10:43:19
@Author  :   YYForReal 
@Email   :   2572082773@qq.com
@description   :   Update the labels of nodes in the knowledge graph.
'''

from typing import Any
from langchain_community.graphs import Neo4jGraph
from metagpt.actions.action import Action

class UpdateLabelAction(Action):
    def __init__(self, graph: Neo4jGraph):
        self.graph = graph

    def run(self):
        try:
            add_label_query = """
            MATCH (n)
            WHERE any(label in labels(n) WHERE label IN ['KnowledgePoint', 'Example', 'Image', 'URL', 'Attribute', 'Method'])
            SET n:__Entity__
            """
            self.graph.query(add_label_query)
            self.graph.query("CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")
        except Exception as e:
            print(f"Error updating labels: {e}")

# Example usage
if __name__ == "__main__":
    graph = Neo4jGraph()
    action = UpdateLabelAction(graph)
    action.run()
