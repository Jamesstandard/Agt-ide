from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.cli.console import console

regular_agent = Agent(model=OpenAIChat(id="gpt-4o"), markdown=True)
reasoning_agent = Agent(
    model=OpenAIChat(id="gpt-4o-2024-08-06"),
    reasoning=True,
    markdown=True,
    structured_outputs=True,
    reasoning_min_steps=3,
)

task = "How many 'r' are in the word 'supercalifragilisticexpialidocious'?"

console.rule("[bold green]Regular Agent[/bold green]")
regular_agent.print_response(task, stream=True)
console.rule("[bold yellow]Reasoning Agent[/bold yellow]")
reasoning_agent.print_response(task, stream=True, show_full_reasoning=True)
