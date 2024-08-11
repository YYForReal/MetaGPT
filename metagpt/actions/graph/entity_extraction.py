from typing import Dict, List
from metagpt.actions import Action
import asyncio
from metagpt.utils.common import OutputParser


EXTRACTION_PROMPT_TEMPLATE1 = """
作为信息提取专家，你正在从用户的问询文本中提取图谱的信息实体。
根据下面用户问询的文本。限定输出格式为 List[str] 提取Web领域图谱可能涉及的实体。

**示例**
input: JS的DOM元素操作怎么和HTML的h1标签使用？
output: ['JS DOM', 'HTML h1']

**输入**
input: {question}
output:
"""

EXTRACTION_PROMPT_TEMPLATE2 = """
作为信息提取专家，你正在从用户的问询文本中提取图谱的信息实体。
根据下面用户问询的文本。限定输出格式为 List[str] 提取Web领域图谱可能涉及的实体。
通过符号`^`后加数字,我们可以进一步表征不同实体的重要性。重要性默认为1，且无需显示^符号

**示例**
input: JS的DOM元素操作怎么和HTML的h1标签使用？
说明：'JS的DOM元素'表示一个实体，'HTML的h1标签'表示另一个实体。我们给修饰词赋予1的重要性，名词性的表述为2。
output: ['JS DOM^2', 'HTML h1^2']

**注意**
接下来给出实际输入，请直接以数组形式输出，不要输出其他内容。

**输入**
input: {question}
output:
"""

EXTRACTION_PROMPT_TEMPLATES = [EXTRACTION_PROMPT_TEMPLATE1, EXTRACTION_PROMPT_TEMPLATE2]



class ExtractEntities(Action):
    """Action class for extracting entities from user queries.

    Args:
        name: The name of the action.
    """

    name: str = "ExtractEntities"
    template_mode: int = 0

    async def run(self, question: str) -> Dict:
        """Execute the action to extract entities based on the user query.

        Args:
            question: The user's question for which entities need to be extracted.

        Returns:
            A dictionary containing the extracted entities.
        """
        
        # Generate the prompt with the user question
        EXTRACTION_PROMPT_TEMPLATE = EXTRACTION_PROMPT_TEMPLATES[self.template_mode]
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(question=question)

        # Call self._aask to get the extracted entities
        entities: List[str] 
        res = await self._aask(prompt=prompt)
        # Parse the result string into a structured format
        try:
            entities = OutputParser.extract_struct(res, list)

        except Exception as e:
            print(f"Error parsing result: {e}")
            return None

        # Prepare the result
        res = {
            "question": question,
            "entities": entities
        }
        return res

# Example usage
async def main():
    action = ExtractEntities()
    question = "如何实现前端圣杯布局？"
    result = await action.run(question)
    print(result)  # {'question': 'JS的DOM元素操作怎么和HTML的h1标签使用？', 'entities': ['JS DOM', 'HTML h1']}


if __name__ == "__main__":
    asyncio.run(main())