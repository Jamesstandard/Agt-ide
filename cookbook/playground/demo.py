"""Run `pip install openai sqlalchemy pypdf duckduckgo-search yfinance exa_py lancedb tantivy` to install dependencies."""

from textwrap import dedent
from datetime import datetime

from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.playground import Playground, serve_playground_app
from phi.storage.agent.sqlite import SqlAgentStorage
from phi.tools.dalle import Dalle
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.exa import ExaTools
from phi.tools.yfinance import YFinanceTools

db_session_storage_file: str = "agents.db"

web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    agent_id="web-agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGo()],
    instructions=["Break down the users request into 2-3 different searches.", "Always include sources"],
    storage=SqlAgentStorage(table_name="web_agent", db_file=db_session_storage_file),
    add_history_to_messages=True,
    num_history_responses=5,
    add_datetime_to_instructions=True,
    markdown=True,
)

finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    agent_id="finance-agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True)],
    instructions=["Always use tables to display data"],
    storage=SqlAgentStorage(table_name="finance_agent", db_file=db_session_storage_file),
    add_history_to_messages=True,
    num_history_responses=5,
    add_datetime_to_instructions=True,
    markdown=True,
)

image_agent = Agent(
    name="Image Agent",
    role="Generate images given a prompt",
    agent_id="image-agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[Dalle(model="dall-e-3", size="1792x1024", quality="hd", style="vivid")],
    storage=SqlAgentStorage(table_name="image_agent", db_file=db_session_storage_file),
    add_history_to_messages=True,
    add_datetime_to_instructions=True,
    markdown=True,
)

research_agent = Agent(
    name="Research Agent",
    role="Write research reports for the New York Times",
    agent_id="research-agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[ExaTools(start_published_date=datetime.now().strftime("%Y-%m-%d"), type="keyword")],
    description=(
        "You are a Research Agent that has the special skill of writing New York Times worthy articles. "
        "If you can directly respond to the user, do so. If the user asks for a report or provides a topic, follow the instructions below."
    ),
    instructions=[
        "For the provided topic, run 3 different searches.",
        "Read the results carefully and prepare a NYT worthy article.",
        "Focus on facts and make sure to provide references.",
    ],
    expected_output=dedent("""\
    Your articles should be engaging, informative, well-structured and in markdown format. They should follow the following structure:

    ## Engaging Article Title

    ### Overview
    {give a brief introduction of the article and why the user should read this report}
    {make this section engaging and create a hook for the reader}

    ### Section 1
    {break the article into sections}
    {provide details/facts/processes in this section}

    ... more sections as necessary...

    ### Takeaways
    {provide key takeaways from the article}

    ### References
    - [Reference 1](link)
    - [Reference 2](link)
    """),
    storage=SqlAgentStorage(table_name="research_agent", db_file=db_session_storage_file),
    add_history_to_messages=True,
    add_datetime_to_instructions=True,
    markdown=True,
)

app = Playground(agents=[web_agent, finance_agent, image_agent, research_agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("demo:app", reload=True)
