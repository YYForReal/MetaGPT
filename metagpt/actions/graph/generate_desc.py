'''
Author: yy 2572082773@qq.com
Date: 2024-07-31 09:16:15
LastEditTime: 2024-08-02 09:29:01
FilePath: \code\LLM\MetaGPT\metagpt\actions\graph\generate_desc.py
Description: 

Copyright (c) 2024 by YYForReal, All Rights Reserved. 
'''
#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2024/7/31 09:50:40
@Author  : YYForReal
@File    : tutorial_assistant.py
@Describe : Actions of the tutorial assistant, including writing directories and document content.
"""

from typing import Dict

from metagpt.actions import Action
from metagpt.prompts.graph.desc import GENERATE_DESC_TEMPLATE


MAX_CONTENT_LENGTH = 80000

class GenerateDescription(Action):
    """Action class for generating a description.

    Args:
        name: The name of the action.
        source: The source data for generating the description.
        style: The style of the description, default is "Informative".
    """

    name: str = "GenerateDescription"
    kp_node: dict = dict()
    style: str = "Informative"
    language: str = "Chinese"

    async def run(self, *args, **kwargs) -> Dict:
        """Execute the action to generate a description based on the source and topic.

        Returns:
            The generated description.
        """
        content = self.kp_node['content']
        if len(content) > MAX_CONTENT_LENGTH:  # 定义一个合适的最大长度
            print("content length: ", len(content))
            print(f"id 1: {self.kp_node['id']} has been cut")
            content = content[:MAX_CONTENT_LENGTH] + "..."  # 截断过长的内容 

        prompt = GENERATE_DESC_TEMPLATE.format(id=self.kp_node['id'], content=content)

        print("prompt length:", len(prompt))
        # print("===========")

        desc = await self._aask(prompt=prompt)
        res = {
            "id":self.kp_node['id'],
            # "content":self.kp_node['content'],
            "metadata":self.kp_node['metadata'],
            "description":desc
        }
        return res


