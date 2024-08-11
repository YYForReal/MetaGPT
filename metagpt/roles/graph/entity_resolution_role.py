#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   entity_resolution_role.py
@Time    :   2024/07/31 10:43:19
@Author  :   YYForReal 
@Email   :   2572082773@qq.com
@description   :   Entity resolution role, input a list of entities to identify and merge duplicates.
'''

from datetime import datetime
from typing import Dict, List, Optional
import os
import json
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
# from metagpt.actions import Action
from metagpt.utils.common import OutputParser
from metagpt.actions.graph.entity_resolution import EntityResolution
from metagpt.tools.libs.graph_controller import GraphController
from metagpt.logs import logger

class EntityResolutionRole(Role):
    """Entity resolution role, input a list of entities to identify and merge duplicates.

    Args:
        name: The name of the role.
        profile: The role profile description.
        goal: The goal of the role.
        constraints: Constraints or requirements for the role.
        language: The language in which the output will be generated.
    """

    name: str = "EntityResolution"
    profile: str = "Entity Resolution Role"
    goal: str = "Identify and merge duplicate entities"
    constraints: str = "Strictly follow with concise and standardized layout."
    language: str = "Chinese"

    topic: str = ""
    source_path: str = "./output/"
    entities: List[str] = []
    merged_entities: List[str] = []

    def __init__(self, entities: List[str] = [], **kwargs):
        super().__init__(**kwargs)
        self.entities = entities
        
        self.graph_controller = GraphController()

        if self.entities == []:
            logger.info("No entities provided. using graph to find potential duplicates.")
            self.entities = self.graph_controller.find_potential_duplicates_by_edit_distance()
            print(self.entities)

        actions = []
        for entities in self.entities:
            # self.graph_controller.add_node(label="Entity", properties={"name": entity})
            print("add ",entities['combinedResult'])
            actions.append(EntityResolution(entities=entities['combinedResult']))

        self.set_actions(actions)
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        """Perform the entity resolution action.

        Returns:
            A message containing the result of the action.
        """
        todo = self.rc.todo
        try:
            result = await todo.run(topic=self.topic)
            print('role result:',result)
            self.merged_entities = result.get("merge_entities", [])
        except Exception as e:
            logger.error(e)

        return Message(content=str(self.merged_entities), role=self.profile)

    async def react(self) -> Message:
        """React to the task and perform actions in sequence.

        Returns:
            A message containing the final result.
        """
        msg = await super().react()
        # root_path = os.path.dirname()
        output_path = os.path.join(self.source_path, f"{self.topic}_merged_entities.json")
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(self.merged_entities, file, ensure_ascii=False)
        msg.content = output_path
        return msg

# Example usage
if __name__ == "__main__":
    entities = ['Star Ocean The Second Story R', 'Star Ocean: The Second Story R']
    role = EntityResolutionRole(entities=entities, topic="Example Topic",source_path = "E:\code\MetaKGRAG\Pipeline\output\Example Topic.json")
    message = role.react()
    print(f"Merged entities saved to: {message.content}")

