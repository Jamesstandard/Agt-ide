from phi.agent import Agent
from phi.tools.firecrawl import FirecrawlTools
from dotenv import load_dotenv

load_dotenv()


def agent_with_predefined_toolkit(url: str):
    agent = Agent(
        tools=[FirecrawlTools(map=True, scrape=True)],
        show_tool_calls=True,
        markdown=True,
        reasoning=True,
    )
    agent.print_response(f"Fetch all the blog links from the website: {url}")
    agent.print_response(
        "scrape and summarize the following website: https://www.firecrawl.dev/blog/using-structured-output-and-json-strict-mode-openai"
    )


# def agent_with_explicit_tools(url: str):
#     fc_tools = [
#         FirecrawlTools(map=True, scrape=True).map_website(url, include_subdomains=True, ignore_sitemap=False, limit=10),
#         FirecrawlTools(map=True, scrape=True).scrape_website(url),
#     ]
#     agent = Agent(tools=fc_tools, show_tool_calls=True, markdown=True, reasoning=True)
#     agent.print_response(f"Fetch all the blog links from the website: {url}")
#     agent.print_response(
#         "scrape and summarize the following website: https://www.firecrawl.dev/blog/using-structured-output-and-json-strict-mode-openai"
#     )


def crawl_example(url: str):
    agent = Agent(
        tools=[FirecrawlTools(scrape=True, crawl=True, async_crawl=True, crawl_limit=25)],
        show_tool_calls=True,
        reasoning=True,
        markdown=True,
    )


if __name__ == "__main__":
    url = "https://www.firecrawl.dev/blog"
    # agent_with_explicit_tools(url)
    agent_with_predefined_toolkit(url)
