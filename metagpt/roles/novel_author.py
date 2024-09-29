#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2024/2/28 15:40:40
@Author  : YYForReal
@File    : novel_author.py
"""

from datetime import datetime
from typing import Dict

from metagpt.actions.write_novel import WriteContent, WriteOutline
from metagpt.const import NOVEL_PATH
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.utils.file import File


class NovelAuthor(Role):
    """小说作者，输入一句话生成一个标记格式的小说。

    Args:
        name: 角色名称。
        profile: 角色简介。
        goal: 角色目标。
        constraints: 角色的约束或要求。
        language: 生成小说的语言。
    """

    name: str = "YYForReal"
    profile: str = "小说作者"
    goal: str = "生成一个奇幻小说"
    constraints: str = "保持一致的叙述风格，包含引人入胜的对话和生动的描述"
    language: str = "Chinese"

    topic: str = ""
    main_title: str = ""
    characters: list = []
    total_content: str = ""

    file_path: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 保存时间戳为实例变量
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.root_path = NOVEL_PATH / self.timestamp
        # 其他初始化代码
        self.set_actions([WriteOutline(language=self.language)])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _handle_outline(self, outline_dict: Dict) -> Message:
        """处理小说的大纲。

        Args:
            outline_dict: 包含大纲和目录结构的字典，例如：
                          {"title": "xxx", "chapters": [{"章节1": ["子章节1", "子章节2"]}]}

        Returns:
            包含目录信息的消息。
        """
        self.main_title = outline_dict.get("title")
        self.characters = outline_dict.get("characters")
        directory = f"{self.main_title}\n"
        self.total_content += f"# {self.main_title}"
        actions = list(self.actions)
        for first_dir in outline_dict.get("chapters"):
            # print(f"outline_dict.get() === > {outline_dict.get('chapters')}")
            print(f"first_dir ===> {first_dir}")
            # input("==================请输入内容===================")
            actions.append(WriteContent(language=self.language, chapters=first_dir,
                                        characters=str(self.characters)))
            key = list(first_dir.keys())[0]
            directory += f"- {key}\n"
            for second_dir in first_dir[key]:
                directory += f"  - {second_dir}\n"
        self.set_actions(actions)
        self.rc.max_react_loop = len(self.actions)
        msg = Message(content=directory, role=self.profile)
        self.rc.memory.add(msg)
        return msg

    async def _act(self) -> Message:
        todo = self.rc.todo
        if isinstance(todo, WriteOutline):
            msg = self.rc.memory.get(k=1)[0]
            self.topic = msg.content
            resp = await todo.run(title=self.topic)
            # self.log_to_streamlit(f"生成大纲: {resp}\n")
            await self._handle_outline(resp)
            msg = Message(content="大纲已处理，动作列表已更新。", role=self.profile)
            self.rc.memory.add(msg)
            return msg
        elif isinstance(todo, WriteContent):
            memory = self.rc.memory.get(k=1)[0].content
            resp = await todo.run(title=self.topic, memory=memory)
            # self.log_to_streamlit(f"生成内容: {resp}\n")
            if self.total_content != "":
                self.total_content += "\n\n\n"
            self.total_content += resp
            msg = Message(content=resp, role=self.profile)
            self.rc.memory.add(msg)
            return msg

    def get_novel_file_path(self):
        # 返回生成的小说文件路径
        return str(self.root_path / f"{self.main_title}.md")



    async def react(self) -> Message:
        msg = await super().react()
        # 使用保存的 root_path
        await File.write(self.root_path, f"{self.main_title}.md", self.total_content.encode("utf-8"))
        msg.content = str(self.root_path / f"{self.main_title}.md")
        return msg

