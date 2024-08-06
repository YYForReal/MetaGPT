from metagpt.actions import Action
from typing import List, Optional,Dict
from pydantic import BaseModel, Field
from metagpt.utils.common import OutputParser


# class DuplicateEntities(BaseModel):
#     entities: List[str] = Field(
#         description="Entities that represent the same object or real-world entity and should be merged"
#     )


# class Disambiguate(BaseModel):
#     merge_entities: Optional[List[DuplicateEntities]] = Field(
#         description="Lists of entities that represent the same object or real-world entity and should be merged"
#     )





class EntityResolution(Action):
    """Action class for resolving entity duplicates.

    Args:
        name: The name of the action.
        entities: The list of entities to process.
    """

    name: str = "EntityResolution"
    entities: List[str] = []

    async def run(self, topic: str, *args, **kwargs) -> Dict:
        """Execute the action to resolve entity duplicates.

        Args:
            topic: The topic related to the entities.

        Returns:
            The merged list of entities.
        """
        system_prompt = """You are a data processing assistant. Your task is to identify duplicate entities in a list and decide which of them should be merged.
        The entities might be slightly different in format or content, but essentially refer to the same thing. Use your analytical skills to determine duplicates.

        Here are the rules for identifying duplicates:
        1. Entities with minor typographical differences should be considered duplicates.
        2. Entities with different formats but the same content should be considered duplicates.
        3. Entities that refer to the same real-world object or concept, even if described differently, should be considered duplicates.
        4. If it refers to different numbers, dates, or products, do not merge results
        """

        user_template = """
        Here is the list of entities to process:
        {entities}

        Please identify duplicates, merge them, and provide the merged list.with a key `merge_entities`
        """

        # prompt = {
        #     "system": system_prompt,
        #     "human": user_template.format(entities=self.entities)
        # }   
        prompts = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_template.format(entities=self.entities)},
        ],

        # Use self._aask to get the result
        result = await self._aask(user_template.format(entities=self.entities),system_msgs=system_prompt)

        print("origin result",result)

        # Parse the result string into a structured format
        try:
            parsed_result = OutputParser.extract_struct(result, dict)
            return parsed_result
        except Exception as e:
            print(f"Error parsing result: {e}")
            return None
        # if parsed_result and "merge_entities" in parsed_result:
        #     return [el["entities"] for el in parsed_result["merge_entities"]]
        # else:
        #     print("Result is None or merge_entities is missing")
        #     return None
