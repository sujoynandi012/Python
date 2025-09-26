from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool
from langgraph.prebuilt import create_react_agent
from agent2.tools.fetchdata import fetchdata
from agent2.tools.updatedata import updatedata
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY")
)

# ---------------------------
# Wrapped tools with logging
# ---------------------------
def fetchdata_with_log(query: str) -> str:
    print("\n[Agent2] Using Tool: FetchData")
    print(f"[Agent2] Query Input: {query}")
    result = fetchdata(query)
    print(f"[Agent2] Tool Output: {result}\n")
    return result

def updatedata_with_log(query: str) -> str:
    print("\n[Agent2] Using Tool: UpdateData")
    print(f"[Agent2] Query Input: {query}")
    result = updatedata(query)
    print(f"[Agent2] Tool Output: {result}\n")
    return result

# ---------------------------
# Tools with detailed description
# ---------------------------
tools = [
    Tool(
        name="FetchData",
        func=fetchdata_with_log,
        description=(
            "Use this tool to fetch employee information from the database. "
            "You must provide (field, identifier). "
            "Valid fields: employee_id, name, office, address, experience, phone_number, skill_set. "
            "Identifier can be either employee_id or name. "
            "Examples:\n"
            "- fetchdata('employee_id', {'name': 'Sujoy'})\n"
            "- fetchdata('phone_number', {'employee_id': '2'})\n"
            "- fetchdata('address', {'name': 'Sujoy'})\n"
            "User may ask:\n"
            "- 'What is the employee id of Sujoy?'\n"
            "- 'What is the phone number of employee id 2?'\n"
            "- 'What is the address of Sujoy?'\n"
            "- 'What is the skill set of Sunita?'"
        ),
    ),
    Tool(
        name="UpdateData",
        func=updatedata_with_log,
        description=(
            "Use this tool to update employee information in the database. "
            "You must provide (field, value, identifier). "
            "Valid fields: phone_number, address, office, skill_set. "
            "Identifier can be either employee_id or name. "
            "Examples:\n"
            "- updatedata('phone_number', '462347382', {'employee_id': '2'})\n"
            "- updatedata('address', 'Kolkata', {'name': 'Sujoy'})\n"
            "- updatedata('skill_set', 'C, Java, Python', {'name': 'Raktim'})\n"
            "- updatedata('phone_number', '51215451612', {'name': 'Sunita'})\n"
            "User may request updates like:\n"
            "- 'Update employee id = 2 phone number 462347382'\n"
            "- 'Update Sujoy address to hvdshjvdhs'\n"
            "- 'Update Raktim skill set to C,Java, Python'\n"
            "- 'Update Sunita phone number to 51215451612'"
        ),
    ),
]

# ---------------------------
# Create LangGraph agent with role-based system prompt
# ---------------------------

system_prompt = (
    "You are Agent2, an HR database assistant for employee management.\n"
    "Your responsibilities:\n"
    "- If the user asks for existing employee details (id, phone number, address, office, skills, experience), call FetchData.\n"
    "- If the user requests a change or update, call UpdateData.\n"
    "- Always map natural language terms to valid SQL fields: "
    "employee_id, name, office, address, experience, phone_number, skill_set.\n"
    "- Always choose the correct identifier (either employee_id or name).\n"
    "- Never guess values — only return results from the database.\n"
    "- If unsure, ask the user for clarification instead of assuming."
)


agent2_app = create_react_agent(
    llm,
    tools=tools,
    prompt=system_prompt
)

# ✅ Wrapper for orchestrator
# keep your existing code as is...

def agent2_handler(prompt: str) -> str:
    """Entry point for Orchestrator to call Agent2."""
    result = agent2_app.invoke({
        "messages": [
            ("user", prompt)
        ]
    })
    return result["messages"][-1].content
