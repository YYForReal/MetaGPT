#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2024/2/28 15:40:40
@Author  : YYForReal
@File    : novel_author.py
"""

from datetime import datetime
from typing import Dict,List

from metagpt.actions.search_arxiv_paper import ArxivCrawlerAction,SummaryContent
from metagpt.const import PAPER_PATH
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.utils.file import File
from metagpt.tools.arvix_paper import ArxivCrawler

class PaperManager(Role):
    """PaperManager

    Args:
        name: The name of the role.
        profile: The role profile description.
        goal: The goal of the role.
        constraints: Constraints or requirements for the role.
        language: The language in which the tutorial documents will be generated.
    """

    name: str = "YYForReal"
    profile: str = "Paper Manager"
    goal: str = "Summarize the paper"
    constraints: str = ""
    language: str = "Chinese"

    topic: str = ""
    paper_list: list = []
    total_content: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ArxivCrawlerAction(language=self.language)])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)
        

    async def _handle_outline(self, key_paper_Dict: Dict) -> Message:
        """Handle the outline for the novel.

        Args:
            paper_list: A dictionary containing the paper_list and directory structure,
                    such as {"keyword": [{"title": "xxx", "abstract": "xxx", "summary": "xxx"}]}

        Returns:
            A message containing information about the directory.
        """
        actions = list()
        self.paper_list = key_paper_Dict
        for keyword, paper_list in key_paper_Dict.items():
            for i in range(len(paper_list)):
                paper = paper_list[i]
                # print("paper---",paper)
                if paper.get("paper_title","") == "" or paper.get("paper_abstract","") == "":
                    continue
                actions.append(SummaryContent(language=self.language, title=paper.get("paper_title",""),abstract=paper.get("paper_abstract",""),index = i,keyword=keyword))
        self.set_actions(actions)

    # 执行角色的动作
    async def _act(self) -> Message:
        todo = self.rc.todo
        if type(todo) is ArxivCrawlerAction:
            msg = self.rc.memory.get(k=1)[0]
            self.topic = msg.content
            resp = await todo.run(keywords=self.topic)
            logger.info(resp)
            # 等待用户确认是否准备好继续
            input("===================ready to continue ??===================")
            await self._handle_outline(resp)
            
            return await super().react()
        
        elif type(todo) is SummaryContent:
            resp = await todo.run()
            logger.info(resp)
            resp = resp.replace("\n","")
            self.paper_list[self.topic][todo.index]["summary"] = resp 
            # 将执行结果添加到总内容中
            # self.total_content += resp
            # 创建一个消息对象，包含响应内容
            msg = Message(content=resp, role=self.profile)
            return msg

        # resp = await todo.run(title=self.topic)
        # logger.info(resp)
        # if self.total_content != "":
        #     self.total_content += "\n\n\n"
        # self.total_content += resp
        # return Message(content=resp, role=self.profile)

    async def react(self) -> Message:
        msg = await super().react()
        arxivCrawler = ArxivCrawler()
        filename = self.topic.replace(" ","_").replace(":","_")
        root_path = PAPER_PATH / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        total_content = arxivCrawler.json_to_md_data(self.paper_list)

        await File.write(root_path, f"{filename}.md", total_content.encode("utf-8"))
        # msg.content = str(root_path / f"{filename}.md")
        msg.content = total_content
        return msg
