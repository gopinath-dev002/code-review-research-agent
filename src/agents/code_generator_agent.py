from ..models.model import State, CodeResponse
from ..utils.config import config
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import HumanMessage
import logging
from ..prompts.prompt import Prompt


logger = logging.getLogger(__name__)


class CodeGenerator:
    def __init__(self):
        self._prompts = Prompt()

    async def generate_code(self, state: State):
        try:
            logger.info(
                f"CODE GENERATOR AGENT REACHED attempt={state['attempts']} "
                f"issue_type={state.get('issue_type')} query={state['user_query']}"
            )
            llm = config.get_llm(max_tokens=4000, temperature=0.4)

            if state["attempts"] == 0 and state.get("issue_type") is None:
                system_prompt = self._prompts.code_generation_prompt(
                    user_query=state["user_query"]
                )
            elif state["issue_type"] == "optimize":
                system_prompt = self._prompts.regenerate_code_from_review(
                    review_result=state["review_result"].review_result,
                    generated_code=state["generated_code"],
                )
            elif state["issue_type"] in ["package", "others"]:
                system_prompt = self._prompts.regenerate_code_with_research(
                    review_result=state["review_result"].review_result,
                    generated_code=state["generated_code"],
                    research_result=state["research_result"],
                )
            else:
                # fallback safety net - should not normally hit this
                system_prompt = self._prompts.code_generation_prompt(user_query=state["user_query"])

            agent = create_agent(
                model=llm,
                system_prompt=system_prompt,
                response_format=ToolStrategy(schema=CodeResponse),
            )

            # Stateless per call: the system prompt already embeds all needed
            # context (original code / review / research). We don't replay
            # full prior history to avoid compounding duplicated context.
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content="Proceed as instructed.")]}
            )

            response: CodeResponse = result["structured_response"]

            return {
                "generated_code": response.code,
                "attempts": state["attempts"] + 1,
                "messages": result["messages"],
            }

        except Exception as e:
            logger.exception(f"Exception occurred in generate_code: {e}")
            raise e