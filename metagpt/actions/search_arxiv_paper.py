from typing import Optional
from metagpt.actions.action import Action
from metagpt.const import TEST_CODES_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import Document, TestingContext
from metagpt.utils.common import CodeParser

import aiohttp
import arxiv
import re
import json
from datetime import datetime
from typing import List, Dict
from metagpt.prompts.arxiv_paper import SUMMARY_PROMPT
from metagpt.tools.arvix_paper import ArxivCrawler


class ArxivCrawlerAction(Action):
    name: str = "ArxivCrawlerAction"

    async def run(self, keywords: str):
        crawler = ArxivCrawler()
        query = crawler.keywords.get(keywords, keywords) # 扩展特定关键词，若没有，则延续
        print("query",query)
        paper_list = await crawler.get_daily_papers(query)
        logger.info(f"{paper_list}")
        return paper_list
    

class SummaryContent(Action):
    """Action class for summary content.

    Args:
        name: The name of the action.
        directory: The content to write.
        language: The language to output, default is "Chinese".
    """

    name: str = "SummaryContent"
    language: str = "Chinese"
    title: str = ""
    abstract: str = ""
    index: int = -1
    keyword: str = ""
    
    async def run(self, *args, **kwargs) -> str:
        """Execute the action to write document content according to the title and absturct.

        Args:
            title: The paper title.
            abstruct: The paper abstruct.

        Returns:
            The written summary content.
        """
        prompt = SUMMARY_PROMPT.format(title=self.title, language=self.language , abstract=self.abstract)
        return await self._aask(prompt=prompt)




async def main():
    arxivCrawler = ArxivCrawler()
    daily_papers = await arxivCrawler.get_daily_papers("NLP")
    print(daily_papers)