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
from metagpt.prompts.graph.desc import GENERATE_DESC_TEMPLATE, GENERATE_DESC_TEMPLATE_EN
from typing import Any
from langchain_community.graphs import Neo4jGraph

import re
from urllib.parse import urljoin
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
    language: str = ""

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

        # if self.language == "Chinese":
        prompt = GENERATE_DESC_TEMPLATE.format(id=self.kp_node['id'], content=content)
        desc = await self._aask(prompt=prompt)
        # else:

        prompt = GENERATE_DESC_TEMPLATE_EN.format(id=self.kp_node['id'], content=content)
        desc_en = await self._aask(prompt=prompt)


        # print("prompt length:", len(prompt))
        # print("===========")



        res = {
            "id":self.kp_node['id'],
            # "content":self.kp_node['content'],
            "metadata":self.kp_node['metadata'],
            "description":desc,
            "description_en":desc_en,
        }
        return res

# for test and not participate in the project

class UpdateDescriptionURL(Action):
    graph:Neo4jGraph = None
    base_url:str = ""

    def run(self):
        self.update_description()
        self.update_description("description_en")
        

    def update_description(self,field_name="description"):
        try:
            # 获取所有带有description字段的知识点节点
            query = f"""
MATCH (kp:KnowledgePoint)
WHERE kp.{field_name} IS NOT NULL
RETURN kp
            """
            knowledge_points = self.graph.query(query)

            # 遍历节点并更新字段
            for kp in knowledge_points:
                kp_id = kp['kp']['id']
                original_value = kp['kp'][field_name]
                # updated_value = update_function(original_value, self.base_url)
                # 假设的detect_and_complete_links函数
                updated_value = self.detect_and_complete_links(original_value, self.base_url)
                
                # 更新节点的字段
                update_query = f"""
                MATCH (kp:KnowledgePoint {{id: $kp_id}})
                SET kp.{field_name} = $updated_value
                """
                self.graph.query(update_query, params = {
                    "kp_id":kp_id, 
                    "updated_value":updated_value
                })
                print(f"Updated {field_name} for KnowledgePoint with id: {kp_id}")
                if original_value != updated_value:
                    print("Description updated successfully.")
                    print("after:",updated_value)
                else:
                    print("No changes to the description.")

        except Exception as e:
            print(f"Error updating descriptions: {e}")



    def detect_and_complete_links(self, text: str, baseURL: str) -> str:
        """
        检测文本中是否存在超链接，并补全相对路径的链接。
        
        参数:
        - text: 要检测的文本。
        - baseURL: 用于补全相对路径的基本 URL。
        
        返回:
        - 补全后的文本。
        """
        # 正则表达式模式，用于匹配 Markdown 格式的链接
        pattern = r'\[(.*?)\]\((.*?)\)'

        def replace_relative_links(match):
            link_text = match.group(1)
            link_url = match.group(2)

            # 判断是否是相对路径（例如：不以 'http://'、'https://' 或 '//' 开头的路径）
            if not re.match(r'^(http://|https://|//)', link_url):
                # 补全相对路径为绝对路径
                link_url = urljoin(baseURL, link_url)
            
            # 返回补全后的链接格式
            return f"[{link_text}]({link_url})"

        # 使用 re.sub 替换相对路径链接
        updated_text = re.sub(pattern, replace_relative_links, text)
        return updated_text


# Example usage
if __name__ == "__main__":
    base_url = "https://www.w3school.com.cn"
    graph = Neo4jGraph()
    action = UpdateDescriptionURL(graph = graph, base_url= base_url)
    action.run()

