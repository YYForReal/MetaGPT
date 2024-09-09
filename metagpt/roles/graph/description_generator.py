#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   description_generator.py
@Time    :   2024/07/31 10:43:19
@Author  :   YYForReal 
@Email   :   2572082773@qq.com
@description   :   Description generator, input topic and source_path to generate descriptions for nodes.
'''


from datetime import datetime
from typing import Dict, List
import re
from urllib.parse import urljoin
import os

from metagpt.actions.graph.generate_desc import GenerateDescription
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.actions import Action
import json

class DescriptionGenerator(Role):
    """Description generator, input topic and source_path to generate descriptions for nodes.

    Args:
        name: The name of the role.
        profile: The role profile description.
        goal: The goal of the role.
        constraints: Constraints or requirements for the role.
        language: The language in which the tutorial documents will be generated.
        source_path: The path to the source file containing node data.
    """

    name: str = "Stitch"
    profile: str = "Description Generator"
    goal: str = "Generate descriptions for nodes"
    constraints: str = "Strictly follow with concise and standardized layout."
    language: str = ""

    topic: str = ""
    source_path: str = ""
    kp_nodes: List[Dict] = []
    output_nodes: List[Dict] = [] 
    
    total_content: str = ""
    finish_count: int = 0

    def __init__(self, source_path: str, **kwargs):
        super().__init__(**kwargs)
        self.source_path = source_path
        self.set_actions(self._handle_nodes())
        print(self.actions)
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    def _read_file(self) -> List[Dict]:
        """Read node data from the source file in JSON format.

        Returns:
            A list of dictionaries containing node data.
        """
        with open(self.source_path, 'r', encoding='utf-8') as file:
            kp_nodes = json.load(file)
        return kp_nodes

    def _handle_nodes(self) -> List[Action]:
        """Handle the nodes for generating descriptions.

        Returns:
            A message containing information about the generated descriptions.
        """
        self.kp_nodes = self._read_file()
        # self.kp_nodes = self.kp_nodes[:3]
        # print("cut kp nodes")
        
        # print(self.kp_nodes)
        # input("=====kp_nodes====")
        
        actions = list()
        count = 0

        def swap_max_node(nodes):
            node_lengths = [(node, len(node.get("content"))) for node in nodes]
            max_node, max_length = max(node_lengths, key=lambda x: x[1])

            nodes.remove(max_node)
            nodes.insert(0, max_node)

            print(f"最大的 content 长度为: {max_length}")
            print("已替换最长内容到开始") # 防止中间溢出，报错

        swap_max_node(self.kp_nodes)


        for node in self.kp_nodes:
            node_id = node.get("id")
            node_content = node.get("content","")
            desc = node.get("description","") 
            metadata = node.get("metadata",{})

            if desc == '':
                actions.append(GenerateDescription(language=self.language, kp_node={"id":node_id, "content":node_content , "metadata":metadata}))
                print("add node_id",node_id)
                count += 1
                print("count: ", count)
            # test = True 
            # if test and len(actions) > 1:
                # print("testing")
                # print("self topic ",self.topic)
                # break
        print("finish to handle nodes, count: ", count)
        # self.rc.max_react_loop = len(self.actions * 2)
        return actions


    async def _act(self) -> Message:
        """Perform an action as determined by the role.

        Returns:
            A message containing the result of the action.
        """
        print("start to act")
        todo = self.rc.todo
        # desc = ""
        try:
            output_node = await todo.run(topic=self.topic)
            logger.info(output_node)
            
            # 追加绝对路径
            # res = {
            #     "id":self.kp_node['id'],
            #     # "content":self.kp_node['content'],
            #     "metadata":self.kp_node['metadata'],
            #     "description":desc,
            #     "description_en":desc_en,
            # }
            output_node['description'] = self.detect_and_complete_links(output_node['description'].strip(),output_node['metadata'].get("sourceURL", ""))  
            output_node['description_en'] = self.detect_and_complete_links(output_node['description_en'].strip(),output_node['metadata'].get("sourceURL", ""))  

            self.output_nodes.append(output_node)
            # [从finish_count 开始计算]，且满足todo.node['id']相同的节点，都使用同一个description
            
            # for index, node in enumerate(self.kp_nodes):
            # # for index, node in enumerate(self.kp_nodes[self.finish_count:]):
            #     if todo.kp_node['id'] == node["id"]:
            #         self.kp_nodes[self.finish_count]["description"] = desc
            #         self.finish_count = max(index, self.finish_count)
            #         print("finish_count: ", self.finish_count)

        except Exception as e:
            logger.error(e)

        return Message(content=str(output_node), role=self.profile)

    async def react(self) -> Message:
        msg = await super().react()
        root_path = os.path.dirname(self.source_path)
        output_path = os.path.join(root_path, f"{self.topic}_descriptions.json")
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(self.output_nodes, file, ensure_ascii=False)
        msg.content = output_path
        return msg




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
        print("补全超链接: ", baseURL)
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

# # 示例文本
# text = """
# ...具有重要价值，例如通过 XMLHttpRequest 下拉列表等。相关链接为：https://www.w3school.com.cn/js/js_json_html.asp ' 接为：![你好](https://www.w3school.com.cn/js/js_json_html.asp) ' 从从服务器获取数据并进行相应处理，以及处理以数组形式返回的 JSON 数据等。同时，还提供了相关的链接，如 [JSON 数组](/js/js_json_arrays.asp "JSON 数组") 和 [JSON PHP](/js/js_json_php.asp "JSON PHP")，以方便用户深入了解相关知识。
# """

# # 调用函数补全相对路径
# baseURL = "https://www.w3school.com.cn"
# result = detect_and_complete_links(text, baseURL)
# print(result)




# Example usage
if __name__ == "__main__":
    source_file = "/path/to/source_file.txt"
    generator = DescriptionGenerator(source_path=source_file, topic="Example Topic")
    message = generator.react()
    print(f"Descriptions generated and saved to: {message.content}")
