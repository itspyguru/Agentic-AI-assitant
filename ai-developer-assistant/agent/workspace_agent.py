import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

load_dotenv()

SERVER_PATH = str(Path(__file__).resolve().parent.parent / "server" / "filesystem_server.py")

async def get_workspace_agent():
    client = MultiServerMCPClient({
        "filesystem": {
            "command": "python",
            "args": [SERVER_PATH],
            "transport": "stdio",
        }
    })

    tools = await client.get_tools()
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-pro-preview",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt="You are a workspace assistant that can list, read, and write files.",
    )
