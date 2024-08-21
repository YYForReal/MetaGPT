from typing import Dict
from metagpt.actions import Action
import asyncio

# 定义一个模板，用于生成高质量的 prompt
PROMPT_TEMPLATE = """
作为一名 {role}，你将根据以下上下文和领域主题来回答用户的问题。

============
## 领域主题
{topic}
============
## 上下文
{context}
============
## 问题
{question}
============
请提供准确的答案，并确保在回答中涵盖相关的领域知识和背景信息。如有URL链接、日期等内容，注意保持完整。
输出语言与用户提出的`问题`语言保持一致 (English or Chinese)

**输出**
"""

EVAL_PROMPT_TEMPLATE = """
作为一名 {role}，你将根据上下文来回答用户的问题。

============
## 上下文
{context}
============
## 问题
{question}
============
请提供准确的答案，并确保在回答中涵盖相关的领域知识和背景信息。如有URL链接、日期等内容，注意保持完整。
输出语言与用户提出的`问题`语言{language}保持一致 

**输出**
"""






class GenerateAnswer(Action):
    """Action class for generating a high-quality prompt and using LLM to get the answer.

    Args:
        name: The name of the action.
    """

    name: str = "GenerateAnswer"
    role: str = "Web专家"
    topic: str = 'Web'
    is_eval: bool = False
    language: str = ""

    async def run(self, question, context: str = "") -> Dict:
        """Execute the action to generate an answer based on the context, question, and topic.

        Args:
            question: The user's question.
            context: The context related to the user's question.

        Returns:
            A dictionary containing the generated prompt and the LLM's answer.
        """
        
        # Generate the prompt based on the provided context, question, topic, and role
        prompt = PROMPT_TEMPLATE.format(role=self.role, topic=self.topic, context=context, question=question,language=self.language)
        if self.is_eval:
            prompt = EVAL_PROMPT_TEMPLATE.format(role=self.role, topic=self.topic, context=context, question=question,language=self.language)

        # Call self._aask to get the answer from the LLM
        answer: str
        try:
            answer = await self._aask(prompt=prompt)
        except Exception as e:
            print(f"Error generating answer: {e}")
            return None

        # Prepare the result
        res = {
            "prompt": prompt,
            "answer": answer
        }
        return res

# Example usage
async def main():
    topic = "市场营销"

    action = GenerateAnswer(topic=topic)
    context = "最近公司推出了新的产品，正在进行市场推广。"
    question = "我们应该如何优化市场推广策略以吸引更多客户？"
    result = await action.run(context=context, question=question, topic=topic)
    print(result)  # {'prompt': '...', 'answer': '...'}

if __name__ == "__main__":
    asyncio.run(main())
