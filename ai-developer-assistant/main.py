import asyncio
import streamlit as st
from langchain_core.messages import AIMessage, ToolMessage

from agent.orchestrator import get_orchestrator


def format_reasoning(messages, skip: int) -> str:
    """Render the agent's intermediate steps from this turn as a readable trace."""
    lines = []
    for msg in messages[skip:-1]:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for call in msg.tool_calls:
                lines.append(f"**Calling tool** `{call['name']}` with `{call['args']}`")
        elif isinstance(msg, AIMessage) and msg.text():
            lines.append(f"**Thinking:** {msg.text()}")
        elif isinstance(msg, ToolMessage):
            lines.append(f"**Tool `{msg.name}` returned:**\n```\n{msg.content}\n```")
    return "\n\n".join(lines) if lines else "_No tool calls — direct answer._"

st.set_page_config(page_title="AI Developer Assistant", page_icon="🤖")
st.title("AI Developer Assistant")


@st.cache_resource
def get_loop():
    return asyncio.new_event_loop()


@st.cache_resource
def load_agent():
    return get_loop().run_until_complete(get_orchestrator())


loop = get_loop()
agent = load_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("reasoning"):
            with st.expander("Reasoning"):
                st.markdown(msg["reasoning"])
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    history = [(m["role"], m["content"]) for m in st.session_state.messages]
    with st.chat_message("assistant"):
        reasoning_box = st.expander("Reasoning", expanded=True)
        reply_box = st.empty()
        reasoning_lines = []
        reply_holder = [""]

        async def run_stream():
            async for chunk in agent.astream(
                {"messages": history}, stream_mode="updates"
            ):
                for node, payload in chunk.items():
                    for msg in payload.get("messages", []):
                        line = ""
                        if isinstance(msg, AIMessage) and msg.tool_calls:
                            for call in msg.tool_calls:
                                line = f"**Calling** `{call['name']}` with `{call['args']}`"
                        elif isinstance(msg, ToolMessage):
                            line = f"**Tool `{msg.name}` returned:**\n```\n{msg.content}\n```"
                        elif isinstance(msg, AIMessage) and msg.text():
                            reply_holder[0] = msg.text()
                            reply_box.markdown(reply_holder[0])
                        if line:
                            reasoning_lines.append(line)
                            reasoning_box.markdown("\n\n".join(reasoning_lines))

        loop.run_until_complete(run_stream())

    st.session_state.messages.append(
        {"role": "assistant", "content": reply_holder[0], "reasoning": "\n\n".join(reasoning_lines)}
    )
