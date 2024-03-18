from phi.assistant import Assistant
from phi.tools.duckduckgo import DuckDuckGo
from phi.llm.anthropic import Claude

assistant = Assistant(
    llm=Claude(model="claude-3-sonnet-20240229"), tools=[DuckDuckGo()], show_tool_calls=True, debug_mode=True
)
assistant.print_response("Tell me about OpenAI Sora? Also tell me some news about it", markdown=True)
