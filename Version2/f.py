import streamlit as st
import uuid

from Version2.b import (
    workflow,
    retrieve_all_chats,
    create_chat,
    update_chat_title,
    generate_chat_title
)

from langchain_core.messages import HumanMessage

def generate_thread_id():

    return str(uuid.uuid4())


def add_thread(thread_id, name="New Chat"):

    existing_ids = [
        chat["id"]
        for chat in st.session_state["chat_threads"]
    ]

    if thread_id not in existing_ids:

        st.session_state["chat_threads"].append({
            "id": thread_id,
            "name": name
        })

        create_chat(
            thread_id,
            name
        )

def reset_chat():

    thread_id = generate_thread_id()

    st.session_state["thread_id"] = thread_id

    add_thread(
        thread_id,
        "New Chat"
    )

    st.session_state["message_history"] = []


def load_conversation(thread_id):

    state = workflow.get_state(
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return state.values.get(
        "messages",
        []
    )

if "message_history" not in st.session_state:

    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:

    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:

    st.session_state["chat_threads"] = retrieve_all_chats()


current_thread_id = st.session_state["thread_id"]

existing_ids = [
    chat["id"]
    for chat in st.session_state["chat_threads"]
]

if current_thread_id not in existing_ids:

    add_thread(
        current_thread_id,
        "New Chat"
    )

st.sidebar.title("MiniChatGPT")

if st.sidebar.button(
    "New Chat",
    use_container_width=True
):
    
    reset_chat()
    st.rerun()

st.sidebar.header("Recent")

for chat in st.session_state["chat_threads"]:

    thread_id = chat["id"]

    chat_name = chat["name"]

    if st.sidebar.button(
        chat_name,
        key=f"chat_{thread_id}",
        use_container_width=True
    ):

        st.session_state["thread_id"] = thread_id

        messages = load_conversation(
            thread_id
        )

        temp_msg = []

        for msg in messages:

            if isinstance(msg,HumanMessage):
                role = "user"
            else:
                role = "assistant"

            temp_msg.append({
                "role": role,
                "content": msg.content
            })

        st.session_state["message_history"] = temp_msg
        st.rerun()

for message in st.session_state["message_history"]:

    with st.chat_message(
        message["role"]
    ):

        st.write(
            message["content"]
        )

user_input = st.chat_input(
    "Type here"
)

if user_input:

    current_thread_id = st.session_state["thread_id"]

    is_first_message = (
        len(
            st.session_state["message_history"]
        ) == 0
    )

    if is_first_message:

        chat_title = generate_chat_title(
            user_input
        )

        for chat in st.session_state["chat_threads"]:

            if chat["id"] == current_thread_id:

                chat["name"] = chat_title

                break

        update_chat_title(
            current_thread_id,
            chat_title
        )

    st.session_state["message_history"].append({

        "role": "user",

        "content": user_input

    })

    with st.chat_message("user"):

        st.write(
            user_input
        )

    CONFIG = {

        "configurable": {
            "thread_id": current_thread_id
        },

        "metadata": {
            "thread_id": current_thread_id
        },

        "run_name": "chat_turn"

    }

    with st.chat_message("assistant"):

        response_stream = workflow.stream(

            {
                "messages": [
                    HumanMessage(
                        content=user_input
                    )
                ]
            },

            config=CONFIG,

            stream_mode="messages"

        )

        ai_message = st.write_stream(

            message_chunk.content

            for message_chunk, metadata
            in response_stream

            if message_chunk.content

        )

    st.session_state["message_history"].append({

        "role": "assistant",

        "content": ai_message

    })