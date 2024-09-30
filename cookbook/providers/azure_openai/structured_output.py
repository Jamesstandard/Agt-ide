import os
from typing import List
from rich.pretty import pprint  # noqa
from pydantic import BaseModel, Field

from dotenv import load_dotenv

from phi.agent import Agent, RunResponse  # noqa
from phi.model.azure import AzureOpenAIChat

load_dotenv()

azure_model = AzureOpenAIChat(
    id=os.getenv("AZURE_OPENAI_MODEL_NAME"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
)


class MovieScript(BaseModel):
    setting: str = Field(..., description="Provide a nice setting for a blockbuster movie.")
    ending: str = Field(..., description="Ending of the movie. If not available, provide a happy ending.")
    genre: str = Field(
        ..., description="Genre of the movie. If not available, select action, thriller or romantic comedy."
    )
    name: str = Field(..., description="Give a name to this movie")
    characters: List[str] = Field(..., description="Name of characters for this movie.")
    storyline: str = Field(..., description="3 sentence storyline for the movie. Make it exciting!")


movie_writer = Agent(
    model=azure_model,
    description="You help people write movie scripts.",
    response_model=MovieScript,
    # debug_mode=True,
)

# Get the response in a variable
# run: RunResponse = movie_agent.run("New York")
# pprint(run.content)

movie_writer.print_response("New York")
