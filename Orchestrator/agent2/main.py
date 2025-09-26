from agents.agent2 import agent2_handler

def run_agent():
    print("🤖 Agent2 is ready! Type your query (or 'exit' to quit):")
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break

        response = agent2_handler(user_input)
        print("Agent2:", response)

if __name__ == "__main__":
    run_agent()
