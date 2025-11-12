import json
import importlib
from typing import List, Dict, Callable, Any

def load_tools_from_mcp_json(file_path: str) -> (List[Dict[str, Any]], Dict[str, Callable]):
    """
    Loads tool definitions and maps function names to callable functions from a JSON file.

    Args:
        file_path (str): The path to the mcp.json file.

    Returns:
        A tuple containing:
        - A list of tool definitions compatible with the OpenAI Assistants API.
        - A dictionary mapping tool names to their actual callable Python functions.
    """
    openai_tools = []
    function_map = {}

    with open(file_path, 'r') as f:
        tool_definitions = json.load(f)

    for tool_def in tool_definitions:
        # Prepare the tool definition for the OpenAI API
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool_def["name"],
                "description": tool_def["description"],
                "parameters": tool_def["parameters"],
            }
        })

        # Dynamically import and map the actual function
        module_path, function_name = tool_def["path"].rsplit('.', 1)
        try:
            module = importlib.import_module(module_path)
            function = getattr(module, function_name)
            function_map[tool_def["name"]] = function
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Could not import function '{function_name}' from module '{module_path}': {e}")

    return openai_tools, function_map
