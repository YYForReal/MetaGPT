#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   update_pagerank.py
@Time    :   2024/08/12 22:23:53
@Author  :   YYForReal 
@Email   :   2572082773@qq.com
@description   : Update the PageRank of nodes in the knowledge graph.
'''


from typing import Any
from langchain_community.graphs import Neo4jGraph
from metagpt.actions.action import Action
import asyncio


class UpdatePageRankAction(Action):
    def __init__(self, graph: Neo4jGraph):
        super().__init__()
        self.graph = graph

    async def run(self):
        try:
            # 获取所有关系类型
            relationship_types_query = """
            CALL db.relationshipTypes() YIELD relationshipType
            RETURN collect(relationshipType) AS relationshipTypes
            """
            relationship_types_result = self.graph.query(relationship_types_query)
            relationship_types = relationship_types_result[0]['relationshipTypes']
            
            print(f"Found {len(relationship_types)} relationship types.")
            print(f"Relationship types: {relationship_types}")
            
            # 删除现有图投影（如果存在）
            drop_graph_projection_query = """
            CALL gds.graph.exists('myGraph')
            YIELD exists
            WITH exists
            WHERE exists
            CALL gds.graph.drop('myGraph') YIELD graphName
            RETURN graphName
            """
            drop_result = self.graph.query(drop_graph_projection_query)
            if drop_result:
                print(f"Dropped existing graph projection: {drop_result}")
            
            # 创建图投影
            create_graph_projection_query = """
            CALL gds.graph.project(
                'myGraph',
                'KnowledgePoint',
                $relationshipProjection
            )
            """
            relationship_projection = {rtype: {} for rtype in relationship_types}
            self.graph.query(create_graph_projection_query, {"relationshipProjection": relationship_projection})
            
            print("Graph projection created successfully.")
            
            # 运行 PageRank 并写入结果
            run_pagerank_query = """
            CALL gds.pageRank.write(
                'myGraph',
                {
                    relationshipTypes: $relationshipTypes,
                    relationshipWeightProperty: null,
                    writeProperty: 'rank'
                }
            )
            YIELD nodePropertiesWritten, ranIterations
            """
            pagerank_result = self.graph.query(run_pagerank_query, {"relationshipTypes": relationship_types})
            
            print(f"PageRank update result: {pagerank_result}")
            print("PageRank updated successfully.")
            return pagerank_result
        except Exception as e:
            print(f"Error updating PageRank: {e}")
            return "Error updating PageRank: {}".format(e)


# Example usage
if __name__ == "__main__":
    graph = Neo4jGraph()
    action = UpdatePageRankAction(graph)
    asyncio.run(action.run())
