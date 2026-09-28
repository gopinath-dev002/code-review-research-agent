from pydantic import BaseModel,Field,field_validator
from typing import Optional, Any,Literal
from langgraph.graph import MessagesState

class UserRequest(BaseModel):
    customer_id:int
    user_query:str

    @field_validator("user_query")
    @classmethod
    def validate_user_query(cls, v: str):
        if not isinstance(v, str):
            raise ValueError("query must be a string")

        if not v.strip():
            raise ValueError("query cannot be empty")

        return v.strip()


class CodeResponse(BaseModel):
    code: str = Field(
        ...,
        description="Complete, runnable Python code that fulfills the user's request. "
                    "Must contain only valid Python source code — no markdown fences, "
                    "no explanations, no comments outside the code itself."
    )

    @field_validator("code")
    @classmethod
    def strip_markdown_fences(cls, v: str) -> str:
        v = v.strip()
        if v.startswith("```"):
            # remove leading ```python / ``` and trailing ```
            v = v.split("\n", 1)[1] if "\n" in v else v
            if v.endswith("```"):
                v = v[: -3]
        return v.strip()

    @field_validator("code")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("code field cannot be empty")
        return v


class ReviewResponse(BaseModel):
    review_result: str = Field(
        ...,
        description="Detailed review of the ORIGINAL code covering strengths, all issues found, and word-only fix suggestions (no corrected code)."
    )
    issue: Literal[
        "no issue proceed",
        "to be optimized",
        "issue in package",
        "other issue"
    ] = Field(
        ...,
        description="Exactly one issue classification based on the review criteria."
    )
    code: str = Field(
        ...,
        description="The ORIGINAL submitted code, extracted verbatim (stripped of surrounding prose only). Never corrected, fixed, or rewritten."
    )


class ResearchResult(BaseModel):
    """Holds the output for my Research agent with a detailed context in a summary"""
    research_summary: str = Field(
        ...,
        description=(
            "A concise, conceptually complete summary of approximately 100-150 words, "
            "covering the core concept, key ideas, and context relevant to the input "
            "(review findings or user query). No filler, no text outside the summary itself."
        )
    )

    
class State(MessagesState):
    user_query: str
    intent: Optional[str] = None
    generated_code: Optional[str] = None
    final_result: Optional[str] = None          # always a JSON-encoded string
    review_result: Optional[ReviewResponse] = None
    research_result: Optional[ResearchResult] = None
    issue_type: Optional[str] = None
    attempts: int = 0    

class APIResponse(BaseModel):
    code: int
    status: str
    message: str
    data: Optional[Any] = None
    error: Optional[Any] = None
    timestamp: str

