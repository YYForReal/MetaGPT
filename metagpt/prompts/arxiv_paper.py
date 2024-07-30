#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2024/3/3 14:22:40
@Author  : YYForReal
@File    : arxiv_paper.py
@Describe : arxiv_paper's prompt templates.
"""

SUMMARY_PROMPT = """
你是一个精通计算机领域自然语言处理（NLP）的权威研究员，你正在阅读一篇论文。
=====
标题：{title}
摘要：{abstract} 
=====
请从摘要中分点提取出论文的关键内容，要求提取文案简洁明了、清晰易懂，符合原意，输出一行即可。不要出现多余的换行与空格。语言为{language}。
"""

