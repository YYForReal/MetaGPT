#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
@Time    : 2024/2/28 14:48:00
@Author  : YYForReal
@File    : tutorial_assistant.py
@Describe : Actions of the novel author, including writing directories and document content.
"""

from typing import Dict

from metagpt.actions import Action
from metagpt.prompts.novel_assistant import CONTENT_PROMPT, DIRECTORY_PROMPT, SUMMARIZE_PROMPT
from metagpt.utils.common import OutputParser

# 定义一个用于写大纲的Action类
class WriteOutline(Action):
    """Action类用于写小说大纲。

    参数:
        name: 动作的名称。
        language: 输出的语言，默认为 "Chinese"。
    """

    name: str = "WriteOutline"
    language: str = "Chinese"

    # 执行动作，根据主题生成小说大纲
    async def run(self, title: str, *args, **kwargs) -> Dict:
        """执行动作以根据主题生成小说大纲。
        参数:
            title: 小说标题。
        返回:
            包含大纲信息的教程目录，
            包括{"title": "..", "characters": ["角色名"..], "chapters": [{"第一章.."}]}。
        """
        prompt = DIRECTORY_PROMPT.format(title=title, language=self.language)  
        resp = await self._aask(prompt=prompt)  # 通过aask方法请求大模型
        return OutputParser.extract_struct(resp, dict)  # 格式化输出后返回

# 定义一个用于写具体内容的Action类
class WriteContent(Action):
    """Action类用于写小说细化章节。

    参数:
        name: 动作的名称。
        chapters: 要写的内容。
        language: 输出的语言，默认为 "Chinese"。
    """

    name: str = "WriteContent"
    chapters: dict = dict()
    language: str = "Chinese"
    characters: str = ""

    # 执行动作，根据章节和标题写文档内容
    async def run(self, title: str, memory: str, *args, **kwargs) -> str:
        """执行动作以根据章节和标题写文档内容。

        参数:
            title: 小说标题。

        返回:
            小说内容。
        """
        prompt = CONTENT_PROMPT.format(title=title, language=self.language, 
                                       chapters=self.chapters, characters=self.characters, memory=memory)
        return await self._aask(prompt=prompt)



class SummarizeContent(Action):
    """总结当前故事背景.

    Args:
        name: The name of the action.
        chapters: The content to write.
        language: The language to output, default is "Chinese".
    """

    name: str = "SummarizeContent"
    chapters: dict = dict()
    language: str = "Chinese"
    background: str = ""
    last_words: str = ""

    async def run(self, title: str, *args, **kwargs) -> str:
        """Execute the action to write document content according to the chapters and title.

        Args:
            title: The novel title.

        Returns:
            The written tutorial content.
        """
        prompt = SUMMARIZE_PROMPT.format(title=title, language=self.language,background=self.background)
        return await self._aask(prompt=prompt)
