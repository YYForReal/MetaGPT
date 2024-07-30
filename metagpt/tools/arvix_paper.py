import aiohttp
import arxiv
import re
import json
from datetime import date
from typing import List, Dict


class ArxivCrawler:
    base_url = "https://arxiv.paperswithcode.com/api/v0/papers/"

    def __init__(self):
        self.keywords = {
            # "NLP": "NLP" + "OR" + "\\" + "Natural Language Processing" + "\"",
            # "Sequence Annotation": "\\" + "Sequence Annotation" + "\\" + "OR" + "\\" + "Sequence Marking" + "\\" + "OR" + "\\" + "Named Entity Recognition" + "\"",
            # "Information Extraction": "\\" + "Information Extraction" + "\\" + "OR" + "\\" + "Automatic Summary" + "\\" + "OR" + "\\" + "Title Generation" + "\\" + "OR" + "\\" + "Event Extraction" + "\"",
            # "Knowledge Graph":  "Knowledge Graph"  + " OR "  + "Knowledge Graphs" ,
            "Recommendation System": "\\" + "Recommendation System" + "\\" + "OR" + "\\" + "Semantic Matching" + "\\" + "OR" + "\\" + "Chatbots" + "\\" + "OR" + "\\" + "Knowledge Graph" + "\\" + "OR" + "\\" + "Knowledge Graphs" + "\""
        }
        self.max_results = 5

    def del_unicode(self, string):
        string = re.sub(r'\\u.{4}', '', string.__repr__())
        return string

    def del_not_english(self, string):
        string = re.sub('[^A-Za-z]', '', string.__str__())
        return string

    def get_authors(self, authors, first_author=False):
        output = str()
        if first_author == False:
            output = ", ".join(str(author) for author in authors)
        else:
            output = authors[0]
        return output

    def sort_papers(self, papers):
        output = dict()
        print("papers:",papers)
        keys = list(papers.keys())
        keys.sort(reverse=True)
        for key in keys:
            output[key] = papers[key]
        return output

    async def get_daily_papers(self, query="nlp", max_results=2) -> List[Dict]:
        """Get daily papers for a given topic."""
        search_engine = arxiv.Search(
            query=  query + " AND (cat:cs.AI OR cat:cs.LG OR cat:cs.IR OR cat:cs.CL OR cs.HC)",
            max_results=max_results * 2,
            sort_by=arxiv.SortCriterion.LastUpdatedDate
        )
        papers_info = []
        async with aiohttp.ClientSession() as session:
            for result in search_engine.results():
                paper_id = result.get_short_id()
                paper_title = result.title
                paper_url = result.entry_id
                code_url = self.base_url + paper_id
                paper_abstract = result.summary.replace("\\n", " ")
                paper_authors = self.get_authors(result.authors)
                paper_first_author = self.get_authors(
                    result.authors, first_author=True)
                primary_category = result.primary_category
                publish_time = result.published.date()
                update_time = result.updated.date()
                ver_pos = paper_id.find('v')
                if ver_pos == -1:
                    paper_key = paper_id
                else:
                    paper_key = paper_id[0:ver_pos]
                try:
                    async with session.get(code_url) as response:
                        r = await response.json()
                        if "official" in r and r["official"]:
                            repo_url = r["official"]["url"]
                            paper_info = {
                                "update_time": update_time,
                                "paper_title": paper_title,
                                "paper_abstract": paper_abstract,
                                "paper_id": paper_id,
                                "paper_url": paper_url,
                                "repo_url": repo_url,
                                "paper_authors":paper_authors
                            }
                            papers_info.append(paper_info)
                        else:
                            paper_info = {
                                "update_time": update_time,
                                "paper_title": paper_title,
                                "paper_abstract": paper_abstract,
                                "paper_id": paper_id,
                                "paper_url": paper_url,
                                "repo_url": None,
                                "paper_authors":paper_authors
                            }
                            papers_info.append(paper_info)
                except Exception as e:
                    print(f"exception: {e} with id: {paper_key}")
        res = {}
        res[query] = papers_info
        sorted(res[query], key=lambda x: x["update_time"], reverse=True) # sort by update_time, descending
        res[query] = res[query][:5] 
        return res

    def generate_content(self, papers_info: List[Dict]) -> Dict[str, str]:
        """Generate content from a list of paper information."""
        content = {}
        content_to_web = {}
        for paper in papers_info:
            paper_key = paper["paper_id"]
            if paper["repo_url"]:
                content[paper_key] = (
                    f"|**{paper['update_time']}**|**{paper['paper_title']}**|{paper['paper_abstract']} et.al.|"
                    f"[{paper['paper_id']}]({paper['paper_url']})|**[link]({paper['repo_url']})**|\\n"
                )
                content_to_web[paper_key] = (
                    f"- **{paper['update_time']}**, **{paper['paper_title']}**, {paper['paper_abstract']} et.al., "
                    f"[PDF:{paper['paper_id']}]({paper['paper_url']}), **[code]({paper['repo_url']})**\\n"
                )
            else:
                content[paper_key] = (
                    f"|**{paper['update_time']}**|**{paper['paper_title']}**|{paper['paper_abstract']} et.al.|"
                    f"[{paper['paper_id']}]({paper['paper_url']})|null|\\n"
                )
                content_to_web[paper_key] = (
                    f"- **{paper['update_time']}**, **{paper['paper_title']}**, {paper['paper_abstract']} et.al., "
                    f"[PDF:{paper['paper_id']}]({paper['paper_url']})\\n"
                )
        return content, content_to_web

    def update_json_file(self, filename, data_all):
        with open(filename, "r") as f:
            content = f.read()
            if not content:
                m = {}
            else:
                m = json.loads(content)

        json_data = m.copy()

        # update papers in each keywords
        for data in data_all:
            for keyword in data.keys():
                papers = data[keyword]

                if keyword in json_data.keys():
                    json_data[keyword].update(papers)
                else:
                    json_data[keyword] = papers

        with open(filename, "w") as f:
            json.dump(json_data, f)

    def json_to_md_data(self,json_data):
        DateNow = date.today()
        DateNow = str(DateNow)
        DateNow = DateNow.replace('-', '.')
        if json_data:
            data = json_data
        else:
            # exception
            return None
        total_content = ""
        # write data into README.md
        total_content += "## Updated on " + DateNow + "\n\n"
        for keyword in data.keys():
            day_content = data[keyword]
            if not day_content:
                continue
            # the head of each part
            total_content += f"## {keyword}\n\n"
            for paper in day_content:
                if paper is not None:
                    update_time = paper["update_time"]
                    paper_title = paper["paper_title"]
                    paper_abstract = paper["paper_abstract"]
                    paper_id = paper["paper_id"]
                    paper_url = paper["paper_url"]
                    repo_url = paper["repo_url"]
                    summary = paper.get("summary", "")
                    total_content += f"### {paper_title}\n"
                    total_content += f"- **Publish Date:** {update_time}\n"
                    total_content += f"- **Authors:** {paper['paper_authors']}\n"
                    total_content += f"- **Abstract:** {paper_abstract}\n"
                    total_content += f"- **Summary:** {summary}\n"
                    total_content += f"- **PDF:** [{paper_id}]({paper_url})\n"
                    if repo_url:
                        total_content += f"- **Code:** [link]({repo_url})\n"
                    total_content += "\n"
        return total_content


    # def json_to_md(self,filename=None, json_data=None, to_web=False, toFile=False,keyword=""):
    #     """
    #     @param filename: str
    #     @return None
    #     """

    #     DateNow = datetime.date.today()
    #     DateNow = str(DateNow)
    #     DateNow = DateNow.replace('-', '.')
    #     if filename:
    #         with open(filename, "r") as f:
    #             content = f.read()
    #             if not content:
    #                 data = {}
    #             else:
    #                 data = json.loads(content)
    #     elif json_data:
    #         data = json_data
    #     else:
    #         # exception
    #         return None
    #     print("data:",data)
    #     total_content = ""
    #     # write data into README.md

    #     if to_web == True:
    #         total_content += "---\n" + "layout: default\n" + "---\n\n"

    #     total_content += "## Updated on " + DateNow + "\n\n"

    #     for keyword in data.keys():
    #         day_content = data[keyword]
    #         if not day_content:
    #             continue
    #         # the head of each part
    #         total_content += f"## {keyword}\n\n"

    #         if to_web == False:
    #             total_content += "|Publish Date|Title|paper_abstract|Summary|PDF|Code|\n" + \
    #                 "|---|---|---|---|---|---|\n"
    #         else:
    #             total_content += "| Publish Date | Title | paper_abstract  |PDF | Code |\n"
    #         # sort papers by date
    #         # day_content = self.sort_papers(day_content)
    #         for paper in day_content:
    #             if paper is not None:
    #                 update_time = paper["update_time"]
    #                 paper_title = paper["paper_title"]
    #                 paper_abstract = paper["paper_abstract"].replace("\n", "")
    #                 paper_id = paper["paper_id"]
    #                 paper_url = paper["paper_url"]
    #                 repo_url = paper["repo_url"]
    #                 summary = paper.get("summary", "").replace("\n", "")
    #                 total_content += f"|**{update_time}**|**{paper_title}**|{paper_abstract}|{summary}|[{paper_id}]({paper_url})|**[link]({repo_url})**|\n"
    #         total_content += f"\n"
    #     print("finished")
    #     return total_content
