from ..models.model import State, ResearchResult
from ..utils.config import config
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import HumanMessage
import logging
import json
from ..prompts.prompt import Prompt

logger = logging.getLogger(__name__)


class CodeReasearcher:
    def __init__(self):
        self._prompt = Prompt()

    async def research_details(self, state: State):
        try:
            logger.info(
                f"CODE RESEARCHER AGENT REACHED query={state['user_query']}"
            )
            llm = config.get_llm(max_tokens=5000, temperature=0.7)
            system_prompt = self._prompt.research_prompt(
                state["review_result"].review_result if state["review_result"] else None
            )
            
            agent = create_agent(
                model=llm,
                system_prompt=system_prompt,
                response_format=ToolStrategy(schema=ResearchResult),
            )

            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=state["user_query"])]}
            )

            research_result: ResearchResult = result["structured_response"]

            final_result = (
                json.dumps({"research_summary": research_result.research_summary})
                if state["intent"] == "research"
                else None
            )

            return {
                "research_result": research_result,
                "final_result": final_result,
                "messages": result["messages"],
            }

        except Exception as e:
            logger.exception(f"Exception occurred in research_details: {e}")
            raise e