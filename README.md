# BugCraft: Automated Bug Reproduction and Action Synthesis
[![arXiv](https://img.shields.io/badge/arXiv-2503.20036-b31b1b.svg)](https://arxiv.org/abs/2503.20036)
BugCraft is a powerful tool designed to streamline bug reproduction by automatically generating detailed, actionable steps to replicate software issues. It leverages a combination of step synthesis and action modeling to produce comprehensive reproduction workflows.

## BugCraft-Bench

The bugcraft_bench folder contains the final 86 bug reports that can be reliably reproduced, serving as our benchmark.

## Prerequisites

-   **Windows OS**: This tool uses `pywin32` for window manipulation, making it Windows-specific.
-   **Capable Hardware**: Ensure your PC meets the requirements to run [OmniParser](https://huggingface.co/microsoft/OmniParser), particularly regarding GPU and memory.
-   **Python 3.8+**: Required for running the application.

## Setup Instructions

1. **Clone Repository**

    ```bash
    git clone https://github.com/erayyap/bugcraft
    cd bugcraft
    ```
2. **Install OmniParser Weights**
    -   From [https://huggingface.co/microsoft/OmniParser](https://huggingface.co/microsoft/OmniParser), download:
        -   `icon_caption_blip2`
        -   `icon_caption_florence`
    -   Place them in the respective directories:

        ```
        ./action_model/OmniParser/weights/
        ```
3. **Create Virtual Environment**

    ```bash
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    ```
4. **Configure Environment**
    Create a `.env` file in the root directory of the project with the following variables:

    ```ini
    OPENAI_API_KEY=TO_BE_FILLED  # Required
    TAVILY_API_KEY=ONLY_FILL_IF_YOU_USE_SEARCH  # Optional for web search

    # Path configurations (You must configure these!)
    WIKI_DIRECTORY=C:\\path\\to\\wiki\\output_pages
    FLORENCE_PATH=C:/path/to/icon_caption_florence
    ICON_MODEL_PATH=C:\\path\\to\\model_v1_5.pt

    # Model configurations
    STEP_SYNTH_MODEL_NAME="gpt-4o"
    ACTION_MODEL_NAME="gpt-4o"
    ```
5. **Prepare Bug Reports**
    Place all bug reports you want to process in the `bug_reports` folder, located in the root directory of the project.

## Usage

**Important:** **Run the following commands in a terminal with administrator privileges**. This is crucial for BugCraft to interact with application windows correctly and perform necessary actions.

**Full Pipeline (Step Synthesizer + Action Model):**

```bash
python main.py
```

**Step Synthesizer Only:**

```bash
python main.py --only-step
```

## Configuration Options

### Step Synthesizer

| Feature                   | Description                                                                                                                      |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `USE_WIKI`                | Enables the use of an internal knowledge base (Requires wiki setup).                                                              |
| `USE_SEARCH`              | Enables web search capabilities using Tavily.                                                                                   |
| `USE_MOB_CHECKER`         | Enables a separate call to an LLM to verify mob interactions.                                                                   |
| `USE_ALTERNATE_SOLUTIONS` | Enables a separate call to an LLM to check for alternative solutions in S2R steps.                                               |
| `USE_REASONING_TRAJECTORY` | Instead of directly including wiki/search pages in the context, utilizes reasoning trajectories (Refer to the paper for details). |
| `USE_FINAL_CLUSTERING`    | Performs a final LLM call to integrate information from images/pictures into the S2R.                                          |

### Action Model

| Feature            | Description                                                                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `MAKE_FULLSCREEN`  | Maximizes the Minecraft window to fullscreen. This can slightly enhance the traversal capabilities of GPT-4o but increases OmniParser's execution time and raises the cost of OpenAI calls due to larger image inputs. |
| `SEPARATE_THOUGHT` | Instead of generating thought and action in separate LLM calls, generates them concurrently.                                                    |
| `USE_CORRECTION`   | Before executing an action, sends another LLM call to verify its correctness. This also helps to prevent the agent from getting stuck in loops. |

## Important Notes

1. **Administrator Privileges**: Ensure you execute the commands with **administrator privileges** to allow BugCraft to function correctly.
2. **Path Configuration**: Double-check that all paths in the `.env` file use the correct Windows-style backslashes (`\`).
3. **API Keys**:
    -   An OpenAI API key (specifically for `gpt-4o`) is mandatory for the default configuration.
    -   A Tavily API key is only required if you enable `USE_SEARCH=True`.

For optimal performance, we recommend:

-   16GB+ RAM
-   NVIDIA GPU with 8GB+ VRAM

If you want the dataset, our run infos and all the configuration pre-done, you can reach all of that as a packaged zip in: https://figshare.com/s/70b5d141e69ff822cd40
