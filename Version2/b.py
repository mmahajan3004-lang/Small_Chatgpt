from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b"
)

class ChatState(TypedDict):

    messages: Annotated[
        list[BaseMessage],
        add_messages
    ]

def chat_node(state: ChatState):

    messages = state["messages"]

    response = llm.invoke(messages)

    return {
        "messages": [response]
    }

conn = sqlite3.connect(
    "data/database.db",
    check_same_thread=False
)

memory = SqliteSaver(conn)
memory.setup()

conn.execute("""
CREATE TABLE IF NOT EXISTS chat_titles (
    thread_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

graph = StateGraph(ChatState)


graph.add_node("chat_node",chat_node)
graph.add_edge(START,"chat_node")
graph.add_edge("chat_node",END)

workflow = graph.compile(checkpointer=memory)
 
def generate_chat_title(message):

    prompt = f"""
Generate a short and meaningful title for this conversation.

User message:
{message}

Rules:
- Maximum 5 words
- Describe the main topic
- Keep it concise
- Natural sounding
- Do not use quotation marks
- Do not use words like Chat, Conversation, or Question
- Return ONLY the title
"""

    response = llm.invoke(prompt)

    return response.content.strip()


def create_chat(thread_id, name="New Chat"):

    conn.execute(
        """
        INSERT OR IGNORE INTO chat_titles
        (thread_id, name)
        VALUES (?, ?)
        """,
        (str(thread_id),name)
    )
    conn.commit()


def update_chat_title(thread_id, name):

    conn.execute(
        """
        UPDATE chat_titles
        SET name = ?
        WHERE thread_id = ?
        """,
        (
            name,
            str(thread_id)
        )
    )

    conn.commit()

def retrieve_all_chats():

    cursor = conn.execute(
        """
        SELECT thread_id, name
        FROM chat_titles
        ORDER BY created_at DESC
        """
    )

    chats = []

    for thread_id, name in cursor.fetchall():

        chats.append({
            "id": thread_id,
            "name": name
        })

    return chats


def retrieve_all_threads():

    all_threads = set()

    for checkpoint in memory.list(None):

        thread_id = checkpoint.config[
            "configurable"
        ].get("thread_id")

        if thread_id:

            all_threads.add(
                str(thread_id)
            )

    return list(all_threads)