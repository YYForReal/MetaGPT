'''
Author: yy 2572082773@qq.com
Date: 2024-07-31 09:18:52
LastEditTime: 2024-08-02 10:01:45
FilePath: \code\LLM\MetaGPT\metagpt\prompts\graph\desc.py
Description: 

Copyright (c) 2024 by YYForReal, All Rights Reserved. 
'''
#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   desc.py
@Time    :   2024/07/31 10:50:05
@Author  :   YYForReal 
@Email   :   2572082773@qq.com
@description   :   节点摘要生成
'''


GENERATE_DESC_TEMPLATE = """
以下是一个网页节点的信息：
节点名称（ID）: {id}
网页内容片段（以'============'作为开始与结束）: 
============
{content}


============
请基于以上信息，并结合您的知识，以节点`{id}`为主题生成一段准确、清晰且具有描述性的信息，以帮助用户更好地理解该节点的含义、用途和重要性。

要求：
1. 描述要易于理解，包含节点的关键特点和价值。
2. 不要使用过多的符号表示。
3. 尽量生成描述性的句子，例如'Javascript原型是指...','CSS3动画是...';
4. 禁止出现任何提及节点或页面的话语。如 '这个节点...'，'该页面...'。
"""

GENERATE_DESC_TEMPLATE_EN = """
Here is the information about a web node:
Node Name (ID): {id}
Web Content Fragment (starting and ending with '============'): 
============
{content}

============
Based on the above information and your knowledge, please generate an accurate, clear, and descriptive piece of information about the node `{id}` to help users better understand its meaning, purpose, and importance.

Requirements:
1. The description should be easy to understand and include key features and value of the node.
2. Avoid using excessive symbols.
3. Aim to generate descriptive sentences, such as 'JavaScript prototypes refer to...', 'CSS3 animations are...';
4. Do not include any structural references to the node or page, such as 'This node ...', 'This page ...'.
5. output using Engish.
"""
