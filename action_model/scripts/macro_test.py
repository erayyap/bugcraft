import requests

api_url = "http://localhost:8500/execute"

commands = [
    "press(\'right_click\')"
]

from pydantic import BaseModel, Field
from typing import List

class CommandList(BaseModel):
    """Model to write commands."""

    command_list: List[str] = Field(
        description="The actions you take using the commands available to you, as a list."
    )

# Example usage:

example_commands = CommandList(
    command_list=[
        "press('right_click')"
    ]
)

# Send the list directly as the JSON payload
response = requests.post(api_url, json=example_commands.command_list) 

try:
    response.raise_for_status()
    print("API response:", response.json())
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    if 'response' in locals():
        print("API response:", response.text) # Print raw response text for debugging