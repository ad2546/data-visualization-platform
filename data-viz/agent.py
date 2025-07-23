
import pandas as pd
from google.adk import Runner
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
import os

async def process_csv(file_path: str) -> str:
    """Processes the uploaded CSV file and generates a visualization."""
    df = pd.read_csv(file_path)

    agent_instructions = """
    You are a data visualization expert. Your task is to generate a compelling and
    informative data visualization from the provided dataset. You have access to a
    tool named `get_data` which will return the data as a pandas DataFrame. You
    must call this tool to get the data. After analyzing the data, generate a
    single, self-contained HTML file that represents the visualization. The HTML
    should be modern, clean, and interactive if possible (e.g., using Plotly).
    Return only the raw HTML content.
    """

    def get_data() -> pd.DataFrame:
        """Call this tool to get the dataset for visualization."""
        return df

    agent = Agent(
        name="visualization_agent",
        tools=[get_data]
    )

    runner = Runner(
        agent=agent,
        session_service=InMemorySessionService(),
        app_name="data-viz-app"
    )

    session_id = "my-session"
    message = "Please generate a visualization for the dataset."

    response_events = await runner.run_async(
        session_id=session_id,
        message=message
    )

    visualization_html = ""
    if response_events and hasattr(response_events[-1], 'content'):
        visualization_html = response_events[-1].content
    else:
        visualization_html = "<html><body><h1>Error</h1><p>Could not generate visualization.</p></body></html>"

    output_dir = "uploads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    visualization_filename = os.path.basename(file_path).replace(".csv", ".html")
    visualization_path = os.path.join(output_dir, visualization_filename)

    with open(visualization_path, "w") as f:
        f.write(visualization_html)

    return visualization_path
