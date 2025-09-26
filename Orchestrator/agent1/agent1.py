import os
import smtplib
from email.mime.text import MIMEText
from typing import Dict

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents import Tool

# -------------------------------
# Load Gemini API Key
# -------------------------------
os.environ["GOOGLE_API_KEY"] = "AIzaSyDYXC4Uu1LpDyFQWzdrZJT17G_1p2Ay5yk"

# -------------------------------
# Global Memory for Content
# -------------------------------
memory: Dict[str, str] = {"content": ""}

# -------------------------------
# Initialize Gemini LLM
# -------------------------------
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# -------------------------------
# Tool 1: Content Reader
# -------------------------------
def content_reader(content: str) -> str:
    """Reads and stores content into memory for later use."""
    memory["content"] = content
    return "✅ Content stored successfully."

content_reader_tool = Tool(
    name="ContentReader",
    func=content_reader,
    description=(
        "Use this tool when the user provides raw content that needs to be remembered. "
        "This will store the text in memory for future Q&A."
    ),
)

# -------------------------------
# Tool 2: Mail Sender
# -------------------------------
def mail_sender(email: str, message: str) -> str:
    """Sends an email to the given recipient with the provided message."""
    try:
        sender_email = "your-email@gmail.com"
        sender_password = "your-app-password"

        msg = MIMEText(message)
        msg["Subject"] = "AI Agent Message"
        msg["From"] = sender_email
        msg["To"] = email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())

        return f"📧 Email successfully sent to {email}"
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"

mail_sender_tool = Tool(
    name="MailSender",
    func=lambda inputs: mail_sender(inputs["email"], inputs["message"]),
    description=(
        "Use this tool when the user requests to send an email. "
        "Input should include an email and a message body."
    ),
)

# -------------------------------
# Tool 3: Q&A Tool
# -------------------------------
def qa_tool(question: str) -> str:
    """Answers questions only from the stored content in memory."""
    if not memory["content"]:
        return "⚠️ No content stored yet. Please provide content first."
    prompt = f"""
    You are a helpful assistant. Use only the following content to answer:

    Content: {memory['content']}

    Question: {question}
    Answer:
    """
    response = llm.invoke(prompt)
    return response.content

qa_tool_instance = Tool(
    name="QnATool",
    func=qa_tool,
    description=(
        "Use this tool when the user asks a question about the previously provided content. "
        "It will only answer based on what is stored in memory."
    ),
)

# -------------------------------
# Build LangGraph Agent
# -------------------------------
tools = [content_reader_tool, mail_sender_tool, qa_tool_instance]

# -------------------------------
# Agent Node with Strong Prompting
# -------------------------------
def agent_node(state):
    """Decide best tool based on user input and run it."""
    user_input = state["input"]

    # Stronger, explicit system prompt
    decision_prompt = f"""
You are an AI agent with 3 tools.
Always select the correct tool for the user's request.

TOOLS:
1. ContentReader → Use ONLY when the user provides content that should be stored in memory.
   Example:
     - "Here is some content: Climate change is affecting agriculture."
     - "Save this text for later use."

2. MailSender → Use ONLY when the user wants to send an email.
   Input must contain a recipient email and a message.
   Example:
     - "Send email to test@example.com with message Hello, how are you?"
     - "Mail sujoy@example.com saying Your meeting is tomorrow."

3. QnATool → Use ONLY when the user asks a question about previously stored content.
   Example:
     - "What is climate change?"
     - "Summarize the content I gave."
     - "Tell me the key points."

IMPORTANT RULES:
- If the user gives content → use ContentReader.
- If the user mentions email/mail → use MailSender.
- If the user asks a question → use QnATool.
- Never answer directly. Always pick one tool.
- Output only the tool name (ContentReader, MailSender, or QnATool).

User request: "{user_input}"
Which tool should be used?
"""

    decision = llm.invoke(decision_prompt)
    decision_text = decision.content.strip().lower()

    # Match tool names
    if "contentreader" in decision_text:
        return {"output": content_reader(user_input)}
    elif "mailsender" in decision_text:
        try:
            parts = user_input.split("with message")
            email = parts[0].split("to")[1].strip()
            message = parts[1].strip()
            return {"output": mail_sender(email, message)}
        except Exception:
            return {"output": "⚠️ Invalid email input format. Example: send email to test@example.com with message Hello"}
    elif "qnatool" in decision_text:
        return {"output": qa_tool(user_input)}
    else:
        return {"output": f"🤔 I couldn't decide. My reasoning was: {decision_text}"}


# Define LangGraph Workflow
graph = StateGraph(dict)
graph.add_node("agent", agent_node)
graph.set_entry_point("agent")
graph.add_edge("agent", END)

agent1_app = graph.compile()

# -------------------------------
# Run Agent
# -------------------------------
if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Agent stopped.")
            break
        result = agent1_app.invoke({"input": user_input})
        print("Agent:", result["output"])
