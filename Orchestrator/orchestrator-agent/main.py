import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from agent1.agent1 import agent1_app
from agent2.agents.agent2 import agent2_handler
# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found in .env file")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# -------------------------------
# FastAPI app
# -------------------------------
app = FastAPI(title="LangGraph Orchestrator Agent")

# -------------------------------
# Agent Handlers
# -------------------------------
def agent1_handler(prompt: str) -> str:
    return f"🤖 Agent1 processed: {prompt}"

def agent2_handler(prompt: str) -> str:
    """Wrapper that invokes the LangGraph Agent2"""
    state = agent2.invoke({"messages": [("user", prompt)]})
    # Get the assistant’s final message
    return state["messages"][-1].content


AGENTS = {
    "Agent1": {
        "description": (
            "Agent1 is a multi-purpose assistant. "
            "It supports three tools:\n"
            "- ContentReader: stores user-provided content into memory.\n"
            "- QnATool: answers questions strictly from the stored content.\n"
            "- MailSender: sends an email with a subject and message.\n\n"
            "Use Agent1 when the task involves reading/storing content, "
            "answering questions from memory, or sending emails."
        ),
        "handler": lambda prompt: agent1_app.invoke({"input": prompt})["output"],  # Agent1's LangGraph app
    },
    "Agent2": {
        "description": (
            "Agent2 is an HR Database Assistant specialized in employee management. "
            "It supports two tools:\n"
            "- FetchData: retrieves employee details such as ID, phone number, address, "
            "office, skills, or experience from the database.\n"
            "- UpdateData: updates employee records (phone number, address, office, or skill set).\n\n"
            "Use Agent2 when the task involves employee data lookup or updates."
        ),
        "handler": agent2_handler,  # your wrapper that calls the LangGraph agent2
    },
}


# -------------------------------
# LangGraph State
# -------------------------------
class OrchestratorState(TypedDict):
    prompt: str
    decision: str
    result: str

# -------------------------------
# Graph Nodes
# -------------------------------
def decide_agent(state: OrchestratorState) -> OrchestratorState:
    decision_prompt = f"""
You are an orchestrator AI.
Choose the best agent for the user task.

Available agents:
{ {a: AGENTS[a]['description'] for a in AGENTS} }

User prompt: "{state['prompt']}"

Rules:
- Reply with exactly one agent name: "Agent1" or "Agent2".
"""
    decision = llm.invoke(decision_prompt).content.strip()
    state["decision"] = decision if decision in AGENTS else "Agent1"
    return state

def execute_agent(state: OrchestratorState) -> OrchestratorState:
    agent = AGENTS[state["decision"]]
    state["result"] = agent["handler"](state["prompt"])
    return state

# -------------------------------
# Build LangGraph Workflow
# -------------------------------
workflow = StateGraph(OrchestratorState)

workflow.add_node("decide_agent", decide_agent)
workflow.add_node("execute_agent", execute_agent)

workflow.set_entry_point("decide_agent")
workflow.add_edge("decide_agent", "execute_agent")
workflow.add_edge("execute_agent", END)

app_graph = workflow.compile()

# -------------------------------
# API Schema
# -------------------------------
class Request(BaseModel):
    prompt: str

class Response(BaseModel):
    agent: str
    result: str

@app.get("/")
async def root():
    return {"message": "🚀 Orchestrator API is running! Use POST /run"}


# -------------------------------
# REST API Endpoint
# -------------------------------
@app.post("/run", response_model=Response)
def run_task(request: Request):
    inputs = {"prompt": request.prompt, "decision": "", "result": ""}
    final_state = app_graph.invoke(inputs)
    return Response(agent=final_state["decision"], result=final_state["result"])

# -------------------------------
# Run: uvicorn main:app --reload
# -------------------------------
