from ..models.model import State, ReviewResponse
from ..utils.config import config
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import HumanMessage, SystemMessage
import logging
import json
from ..prompts.prompt import Prompt

logger = logging.getLogger(__name__)


class CodeReviewer:
    def __init__(self):
        self._prompt = Prompt()

    def _map_issue(self, issue: str) -> str:
        issue = issue.lower().strip()
        if issue == "to be optimized":
            return "optimize"
        if issue == "issue in package":
            return "package"
        if issue == "no issue proceed":
            return "no issue"
        return "others"

    async def review_code(self, state: State):
        try:
            logger.info(
                f"CODE REVIEWER AGENT REACHED attempt={state['attempts']} "
                f"query={state['user_query']}"
            )
            llm = config.get_llm(max_tokens=4000, temperature=0.1)
            system_prompt = self._prompt.review_prompt()

            agent = create_agent(
                model=llm,
                system_prompt=system_prompt,
                response_format=ToolStrategy(schema=ReviewResponse),
            )

            code_to_review = state["generated_code"] or state["user_query"]

            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=code_to_review)]}
            )

            review_result: ReviewResponse = result["structured_response"]
            issue_type = self._map_issue(review_result.issue)

            final_result = None
            generated_code = state["generated_code"]

            if state["intent"] == "review":
                final_result = json.dumps({
                "code": review_result.code,
                "review_result": review_result.review_result,
                "issue": review_result.issue,
                })
                generated_code = review_result.code

            elif state["intent"] == "generation":
                if issue_type == "no issue" or state["attempts"] >= 3:
                    final_result = json.dumps({"code": review_result.code})
                    generated_code = review_result.code

            return {
                "final_result": final_result,
                "issue_type": issue_type,
                "generated_code": generated_code,
                "review_result": review_result,
                "messages": result["messages"],
            }

        except Exception as e:
            logger.exception(f"Exception occurred in review_code: {e}")
            raise e