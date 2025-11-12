import os
from dotenv import load_dotenv
from core.agent import MCPAgent

def main():
    """
    Main function to initialize and run the agent.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get the OpenAI API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or api_key == "YOUR_OPENAI_API_KEY":
        print("Error: OPENAI_API_KEY not found or not set.")
        print("Please create a .env file and add your OpenAI API key to it.")
        return

    try:
        # Initialize and run the agent
        agent = MCPAgent(api_key=api_key)
        agent.run_conversation()
    except Exception as e:
        print(f"Failed to start the agent: {e}")

if __name__ == "__main__":
    main()
