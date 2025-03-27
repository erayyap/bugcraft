from step_synth.prompts import *
from step_synth.environment import *
import os
from langchain_community.tools import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List
from langchain_core.output_parsers import PydanticOutputParser

search_tool = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=False,
    include_raw_content=True,
    include_images=False,
)

class JudgmentModel(BaseModel):
    """Model to judge a response."""

    reasoning: str = Field(
        description="Write a detailed analysis of the response based on your system prompt."
    )
    point: int = Field(
        ge=0,  # Minimum value
        le=10,  # Maximum value
        description="A point value representing the score. Must be between 0 and 10."
    )
judgment_parser = PydanticOutputParser(pydantic_object=JudgmentModel)
judgment_instructions = judgment_parser.get_format_instructions()

class BooleanModel(BaseModel):
    """Model to get a yes or no response."""

    decision: str = Field(
        description="Just type YES or NO here."
    )
boolean_parser = PydanticOutputParser(pydantic_object=BooleanModel)
boolean_instructions = boolean_parser.get_format_instructions()

class ContradictionModel(BaseModel):
    """Model to to store contradiction."""

    contradiction: str = Field(
        description="A short title form of the contradiction."
    )
    description: str = Field(
        description="A detailed explanation of the contradiction."
    )
class ContradictionsModel(BaseModel):
    """Model to to store contradictions."""

    contradiction_list: List[ContradictionModel] = Field(
        description="List of contradictions."
    )
contradiction_parser = PydanticOutputParser(pydantic_object=ContradictionsModel)
contradiction_instructions = contradiction_parser.get_format_instructions()
class ExtractedNodes(BaseModel):
    """Extracted node list"""

    nodes: List[str] = Field(
        description="Field to put all extracted nodes."
    )
node_parser = PydanticOutputParser(pydantic_object=ExtractedNodes)
node_instructions = node_parser.get_format_instructions()
class StepCluster(BaseModel):
    """Logically relevant steps in one list"""
    title: str = Field(
        description="Name of the step cluster."
    )
    steps: List[str] = Field(
        description="Field to put all relevant steps."
    )
class StepClusterList(BaseModel):
    """Place to put all steps"""

    step_clusters: List[StepCluster] = Field(
        description="Field to put all relevant step clusters."
    )
step_cluster_parser = PydanticOutputParser(pydantic_object=StepClusterList)
step_cluster_instructions = step_cluster_parser.get_format_instructions()
class StepSelection(BaseModel):
    """Model to match steps with images."""
    annotation: str = Field(
        description="Detailed annotation of the image."
    )
    reasoning: str = Field(
        description="Reasoning on why a particular step cluster was selected."
    )
    conclusion: str = Field(
        description="Only write a number, END or NOT RELEVANT here."
    )
step_selection_parser = PydanticOutputParser(pydantic_object=StepSelection)
step_selection_instructions = step_selection_parser.get_format_instructions()

s2r_rewrite_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
query_gen_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
judge_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
contradiction_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
suggestion_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
enhance_s2r_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
alternate_soln_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
node_extract_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
node_distill_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
step_cluster_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
reasnoning_trajectory_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
step_selection_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
cluster_check_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
cluster_rewrite_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
video_step_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
running_summary_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
final_cluster_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
mob_checker_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
crash_checker_llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0)
query_gen_chat = ChatPromptTemplate(
    [("system", query_gen_prompt), ("user", "{bug_report}")]
)

s2r_rewrite_chat = ChatPromptTemplate(
    [("system", initial_s2r_prompt), ("user", "{bug_report}")]
)
enhance_s2r_chat = ChatPromptTemplate(
    [("system", enhance_s2r_prompt)]
)
crash_checker_chat = ChatPromptTemplate(
    [("system", crash_checker_prompt+ "\n" + "{format_instructions}"),
    ],
    partial_variables= {"format_instructions": boolean_instructions}
)
suggestion_chat = ChatPromptTemplate(
    [("system", suggestion_prompt), ("user", "{bug_report}")]
)
alternate_soln_chat = ChatPromptTemplate(
    [("system", alternate_soln_prompt), ("user", "{bug_report}")]
)
mob_checker_chat = ChatPromptTemplate(
    [("system", mob_checker_prompt), ("user", "{bug_report}")]
)
reasoning_trajectory_chat = ChatPromptTemplate(
    [("system", reasoning_trajectory_prompt), ("user", "BUG REPORT: \n{bug_report}\nCONTENT:{content}")]
)

judge_chat = ChatPromptTemplate(
    [("system", judge_source_prompt + "\n" + "{format_instructions}"), ("user", "{bug_report}"),
    ],
    partial_variables= {"format_instructions": judgment_parser.get_format_instructions()}
)
contradiction_chat = ChatPromptTemplate(
    [("system", contradiction_prompt + "\n" + "{format_instructions}"), ("user", "{bug_report}"),
    ],
    partial_variables= {"format_instructions": contradiction_parser.get_format_instructions()}
)
contradiction_chat_2 = ChatPromptTemplate(
    [("system", contradiction_prompt), ("user", "{bug_report}"),
    ],
)
cluster_check_chat = ChatPromptTemplate(
    [("system", cluster_check_prompt), ("user", "{step_clusters}"),
    ],
)
node_extract_chat = ChatPromptTemplate(
    [("system", node_extract_prompt + "\n" + "{format_instructions}"), ("user", "{bug_report}"),
    ],
    partial_variables= {"format_instructions": node_instructions}
)
node_distill_chat = ChatPromptTemplate(
    [("system", node_distill_prompt + "\n" + "{format_instructions}"), ("user", "{bug_report}"),
    ],
    partial_variables= {"format_instructions": node_instructions}
)
step_cluster_chat = ChatPromptTemplate(
    [("system", step_cluster_prompt + "\n" + "{format_instructions}"), ("user", "{bug_report}"),
    ],
    partial_variables= {"format_instructions": step_cluster_instructions}
)
cluster_rewrite_chat = ChatPromptTemplate(
    [("system", cluster_rewrite_prompt + "\n" + "{format_instructions}"), ("user", "{step_clusters}"),
    ],
    partial_variables= {"format_instructions": step_cluster_instructions}
)
step_selection_chat = ChatPromptTemplate(
    [("system", step_selection_prompt + "\n" + "{format_instructions}"), ("user", [
        {"type": "text", "text": "STEPS: \n {bug_report}"},
        {
            "type": "image_url",
            "image_url": {"url": "data:image/jpeg;base64,{image_data}"},
        },
    ]),
    ],
    partial_variables= {"format_instructions": step_selection_instructions}
)
video_step_chat = ChatPromptTemplate(
    [("system", video_step_prompt + "\n" + "{format_instructions}"), ("user", [
        {"type": "text", "text": "STEPS: \n {bug_report} \n PREVIOUS FRAMES SUMMARY: \n {summary} \n LAST FRAME CONCLUSION: {conclusion}"},
        {
            "type": "image_url",
            "image_url": {"url": "data:image/jpeg;base64,{image_data}"},
        },
    ]),
    ],
    partial_variables= {"format_instructions": step_selection_instructions}
)
running_summary_chat = ChatPromptTemplate(
    [("system", running_summary_prompt), ("user", "PREVIOUS SUMMARY: \n {previous_summary} \n CURRENT FRAME: \n {current_frame}"),
    ],
)
final_cluster_chat = ChatPromptTemplate(
    [("system", final_cluster_prompt + "\n" + "{format_instructions}"), ("user", "{bug_report}\n IMAGE ANNOTATIONS: {image_annotations}\n VIDEO ANNOTATIONS: {video_annotations}"),
    ],
    partial_variables= {"format_instructions": step_cluster_instructions}
)
query_chain = query_gen_chat | query_gen_llm | StrOutputParser()
s2r_chain = s2r_rewrite_chat | s2r_rewrite_llm | StrOutputParser()
judge_chain = judge_chat | judge_llm | judgment_parser
contradiction_chain = contradiction_chat | contradiction_llm | contradiction_parser
suggestion_chain = suggestion_chat | suggestion_llm | StrOutputParser()
enhance_s2r_chain = enhance_s2r_chat | enhance_s2r_llm | StrOutputParser()
alternate_soln_chain = alternate_soln_chat | alternate_soln_llm | StrOutputParser()
node_extract_chain = node_extract_chat | node_extract_llm | node_parser
node_distill_chain = node_distill_chat | node_distill_llm | node_parser
step_cluster_chain = step_cluster_chat | step_cluster_llm | step_cluster_parser
reasoning_trajectory_chain = reasoning_trajectory_chat | reasnoning_trajectory_llm | StrOutputParser()
step_selection_chain = step_selection_chat | step_cluster_llm | step_selection_parser
cluster_check_chain = cluster_check_chat | cluster_check_llm | StrOutputParser()
cluster_rewrite_chain = cluster_rewrite_chat | cluster_rewrite_llm | step_cluster_parser
video_step_chain = video_step_chat | video_step_llm | step_selection_parser
running_summary_chain = running_summary_chat | running_summary_llm | StrOutputParser()
final_cluster_chain = final_cluster_chat | final_cluster_llm | step_cluster_parser
mob_checker_chain = mob_checker_chat | mob_checker_llm | StrOutputParser()
crash_checker_chain = crash_checker_chat | crash_checker_llm | boolean_parser