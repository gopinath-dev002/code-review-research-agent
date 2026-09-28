from ..utils.config import config
from ..models.model import State, APIResponse
from ..setting import credentials
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from ..agents.code_generator_agent import CodeGenerator
from ..agents.code_research_agent import CodeReasearcher
from ..agents.code_reviewer_agent import CodeReviewer
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.runnables import RunnableConfig
from urllib.parse import quote_plus
from datetime import datetime, UTC
import logging
import json
from ..prompts.prompt import Prompt

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self):
        self.generate = CodeGenerator()
        self.review = CodeReviewer()
        self.research = CodeReasearcher()
        self._prompt = Prompt()

    async def code_generation(self, state: State):
        return await self.generate.generate_code(state)

    async def code_review(self, state: State):
        return await self.review.review_code(state)

    async def code_research(self, state: State):
        return await self.research.research_details(state)

    def route_after_classify(self, state: State):
        if state["intent"] == "generation":
            return "code_generation"
        elif state["intent"] == "review":
            return "code_review"
        elif state["intent"] == "research":
            return "code_research"
        elif state["intent"] == "others":
            return END
        return "code_generation"

    def route_after_review(self, state: State):
        # attempts already incremented by code_generation on entry;
        # terminate if we've exhausted retries or review is clean
        if state["intent"] == "review":
            return END
        if state["issue_type"] == "no issue":
            return END
        if state["attempts"] >= 3:
            return END
        if state["issue_type"] == "optimize":
            return "code_generation"
        if state["issue_type"] in ["package", "others"]:
            return "code_research"
        return END

    def route_after_research(self, state: State):
        logger.info(f"Route after research called, state={state}")
        if state["issue_type"] in ["package", "others"] or state.get("generated_code"):
            return "code_generation"
        return END

    def classify_intent(self, state: State):
        llm = config.get_llm(max_tokens=500, temperature=0.1)
        system_prompt = self._prompt.classify_intent_prompt

        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=state["user_query"])]
        )
        intent = response.content.lower()

        if "generation" in intent:
            state["intent"] = "generation"
        elif "review" in intent:
            state["intent"] = "review"
        elif "research" in intent:
            state["intent"] = "research"
        else:
            state["intent"] = "others"
            state["final_result"] = json.dumps({
        "message": "Sorry, ask me anything related to coding, reviewing code, or researching about code."})

        logger.info(f"Intent classified: {state['intent']}")
        return state

    async def build_graph(self, customer_id: str, user_query: str):
        try:
            logger.info("Build graph reached")

            state: State = {
                "user_query": user_query,
                "intent": None,
                "generated_code": None,
                "final_result": None,
                "review_result": None,
                "research_result": None,
                "issue_type": None,
                "attempts": 0,
                "messages": [],
            }
            logger.info(f"Initial state: {state}")

            encoded_password = quote_plus(credentials.db_password)
            DB_URI = (
                f"postgresql://{credentials.db_username}:{encoded_password}"
                f"@{credentials.db_host}:{credentials.db_port}/{credentials.db_name}"
            )

            graph = StateGraph(State)
            graph.add_node("code_generation", self.code_generation)
            graph.add_node("code_review", self.code_review)
            graph.add_node("code_research", self.code_research)
            graph.add_node("classify_intent", self.classify_intent)
            graph.set_entry_point("classify_intent")

            graph.add_conditional_edges(
                "classify_intent",
                self.route_after_classify,
                {
                    "code_generation": "code_generation",
                    "code_review": "code_review",
                    "code_research": "code_research",
                    END: END,
                },
            )

            graph.add_edge("code_generation", "code_review")

            graph.add_conditional_edges(
                "code_review",
                self.route_after_review,
                {
                    "code_generation": "code_generation",
                    "code_research": "code_research",
                    END: END,
                },
            )

            graph.add_conditional_edges(
                "code_research",
                self.route_after_research,
                {
                    "code_generation": "code_generation",
                    END: END,
                },
            )

            async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
                await checkpointer.setup()
                app = graph.compile(checkpointer=checkpointer)
                self.config = RunnableConfig(configurable={"thread_id": str(customer_id)})

                result = await app.ainvoke(state, config=self.config)
                final_result = result.get("final_result")

                return APIResponse(
                    code=200,
                    status="Success",
                    message="Successfully done",
                    data={"code": final_result},
                    error="null",
                    timestamp=datetime.now(UTC).isoformat(),
                )

        except Exception as e:
            logger.exception(f"Exception occurred: {e}")
            return APIResponse(
                code=500,
                status="failed",
                message="Bot processing failed",
                error={"details": str(e)},
                timestamp=datetime.now(UTC).isoformat(),
            )
