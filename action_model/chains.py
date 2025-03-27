from action_model.environment import *
if USE_UNANNOTATED_IMAGES:
    from action_model.prompts import (thought_prompt, 
                     action_prompt, 
                     reflection_prompt,
                     cluster_verification_prompt,
                     thought_action_prompt,
                     self_correction_prompt,
                     action_correction_prompt)
else:
    from action_model.prompts_annotated import (thought_prompt, 
                     action_prompt, 
                     reflection_prompt,
                     cluster_verification_prompt,
                     thought_action_prompt,
                     self_correction_prompt,
                     action_correction_prompt)
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List
from langchain_core.output_parsers import PydanticOutputParser

class CommandList(BaseModel):
    """Model to write commands."""

    command_list: List[str] = Field(
        description="The actions you take using the commands available to you, as a list."
    )
command_parser = PydanticOutputParser(pydantic_object=CommandList)
command_instructions = command_parser.get_format_instructions()

class Thought_Action(BaseModel):
    """Model to write both thought and action."""

    thought: str = Field(
        description="A thought about what you see, and what action you will take considering the steps and trajectory."
    )

    command_list: List[str] = Field(
        description="The actions you take using the commands available to you, as a list."
    )
thought_action_parser = PydanticOutputParser(pydantic_object=Thought_Action)
thought_action_instructions = thought_action_parser.get_format_instructions()

class ReflectionModel(BaseModel):
    """Model to make reflections."""

    reflection: str = Field(
        description="Write your assessment here whether the step was successfully executed. If successful, write a short text saying how it was successful and what changed. If it failed, write a short text on what should be fixed and what was the error. Always include what the screen shows and what texts are written!"
    )
    classification: str = Field( 
        description ="Only write SUCCESS, FAILURE or MOVE_TO_NEXT_CLUSTER here."
    )
reflection_parser = PydanticOutputParser(pydantic_object=ReflectionModel)
reflection_instructions = reflection_parser.get_format_instructions()

class JudgmentModel(BaseModel):
    """Model to judge a response."""

    reasoning: str = Field(
        description="Write a detailed analysis of the response based on your system prompt."
    )
    classification: str = Field(
        description="Write only CORRECT or INCORRECT here."
    )
judgment_parser = PydanticOutputParser(pydantic_object=JudgmentModel)
judgment_instructions = judgment_parser.get_format_instructions()

llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0, base_url=BASE_URL, max_completion_tokens=1000)
thought_llm = llm
action_llm = llm
reflection_llm = llm
cluster_verification_llm = llm
thought_action_llm = llm
self_correction_llm = llm
action_correction_llm = llm

def get_user_messages():
    base_messages = [
        {"type": "text", "text": "ANNOTATION TABLE (THERE ARE SOME INCORRECT ONES IN THE TABLE!): \n {annotation_table}"},
        {
            "type": "image_url",
            "image_url": {"url": "data:image/jpeg;base64,{annotated_image_data}", "detail": "high"},
        }
    ]
    if USE_UNANNOTATED_IMAGES:
        unannotated_part = [
            {"type": "text", "text": "UNANNOTATED IMAGE:"},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64,{unannotated_image_data}", "detail": "high"},
            }
        ]
        return unannotated_part + base_messages
    return base_messages

# Reusable chat prompt structure
def create_chat_prompt(system_prompt, format_instructions=None):
    partial_vars = {}
    if format_instructions:
        partial_vars["format_instructions"] = format_instructions
    return ChatPromptTemplate(
        [
            ("system", system_prompt + ("\n{format_instructions}" if format_instructions else "")),
            ("user", get_user_messages())
        ],
        partial_variables=partial_vars
    )

# Initialize all chat prompts using the centralized structure
thought_chat = create_chat_prompt(thought_prompt)
action_chat = create_chat_prompt(action_prompt, command_instructions)
self_correction_chat = create_chat_prompt(self_correction_prompt, judgment_instructions)
thought_action_chat = create_chat_prompt(thought_action_prompt, thought_action_instructions)
action_correction_chat = create_chat_prompt(action_correction_prompt, thought_action_instructions)

reflection_chat = ChatPromptTemplate(
    [("system", reflection_prompt + "\n" + "{format_instructions}"), ("user", [
        {"type": "text", "text": "Image after the taken action:"},
        {
            "type": "image_url",
            "image_url": {"url": "data:image/jpeg;base64,{image_data}",
                          "detail": "high",},
        },
    ]),
    ],
    partial_variables= {"format_instructions": reflection_instructions}
)

cluster_verification_chat = ChatPromptTemplate(
    [("system", cluster_verification_prompt + "\n" + "{format_instructions}"), ("user", [
        {"type": "text", "text": "Image after the taken action:"},
        {
            "type": "image_url",
            "image_url": {"url": "data:image/jpeg;base64,{image_data}",
                          "detail": "high",},
        },
    ]),
    ],
    partial_variables= {"format_instructions": judgment_instructions}
)

thought_chain = thought_chat | thought_llm | StrOutputParser()
action_chain = action_chat | action_llm | command_parser
reflection_chain = reflection_chat | reflection_llm | reflection_parser
cluster_verification_chain = cluster_verification_chat | cluster_verification_llm | judgment_parser
thought_action_chain = thought_action_chat | thought_action_llm | thought_action_parser
self_correction_chain = self_correction_chat | self_correction_llm | judgment_parser
action_correction_chain = action_correction_chat | action_correction_llm | thought_action_parser
