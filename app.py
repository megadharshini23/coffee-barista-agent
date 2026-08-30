
# app.py
import streamlit as st
import json

# Set page config for a premium look
st.set_page_config(
    page_title="☕ Coffee Shop - Barista Bot",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to make the header sticky
st.markdown("""
<style>
    div[data-testid="element-container"]:has(.header-container),
    div.element-container:has(.header-container) {
        position: sticky;
        top: 2.875rem;
        z-index: 999;
        background-color: transparent;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.title("☕ Coffee Shop")
st.write("Your friendly AI Barista is ready to help you find the perfect drink or pastry!")

# ============================================================
# LOAD MENU FROM FIRESTORE
# ============================================================

# [START load_menu]
from google.cloud import firestore

try:
    db = firestore.Client(database="coffee-menu")

    docs = db.collection("menu").stream()

    menu_items = []

    for doc in docs:
        item = doc.to_dict()

        # Remove embedding before displaying the menu
        item.pop("embedding", None)

        menu_items.append(item)

except Exception as e:
    st.error(f"Error loading menu from Firestore: {e}")
    menu_items = []

# [END load_menu]


# ============================================================
# SIDEBAR MENU
# ============================================================

with st.sidebar:

    st.markdown("## ☕ Coffee Shop Menu")

    st.markdown(
        "Explore our offerings and ask the barista for recommendations."
    )

    st.markdown("---")

    for item in menu_items:

        with st.container(border=True):

            st.markdown(
                f"**{item['name']}**  •  **${item['price']:.2f}**"
            )

            st.caption(item["description"])

            # Tags
            tags = " ".join(
                [f"`{t}`" for t in item.get("tags", [])]
            )

            if tags:
                st.markdown(tags)

            # Allergens
            allergens = ", ".join(
                item.get("allergens", [])
            )

            if allergens:
                st.markdown(
                    f"⚠️ *Allergens: {allergens}*"
                )


# ============================================================
# CHAT INTERFACE
# ============================================================

if "session_id" not in st.session_state:

    import uuid

    st.session_state.session_id = str(uuid.uuid4())


# Create ADK runner
if "runner" not in st.session_state:

    from google.adk.runners import InMemoryRunner
    from agent import app

    st.session_state.runner = InMemoryRunner(app=app)


# Initialize chat messages
if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Welcome to ☕ Coffee Shop! "
                "What can I get started for you today?"
            )
        }
    ]


# ============================================================
# DISPLAY EXISTING MESSAGES
# ============================================================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])


# ============================================================
# USER INPUT
# ============================================================

if prompt := st.chat_input(
    "Ask for recommendations "
    "(e.g., 'What dairy-free pastries do you have?')"
):

    # Display user message
    with st.chat_message("user"):

        st.markdown(prompt)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )


    # Generate AI response
    with st.chat_message("assistant"):

        try:

            import asyncio

            async def fetch_response():

                return await st.session_state.runner.run_debug(
                    prompt,
                    session_id=st.session_state.session_id
                )


            # Run ADK agent
            res_events = asyncio.run(
                fetch_response()
            )


            # Extract response text
            response_text = "".join(
                [
                    part.text
                    for event in res_events
                    if event.content
                    and event.content.parts
                    for part in event.content.parts
                    if part.text
                ]
            )


            # Display response
            st.markdown(response_text)


            # Save response
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response_text
                }
            )


        except Exception as e:

            st.error(
                f"Apologies, I ran into an error: {e}"
            )
            
