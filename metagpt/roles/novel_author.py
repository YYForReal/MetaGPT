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
    """Novel author, input one sentence to generate a novel in markup format.

    Args:
        name: The name of the role.
        profile: The role profile description.
        goal: The goal of the role.
        constraints: Constraints or requirements for the role.
        language: The language in which the tutorial documents will be generated.
    """

    name: str = "YYForReal"
    profile: str = "Novel Author"
    goal: str = "Generate a fantastic novel"
    constraints: str = "Maintain a consistent narrative voice, with engaging dialogue and vivid descriptions"
    language: str = "Chinese"

    topic: str = ""
    main_title: str = ""
    characters: list = []
    total_content: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteOutline(language=self.language)])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _handle_outline(self, outline_dict: Dict) -> Message:
        """Handle the outline for the novel.

        Args:
            outline_dict: A dictionary containing the outline_dict and directory structure,
                    such as {"title": "xxx", "chapters": [{"dir 1": ["sub dir 1", "sub dir 2"]}]}

        Returns:
            A message containing information about the directory.
        """
        self.main_title = outline_dict.get("title")
        self.characters = outline_dict.get("characters")
        directory = f"{self.main_title}\n"
        self.total_content += f"# {self.main_title}"
        actions = list()
        for first_dir in outline_dict.get("chapters"):
            actions.append(WriteContent(language=self.language, chapters=first_dir,
                                        characters=str(self.characters)))
            key = list(first_dir.keys())[0]
            directory += f"- {key}\n"
            for second_dir in first_dir[key]:
                directory += f"  - {second_dir}\n"
        self.set_actions(actions)

    # 执行角色的动作
    async def _act(self) -> Message:
        # 获取角色的待办事项
        todo = self.rc.todo
        # 判断待办事项的类型
        if type(todo) is WriteOutline:
            # 从记忆中获取最新的1条消息
            msg = self.rc.memory.get(k=1)[0]
            # 设置主题
            self.topic = msg.content
            # 执行待办事项的动作，传入主题作为参数
            resp = await todo.run(title=self.topic)
            logger.info(resp)
            # 等待用户确认是否准备好继续
            input("===================ready to continue ??===================")
            # 处理大纲的响应
            await self._handle_outline(resp)
            # 返回角色的反应
            return await super().react()
        
        elif type(todo) is WriteContent:
            # 从记忆中获取最新的消息内容
            memory = self.rc.memory.get(k=1)[0].content
            print("memory：", memory)
            # 执行待办事项的动作，传入主题和记忆作为参数
            resp = await todo.run(title=self.topic, memory=memory)
            logger.info(resp)
            # 如果总内容不为空，则添加新行
            if self.total_content != "":
                self.total_content += "\n\n\n"
            # 将执行结果添加到总内容中
            self.total_content += resp
            # 创建一个消息对象，包含响应内容
            msg = Message(content=resp, role=self.profile)
            # 将消息添加到记忆中
            self.rc.memory.add(msg)
            return msg

        # resp = await todo.run(title=self.topic)
        # logger.info(resp)
        # if self.total_content != "":
        #     self.total_content += "\n\n\n"
        # self.total_content += resp
        # return Message(content=resp, role=self.profile)

    async def react(self) -> Message:
        msg = await super().react()
        root_path = NOVEL_PATH / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        await File.write(root_path, f"{self.main_title}.md", self.total_content.encode("utf-8"))
        msg.content = str(root_path / f"{self.main_title}.md")
        return msg
