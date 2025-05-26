import streamlit as st
import random
import time
import re
import asyncio
import os
import spacy

# --- Streamlit App Configuration and Styling ---
st.set_page_config(
    page_title="Nigeria Info Chatbot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for white and green theme, and basic animation
st.markdown(
    """
    <style>
    /* Dominant white background for the entire app */
    .stApp {
        background-color: white;
        color: #2E8B57; /* Darker green for general text */
    }

    /* Sidebar background and text (Still kept for general Streamlit styling) */
    [data-testid="stSidebar"] {
        background-color: #F0FFF0; /* Very light green/mint */
        color: #2E8B57; /* Dark green for sidebar text */
    }

    /* Header/Title */
    h1 { /* Targeting H1 tag for the main title */
        color: #2E8B57; /* Dark green title */
        text-align: center;
        margin-bottom: 20px;
    }

    /* User chat message bubble - light green background */
    /* This targets the actual content container within the user's chat message */
    [data-testid="stChatMessage"] div.st-emotion-cache-nahz7x { /* This class is for user messages */
        background-color: #E0FFE0; /* Light green for user messages */
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 8px;
        color: #1A1A1A; /* Dark text for readability */
    }

    /* Bot chat message bubble - off-white/light mint background with green border and animation */
    /* This targets the actual content container within the assistant's chat message */
    [data-testid="stChatMessage"] div.st-emotion-cache-1c7y2qn { /* This class is for assistant messages */
        background-color: #F5FFFA; /* Very light mint/off-white */
        border-left: 5px solid #2E8B57; /* Dark green accent border */
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 8px;
        color: #1A1A1A; /* Dark text for readability */
        animation: fadeIn 1s ease-in-out; /* Apply fade-in animation */
    }

    /* Input widget (text input for chat) */
    /* This targets the overall container for the chat input */
    .st-emotion-cache-10qj07o { /* Common class for the text input container */
        background-color: white; /* Ensure input area is white */
        border-top: 1px solid #2E8B57; /* Green line above input */
        padding-top: 10px;
    }
    /* This targets the actual input field */
    [data-testid="stTextInput"] input {
        border: 2px solid #2E8B57; /* Green border for input field */
        border-radius: 8px;
        padding: 10px;
        color: #2E8B57; /* Green text in input */
        background-color: white;
    }
    /* This targets the label of the input field */
    [data-testid="stTextInput"] label {
        color: #2E8B57; /* Green label for input */
    }

    /* Buttons (e.g., submit button) */
    /* This targets the "Send" button in the chat input */
    .st-emotion-cache-r42kk1 { /* Common class for buttons */
        background-color: #2E8B57; /* Dark green button */
        color: white; /* White text on button */
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        transition: background-color 0.3s ease; /* Smooth hover effect */
    }
    .st-emotion-cache-r42kk1:hover {
        background-color: #3CB371; /* Lighter green on hover */
        color: white;
    }

    /* General Markdown text color (for responses) */
    /* This ensures text within markdown containers (like your responses) is readable */
    .st-emotion-cache-cnbnn3 p { /* Targets paragraphs within markdown containers */
        color: #1A1A1A; /* Ensure response text is readable dark color */
    }

    /* Animation Keyframes */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load the SpaCy English model
# This will load the model downloaded in the terminal (en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    st.error("SpaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm' in your terminal.")
    st.stop() # Stop the app if model is not found


# --- Helper functions for NLP processing ---
def preprocess_text_for_matching(text): # Removed use_stemming parameter
    """
    Tokenizes, converts to lowercase, removes stopwords, and lemmatizes the text using SpaCy.
    Returns a space-separated string of processed words.
    """
    doc = nlp(text.lower()) # Process text with SpaCy
    processed_tokens = []
    for token in doc:
        # Check if it's an alphabetic token and not a stop word
        if token.is_alpha and not token.is_stop:
            # Use token.lemma_ for lemmatization
            processed_tokens.append(token.lemma_)
    return " ".join(processed_tokens) # Return as a single string for TfidfVectorizer

# 1. Define Initial Greetings ---
INITIAL_GREETINGS = [
    "Hello there! How can I assist you today regarding the Nigerian Government?",
    "Hi, human! I'm GovFocus AI, ready to help you with information about the Nigerian Government. What's on your mind?",
    "Welcome! Ask me anything about the Nigeria Government. I'm here to provide information.",
    "Greetings! What specific information are you seeking about the Nigerian government today?"
]

# --- 2. Define User Greeting Keywords and Corresponding Assistant Responses ---
USER_GREETING_KEYWORDS = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
ASSISTANT_GREETING_RESPONSES = [
    "Hello! How can I help you with information about the Nigerian government?",
    "Hi there! What can I tell you about the Nigerian government today?",
    "Hey! Ask away about the Nigerian government.",
    "Greetings! What's your question regarding the Nigerian government?"
]

# --- Initialize TF-IDF Vectorizer and Process KB ---
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from knowledge_base import RAW_KNOWLEDGE_BASE

# FIX: Set lowercase=True to ensure consistency with preprocess_text_for_matching
vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split(), lowercase=True)


processed_kb_keys_list = [
    preprocess_text_for_matching(key)
    for key in RAW_KNOWLEDGE_BASE.keys()
]


kb_vectors = vectorizer.fit_transform(processed_kb_keys_list)

KB_ENTRIES_FOR_MATCHING = list(RAW_KNOWLEDGE_BASE.items())

# --- 4. Function to Check for User Greetings ---
def check_for_user_greeting(query):
    query_lower = query.lower()
    for keyword in USER_GREETING_KEYWORDS:
        if keyword in query_lower:
            return random.choice(ASSISTANT_GREETING_RESPONSES)
    return None

# --- 5. Function to Search Knowledge Base (using TF-IDF and Cosine Similarity) ---
def get_response_from_kb(query, similarity_threshold=0.3): # Adjust threshold as needed
    processed_user_query_str = preprocess_text_for_matching(query)

    # TEMPORARY DEBUGGING PRINTS (will appear in Codespaces terminal/logs)
    print(f"\n--- KB Matching Debug ---")
    print(f"User Query (Raw): {query}")
    print(f"User Query (Processed): '{processed_user_query_str}'")

    if not processed_user_query_str.strip():
        print("No meaningful words in processed user query.")
        return None

    user_query_vector = vectorizer.transform([processed_user_query_str])

    similarity = cosine_similarity(user_query_vector, kb_vectors)

    best_match_index = similarity.argmax()
    highest_similarity_score = similarity[0, best_match_index]

    print(f"Highest Similarity Score: {highest_similarity_score:.2f}")
    if best_match_index < len(KB_ENTRIES_FOR_MATCHING): # Safety check
        matched_kb_original_key = KB_ENTRIES_FOR_MATCHING[best_match_index][0]
        print(f"Matching KB Original Key: {matched_kb_original_key}")
        print(f"Matching KB Processed Key: {processed_kb_keys_list[best_match_index]}")
    else:
        print(f"ERROR: best_match_index ({best_match_index}) out of bounds for KB_ENTRIES_FOR_MATCHING (size {len(KB_ENTRIES_FOR_MATCHING)})")


    if highest_similarity_score >= similarity_threshold:
        return KB_ENTRIES_FOR_MATCHING[best_match_index][1]

    print(f"No significant KB match found above threshold ({similarity_threshold:.2f}).")
    return None

# --- Streamed response emulator (ASYNCHRONOUS) ---
async def response_generator(response_text):
    for word in response_text.split():
        yield word + " "
        await asyncio.sleep(0.05)

st.title("🇳🇬 GovFocus AI: Your Guide to the Nigerian Government")
st.markdown("Ask me anything about the Nigerian Government.")

# --- Initialize ALL session state variables here ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.first_message_displayed = False

# --- Display initial greeting if it's the first run (and only once per session) ---
if not st.session_state.first_message_displayed:
    initial_greeting = random.choice(INITIAL_GREETINGS)
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(initial_greeting))
    st.session_state.messages.append({"role": "assistant", "content": initial_greeting})
    st.session_state.first_message_displayed = True
    st.balloons() # Added balloons animation on initial load

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)


# Accept user input
if prompt := st.chat_input("What do you want me to talk to you about:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt, unsafe_allow_html=True)

    # --- Determine assistant response based on hierarchy: Greeting -> KB -> Fallback ---
    assistant_response = None

    # 1. Check for user greetings first
    greeting_response = check_for_user_greeting(prompt)
    if greeting_response:
        assistant_response = greeting_response
    else:
        # 2. If no greeting, check knowledge base using processed query
        with st.spinner("Searching knowledge base..."):
            assistant_response = get_response_from_kb(prompt)

    # 3. If still no response, use fallback (now a fixed message as OpenAI removed)
    if not assistant_response:
        assistant_response = "I can not respond to this now. In future iterations, I will be able to provide an answer. I am still a work in progress."

    # Display the chosen assistant response
    with st.chat_message("assistant"):
        response_stream = response_generator(assistant_response)
        response = st.write_stream(response_stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
