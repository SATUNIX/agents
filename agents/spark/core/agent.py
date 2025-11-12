import os
import time
import json
from openai import OpenAI
from core.mcp_loader import load_tools_from_mcp_json

class MCPAgent:
    """
    A lightweight agent that uses the OpenAI Assistants API and dynamically loaded tools.
    """
    def __init__(self, api_key: str, mcp_json_path: str = "config/mcp.json"):
        """
        Initializes the agent, loads tools, and sets up the OpenAI Assistant.

        Args:
            api_key (str): The OpenAI API key.
            mcp_json_path (str): Path to the mcp.json tool configuration file.
        """
        self.client = OpenAI(api_key=api_key)
        self.assistant = None
        self.thread = None

        # Load tools and create a mapping from tool names to functions
        print("Loading tools from MCP...")
        self.openai_tools, self.function_map = load_tools_from_mcp_json(mcp_json_path)
        print(f"Loaded {len(self.openai_tools)} tools.")

        self._create_assistant()
        self._create_thread()

    def _create_assistant(self):
        """Creates the OpenAI Assistant with the loaded tools."""
        print("Creating OpenAI Assistant...")
        self.assistant = self.client.beta.assistants.create(
            name="MCP General Agent",
            instructions="You are a helpful assistant. You have access to a variety of tools to answer user questions. When you use a tool, provide the result to the user in a clear and concise way. Do not just output the raw JSON from the tool.",
            tools=self.openai_tools,
            model="gpt-4-1106-preview" # or "gpt-3.5-turbo-1106"
        )
        print(f"Assistant created with ID: {self.assistant.id}")

    def _create_thread(self):
        """Creates a new conversation thread."""
        print("Creating new conversation thread...")
        self.thread = self.client.beta.threads.create()
        print(f"Thread created with ID: {self.thread.id}")

    def _execute_run_and_handle_tools(self, run):
        """
        Executes a run, waits for its completion, and handles required tool calls.
        """
        while run.status in ['queued', 'in_progress']:
            time.sleep(1)
            run = self.client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)

        if run.status == 'requires_action':
            print("Run requires action. Executing tools...")
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                print(f"  - Calling tool: {func_name} with args: {func_args}")
                
                if func_name in self.function_map:
                    try:
                        function_to_call = self.function_map[func_name]
                        result = function_to_call(**func_args)
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": result,
                        })
                    except Exception as e:
                        print(f"Error executing tool {func_name}: {e}")
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": f'{{"error": "Failed to execute tool: {e}"}}',
                        })
                else:
                    print(f"Unknown tool: {func_name}")
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": f'{{"error": "Unknown tool: {func_name}"}}',
                    })

            # Submit tool outputs back to the Assistant
            run = self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=self.thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            # Recursively handle the next state of the run
            return self._execute_run_and_handle_tools(run)

        elif run.status == 'completed':
            print("Run completed.")
            return self.client.beta.threads.messages.list(thread_id=self.thread.id)
        else:
            print(f"Run ended with status: {run.status}")
            print(run.last_error)
            return None

    def run_conversation(self):
        """Starts and manages the interactive conversation loop with the user."""
        print("\n--- Agent is ready. Type 'exit' to end the conversation. ---")
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() == 'exit':
                    print("Exiting agent. Goodbye!")
                    self._cleanup()
                    break

                # Add user message to the thread
                self.client.beta.threads.messages.create(
                    thread_id=self.thread.id,
                    role="user",
                    content=user_input
                )

                # Create and execute a run
                run = self.client.beta.threads.runs.create(
                    thread_id=self.thread.id,
                    assistant_id=self.assistant.id,
                )
                
                messages = self._execute_run_and_handle_tools(run)

                if messages:
                    # Get the latest message from the assistant
                    assistant_messages = [m for m in messages.data if m.role == 'assistant']
                    if assistant_messages:
                        print(f"Agent: {assistant_messages[0].content[0].text.value}")

            except KeyboardInterrupt:
                print("\nInterrupted. Exiting agent. Goodbye!")
                self._cleanup()
                break
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                self._cleanup()
                break
    
    def _cleanup(self):
        """Deletes the assistant and thread from OpenAI to avoid orphaned resources."""
        print("Cleaning up resources...")
        try:
            if self.assistant:
                self.client.beta.assistants.delete(self.assistant.id)
                print(f"Deleted assistant: {self.assistant.id}")
            if self.thread:
                self.client.beta.threads.delete(self.thread.id)
                print(f"Deleted thread: {self.thread.id}")
        except Exception as e:
            print(f"Error during cleanup: {e}")
