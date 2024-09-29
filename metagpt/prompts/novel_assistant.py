#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2024/2/28 16:40:40
@Author  : YYForReal
@File    : novel_assistant.py
@Describe : novel Assistant's prompt templates.
"""

COMMON_PROMPT = """
You are now a skilled novelist specializing in thrilling and engaging internet-themed novels. 
We need you to craft a captivating novel with the title "{title}".
"""

DIRECTORY_PROMPT_EN = (
    COMMON_PROMPT
    + """
Please provide a specific and imaginative outline for this novel, strictly following the following requirements:
1. The output must be strictly in the specified language, {language}.
2. Answer strictly in the dictionary format like {{"title": "xxx", "characters": ["David, a hero in ...","Bob, an young boy..."], "chapters": [{{"第一章": "xx"}}, {{"第二章": "xx"}},...]}}.
3. At least 20 chapters.
4. The outline should be as creative and detailed as possible, with primary chapters and secondary sections. The secondary sections are in the array.
5. Do not have extra spaces or line breaks.
6. Each chapter and section title must be intriguing and relevant to the story.
7. The story should reflect the protagonist's growth and have some plots with twists and turns.
"""
)


DIRECTORY_PROMPT = (
    COMMON_PROMPT
    + """
请为这部小说提供一个具体而富有想象力的提纲，严格遵循以下要求:
0. 请严格按照指定的语言{language}回答。
1. 严格按照字典格式回答，如{{"title": "西游记", "characters": ["孙悟空, 花果山诞生的美猴王。桀骜不驯，本领高强..", "猪八戒, 憨厚可爱，贪吃懒惰。在第十二章后出现于高老庄...",...],"chapters":[{{"第一章 石猴诞生":"花果山上，一块仙石孕育出一个石猴，石猴勇敢聪明，成为猴王。"}},{{"第二章 石猴称霸":"石猴习得武艺，闯荡龙宫..."}},...]}}.
2. 至少20章。
3. 大纲应该尽可能有创意和详细，主要章节使用数组表示。
4. 不要有额外的空格或换行符。
5. 每一章和章节的标题都必须引人入胜，与故事相关。
6. 设计的章节应该反映主人公的成长，并存在跌宕起伏的情节。适当存在一些高危时刻、情节转折与逆转。 
"""
)




CONTENT_PROMPT_EN = (
    COMMON_PROMPT
    + """
Now I will give you the chapter and section titles for the novel. 
Please output the detailed narrative content of each section. 

The characters for the novel are as follows:
{characters}

The chapter and section titles for the novel are as follows:
{chapters}

Here is your last plot:
======
{memory}
======

Strictly limit output according to the following requirements:
1. If there are dialogue examples, they must be lively.
2. The output must be strictly in the specified language, {language}.
3. Do not have redundant output, including concluding remarks.
4. Strict requirement not to output the title "{title}" explicitly within the narrative.
5. Maintain a consistent narrative voice, alternating between first-person and third-person perspectives.
6. Include occasional vivid descriptions of scenery and detailed character portrayals.
7. Enrich character images through dialogue and actions.
8. Ensure the story reflects the protagonist's growth and has a plot with twists and turns.
"""
)


CONTENT_PROMPT = (
    COMMON_PROMPT
    + """
现在我将给你小说的章节标题，请直接输出小说内容。

下面是小说的背景信息：
# 标题：{title}

# 人物: {characters}

# 小说之前的最后一个情节:
= = = = = =
{memory}
= = = = = =

# 当前需要输出的章节小说标题及大纲:
{chapters}

请顺承最后一个情节，继续攥写本章小说内容。以'## 章节标题'开始，后续直接输出内容即可。

严格按照以下要求限制输出:
1. 如果有对话样例，一定要生动活泼。通过对话、动作、神态丰富人物形象。
2. 输出必须严格使用指定的语言{language}。
3. 不要有多余的输出以及结束语。
4. 不要在叙述中输出标题“{title}”及其他markdown内容。
5. 保持一致的叙述声音，交替使用第一人称和第三人称视角。
6. 包括偶尔对风景的生动描述和详细的人物细节描写。
7. 确保故事反映主角的成长，情节跌宕起伏。
"""
)



SUMMARIZE_PROMPT = (
    COMMON_PROMPT
    + """
Now I will provide you with a summary of the previous content and the detailed narrative content of the new section. 
Please output a new story background summary based on the previous one. 
Finally, provide a summary of the event the protagonist is currently in, for easy continuation of the plot.

The chapter and section titles for the novel are as follows:
{chapters}

Previous Content Summary:
{background}

New Section Content:
{new_section_content}

Strictly limit output according to the following requirements:
1. The output must be strictly in the specified language, {language}.
2. Do not have redundant output, including concluding remarks.
3. Strict requirement not to output the title "{title}" explicitly within the narrative.
4. Maintain a consistent narrative voice, alternating between first-person and third-person perspectives.
"""
)


