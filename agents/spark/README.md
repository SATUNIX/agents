# Lightweight "Mixture of Agents" MCP Agent

This project implements a lightweight, general-use agent based on the "Mixture of Agents" methodology. It uses the OpenAI Assistants API and allows for tools (skills) to be added easily through a `mcp.json` configuration file.

The core idea is that the main agent acts as an orchestrator, delegating tasks to specialized tools based on the user's request.

## Features

- **Dynamic Tool Loading:** Easily add or remove tools by editing `config/mcp.json` and adding the corresponding Python function in the `tools` directory.
- **OpenAI Assistants API:** Leverages the power of persistent threads and context management provided by the latest OpenAI API.
- **Lightweight & Extendable:** The "Mixture of Agents" approach keeps the core agent simple and promotes modular, reusable tools.
- **Clean Exit:** The agent cleans up the created Assistant and Thread on OpenAI's servers when you exit, preventing orphaned resources.

## Project Structure

```
spark/
├── core/
│   ├── agent.py           # The main agent class and conversation logic.
│   └── mcp_loader.py      # Logic for loading tools from mcp.json.
├── tools/
│   └── mcp_example_tool.py # Example tool functions.
├── config/
│   └── mcp.json           # JSON configuration for defining tools.
├── .env                   # Environment variables (for API key).
├── main.py                # The entrypoint to run the agent.
├── requirements.txt       # Python dependencies.
└── README.md              # This file.
```

## Setup and Usage

### 1. Prerequisites

- Python 3.7+
- An OpenAI API key.

### 2. Installation

1.  **Clone the repository (or download the files):**
    ```bash
    git clone <repository_url>
    cd spark
    ```

2.  **Create a `.env` file:**
    Copy the contents of the `.env.example` file or create a new file named `.env` in the root of the project.

3.  **Add your API Key:**
    Open the `.env` file and replace `"YOUR_OPENAI_API_KEY"` with your actual OpenAI API key.
    ```
    OPENAI_API_KEY="sk-..."
    ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Running the Agent

To start the agent and begin a conversation, run:

```bash
python main.py
```

The agent will initialize, create the assistant on OpenAI's servers, and prompt you for input.

**Example Conversation:**

```
Loading tools from MCP...
Loaded 2 tools.
Creating OpenAI Assistant...
Assistant created with ID: asst_...
Creating new conversation thread...
Thread created with ID: thread_...

--- Agent is ready. Type 'exit' to end the conversation. ---
You: What's the weather in San Francisco?
Run requires action. Executing tools...
  - Calling tool: get_current_weather with args: {'location': 'San Francisco, CA'}
Run completed.
Agent: The weather in San Francisco, CA is 65 degrees fahrenheit with a forecast of sunny.
You: What is the price of Google stock?
Run requires action. Executing tools...
  - Calling tool: get_stock_price with args: {'symbol': 'GOOG'}
Run completed.
Agent: The current price for the symbol GOOG is $278.19.
You: exit
Exiting agent. Goodbye!
Cleaning up resources...
Deleted assistant: asst_...
Deleted thread: thread_...
```

## How to Add a New Tool

1.  **Create the Python Function:**
    Add a new Python function to an existing file in the `tools/` directory or create a new file (e.g., `tools/my_new_tool.py`). The function should be self-contained and have clear parameters with type hints.

    *Example in `tools/my_new_tool.py`:*
    ```python
    def get_server_status(server_name: str) -> str:
        """Checks the status of a given server."""
        # In a real scenario, you would query the server.
        return f'{{"server": "{server_name}", "status": "online"}}'
    ```

2.  **Define the Tool in `mcp.json`:**
    Open `config/mcp.json` and add a new JSON object to the list.

    - `name`: The function name the LLM will call. **Must match your Python function name.**
    - `description`: A clear, concise description of what the tool does. This is crucial for the LLM to decide when to use it.
    - `path`: The Python module path to your function (`folder.file.function_name`).
    - `parameters`: A JSON schema describing the function's arguments.

    *Addition to `config/mcp.json`:*
    ```json
    {
      "name": "get_server_status",
      "description": "Checks the status of a given server.",
      "path": "tools.my_new_tool.get_server_status",
      "parameters": {
        "type": "object",
        "properties": {
          "server_name": {
            "type": "string",
            "description": "The name of the server to check, e.g. 'primary-db'."
          }
        },
        "required": ["server_name"]
      }
    }
    ```

3.  **Relaunch the Agent:**
    That's it! The new tool will be loaded automatically the next time you run `python main.py`.
