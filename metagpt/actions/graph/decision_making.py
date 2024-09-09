import re
from typing import Dict, List
from metagpt.actions import Action
import asyncio
from metagpt.utils.common import OutputParser


DECISION_PROMPT_TEMPLATE = """
**任务背景**
你是一个智能决策系统，负责根据当前处理的问询和已获取的上下文信息，决定下一步操作。用户的目标是通过多步推理和上下文搜索来生成一个准确的答案。当前，你已经提取了以下实体，并且进行了初步的上下文搜索。现在，你需要决定下一步的操作步骤。

**上下文信息**
1. 用户提问: {question}
2. 已检索的实体关键词: {entities}
2. 已检索到的上下文信息:
{contexts}

**决策任务**
根据当前的上下文信息和提取的实体，判断下一步操作，并给出简短的解释。你可以在以下三种操作中选择一个最适合当前情况的步骤：
1. **执行多跳搜索**：需要额外的多跳搜索。基于上下文信息中的邻居关系作为参数，搜索邻居节点以获取更多信息。
2. **重新进行结构化搜索**：需要重新修改提取的实体表达（例如修正实体重要性），然后再次进行结构化搜索，以获取更相关的上下文。
3. **生成答案并结束**：已具备足够的上下文信息，可以生成最终答案，并结束流程。

**输出格式**
- 操作选择: <选择操作1、2或3>
- 操作理由: <简要说明为什么选择这个操作>
- 操作参数: <与所选操作相关的参数>

**示例1**
- 操作选择: 1
- 操作理由: 当前的上下文信息不完整，需要进一步探索相关节点的信息。
- 操作参数: ['邻居节点A', '邻居节点B']

**示例2**
- 操作选择: 2
- 操作理由: 原本检索user-adjustable element size无结果，可以通过^重新调整实体表达的权重，且更换相似近义词扩大搜索范围。
- 操作参数: ['element size^2','resizable']

**示例3**
- 操作选择: 3
- 操作理由: 当前的上下文信息已经完整，可直接生成回复。
- 操作参数: []

**实际输入**
- 操作选择:
- 操作理由:
- 操作参数:

"""

JSON_REFORMAT_PROMPT_TEMPLATE = """
**提示**
将以下内容转为JSON格式，其中包括三个键:'operation'、'reason' 和 'parameters'。
operation的值为整数:'1'、'2'或者'3'。reason的值为字符串，parameters的值是一个列表，若无参数，则为空列表。直接输出对应JSON结果即可。

**内容**
{decision_result}

**格式**
{{
  "operation": <操作编号>,
  "reason": "<选择理由>",
  "parameters": <操作参数>
}}
"""


class DecisionMaking(Action):
    """Action class for making decisions on the next step in the RAG QA pipeline."""

    name: str = "DecisionMaking"


    async def reformat_decision(self, decision: str) -> Dict:
        """Reformat the decision result into a dictionary."""
        # If regex parsing fails, generate a new prompt to reformat the result as JSON
        decision_escaped = decision.replace("{", "{{").replace("}", "}}")

        reformat_prompt = JSON_REFORMAT_PROMPT_TEMPLATE.format(decision_result=decision)
        reformatted_result = await self._aask(prompt=reformat_prompt)
        print("formated result: ", reformatted_result)
        try:
            decision = OutputParser.extract_struct(reformatted_result, dict)
            return decision
        except Exception as e:
            print(f"Error parsing reformatted result: {e}")
            return None

    async def run(self, question: str, entities: List[str], contexts: List[str]) -> Dict:
        """Execute the decision-making process based on the provided context.

        Args:
            question: The user's question.
            entities: A list of entities extracted from the user's question.
            contexts: A list of contexts retrieved based on the entities.

        Returns:
            A dictionary containing the selected operation and the reason for the selection.
            {
                "operation": int,
                "reason": string
                "parameters": array<string>
            }
        """
        
        # Format the decision prompt
        prompt = DECISION_PROMPT_TEMPLATE.format(
            question=question,
            entities=entities,
            contexts=contexts
        )

        # Call self._aask to get the decision result
        decision_result = await self._aask(prompt=prompt)
        
        # Try to parse the decision using regex
        operation_match = re.search(r"操作选择:\s*(\d)", decision_result)
        reason_match = re.search(r"操作理由:\s*(.*)", decision_result)
        parameters_match = re.search(r"操作参数:\s*(.*)", decision_result)

        if not operation_match or not reason_match or not parameters_match:
            print("Error parsing decision result, trying to reformat...")
            decision = await self.reformat_decision(decision_result)
            if decision is None:
                decision = {

                }
        else:
            try:
                decision = {
                    "operation": int(operation_match.group(1)),
                    "reason": reason_match.group(1).strip(),
                    "parameters": eval(parameters_match.group(1).strip())
                }
            except Exception as e:
                print(f"Error parsing decision result: {e}")
                decision = self.reformat_decision(decision_result)
                return None

        return decision


# Example usage
async def main():
    decision_action = DecisionMaking()
    question = "如何实现前端圣杯布局？"
    entities = ['CSS Flexbox']
    contexts = ["""    
**entities**:
**direction** description_en: The `direction` property in CSS is used to specify the text direction and writing direction. It defines the basic writing direction of a block and the embedding and override directions for the Unicode bidirectional algorithm. The default value is `ltr` (text direction from left to right), but it can also be set to `rtl` (text direction from right to left). It is an inheritable property. Supported values are `ltr`, `rtl`, `initial`, and `inherit`. This property is available since CSS2. Browsers like Chrome (version 2.0), IE/Edge (version 5.5), Firefox (version 1.0), Safari (version 1.3), and Opera (version 9.2) fully support this property. Users can refer to the CSS tutorial on [CSS Text](/css/css_text.asp "CSS 文本") and the HTML DOM reference manual on [direction property](/jsref/prop_style_direction.asp "HTML DOM direction 属性") for more information. Examples are provided to show how to set the text direction, such as setting the text direction to "from right to left" as follows: `div { direction: rtl; }`.

**flex-direction** description_en: The `flex-direction` property in CSS is used to define the direction of flex items. It has several values: `row` (the default, displaying flex items as a horizontal row), `row-reverse` (the same as row but in the opposite direction), `column` (displaying flex items as a vertical column), `column-reverse` (the same as column but in the opposite direction), `initial` (setting the property to its default value), and `inherit` (inheriting the property from the parent element). It is important for controlling the layout of flex items. Examples are provided to show how to set the direction of flex items in a `<div>` element and how to use `flex-direction` in combination with media queries for different screen sizes and devices. The property is not inherited and is not supported for animation. It was introduced in CSS3 and is supported by various browsers.

**relationships**:
cursor - NEXT_KNOWLEDGE -> direction
direction - LINK -> https://www.w3school.com.cn/cssref/pr_text_direction.asp
direction - NEXT_KNOWLEDGE -> display
direction - PART_OF -> CSS 属性
direction - PRE_KNOWLEDGE -> cursor
display - PRE_KNOWLEDGE -> direction
flex-basis - NEXT_KNOWLEDGE -> flex-direction
flex-direction - LINK -> https://www.w3school.com.cn/cssref/pr_flex-direction.asp
flex-direction - NEXT_KNOWLEDGE -> flex-flow
flex-direction - PART_OF -> CSS 属性
flex-direction - PRE_KNOWLEDGE -> flex-basis
flex-flow - PRE_KNOWLEDGE -> flex-direction
"""
    ]

    decision = await decision_action.run(question, entities, contexts)
    print(decision)  # 输出选择的操作和理由
    print("operation", decision["operation"])
    print("reason", decision["reason"])
    

if __name__ == "__main__":
    asyncio.run(main())
