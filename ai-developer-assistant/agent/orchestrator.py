import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from agent.workspace_agent import get_workspace_agent

load_dotenv()


async def get_orchestrator():
    workspace_agent = await get_workspace_agent()

    @tool
    async def workspace(query: str) -> str:
        """Delegate filesystem tasks (listing folders, reading files, writing files) to the workspace agent. Pass a natural-language instruction."""
        result = await workspace_agent.ainvoke({
            "messages": [("user", query)]
        })
        return result["messages"][-1].text()

    # add more sub-agent tools here as you build them, e.g. `code_review`, `search`, etc.

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-pro-preview",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )
    return create_agent(
        model=llm,
        tools=[workspace],
        system_prompt=(
            "You are an orchestrator. You have specialist sub-agents available as tools. "
            "Pick the right one for each user request and delegate to it. "
            "Synthesize their answers into a single helpful reply."
        ),
    )
