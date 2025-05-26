import streamlit as st
import random
import time
import re
import asyncio
import os
import spacy
import openai # Import the OpenAI library

# --- Load the knowledge base ---
from knowledge_base import RAW_KNOWLEDGE_BASE

# --- Load SpaCy Model (handle potential download issue on Streamlit Cloud) ---
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    st.error("SpaCy model 'en_core_web_sm' not found. Attempting to download...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# --- Initialize OpenAI Client ---
# Use st.secrets to securely access the API key
if "OPENAI_API_KEY" in st.secrets:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
else:
    st.error("OpenAI API key not found. Please set it in your .streamlit/secrets.toml file.")
    st.stop() # Stop the app if API key is missing

# --- Helper functions for NLP processing ---
def preprocess_text_for_matching(text):
    """
    Tokenizes, converts to lowercase, removes stopwords, and lemmatizes the text using SpaCy.
    Returns a space-separated string of processed words.
    """
    doc = nlp(text.lower())
    processed_tokens = []
    for token in doc:
        if token.is_alpha and not token.is_stop:
            processed_tokens.append(token.lemma_)
    processed_str = " ".join(processed_tokens)
    st.sidebar.write(f"Preprocessing Debug: '{text}' -> '{processed_str}'")
    return processed_str

# --- Define Initial Greetings ---
INITIAL_GREETINGS = [
    "Hello there! How can I assist you today regarding the Nigerian Government?",
    "Hi, human! I'm GovFocus AI, ready to help you with information about the Nigerian Government. What's on your mind?",
    "Welcome! Ask me anything about the Nigeria Government. I'm here to provide information.",
    "Greetings! What specific information are you seeking about the Nigerian government today?"
]

# --- Define User Greeting Keywords and Corresponding Assistant Responses ---
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

vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split(), lowercase=False)

processed_kb_keys_list = [
    preprocess_text_for_matching(key)
    for key in RAW_KNOWLEDGE_BASE.keys()
]

kb_vectors = vectorizer.fit_transform(processed_kb_keys_list)

KB_ENTRIES_FOR_MATCHING = list(RAW_KNOWLEDGE_BASE.items())

# --- Pre-compute state names and their mapping for governor lookup ---
GOVERNORS_KB_KEY = "Current Governors of Nigerian States (as of May 2025)"
governors_list_content = RAW_KNOWLEDGE_BASE.get(GOVERNORS_KB_KEY, "")

ALL_FORMAL_STATE_NAMES = []
STATE_NAME_MAP = {} # Maps lowercased aliases to formal names (e.g., "lagos" -> "Lagos State")

if governors_list_content:
    state_pattern = r"\*\*([A-Za-z\s]+? State):\*\*"
    matches = re.findall(state_pattern, governors_list_content)
    
    for formal_name in matches:
        formal_name_stripped = formal_name.strip()
        ALL_FORMAL_STATE_NAMES.append(formal_name_stripped)
        STATE_NAME_MAP[formal_name_stripped.lower()] = formal_name_stripped
        if " State" in formal_name_stripped:
            STATE_NAME_MAP[formal_name_stripped.replace(" State", "").strip().lower()] = formal_name_stripped

    if "Federal Capital Territory (Minister):" in governors_list_content:
        ALL_FORMAL_STATE_NAMES.append("Federal Capital Territory")
        STATE_NAME_MAP["federal capital territory"] = "Federal Capital Territory"
        STATE_NAME_MAP["fct"] = "Federal Capital Territory"
        STATE_NAME_MAP["abuja"] = "Federal Capital Territory"

# --- Function to Check for User Greetings ---
def check_for_user_greeting(query):
    query_lower = query.lower()
    for keyword in USER_GREETING_KEYWORDS:
        if keyword in query_lower:
            return random.choice(ASSISTANT_GREETING_RESPONSES)
    return None

# --- Function to Search Knowledge Base (using TF-IDF and Cosine Similarity) ---
def get_response_from_kb(query, similarity_threshold=0.3):
    processed_user_query_str = preprocess_text_for_matching(query)

    st.sidebar.write(f"--- Query Matching Debug ---")
    st.sidebar.write(f"User Query (Raw): {query}")
    st.sidebar.write(f"User Query (Processed): '{processed_user_query_str}'")

    if not processed_user_query_str.strip():
        st.sidebar.write("No meaningful words in processed user query.")
        return None

    user_query_vector = vectorizer.transform([processed_user_query_str])

    similarities = cosine_similarity(user_query_vector, kb_vectors)

    best_match_index = similarities.argmax()
    highest_similarity_score = similarities[0, best_match_index]

    st.sidebar.write(f"Highest Similarity Score: {highest_similarity_score:.2f}")
    matched_kb_original_key = KB_ENTRIES_FOR_MATCHING[best_match_index][0]
    st.sidebar.write(f"Matching KB Original Key: {matched_kb_original_key}")
    st.sidebar.write(f"Matching KB Processed Key: {processed_kb_keys_list[best_match_index]}")

    if highest_similarity_score >= similarity_threshold:
        full_kb_content_for_key = KB_ENTRIES_FOR_MATCHING[best_match_index][1]

        if matched_kb_original_key == GOVERNORS_KB_KEY:
            st.sidebar.write(f"--- Governor Specific Lookup Debug ---")
            query_lower = query.lower()
            
            target_state_name_formal = None

            st.sidebar.write(f"Attempting to detect state in query: '{query_lower}'")
            for alias_lower, formal_name in STATE_NAME_MAP.items():
                if alias_lower in query_lower:
                    target_state_name_formal = formal_name
                    st.sidebar.write(f"Detected State Alias in query: '{alias_lower}' -> Formal Name: '{formal_name}'")
                    break
            
            if target_state_name_formal:
                if target_state_name_formal == "Federal Capital Territory":
                    governor_regex = r"\*\*Federal Capital Territory \(Minister\):\*\*\s*(.+?)(?=\n\*|$)"
                else:
                    escaped_state_name = re.escape(target_state_name_formal)
                    governor_regex = rf"\*\*({escaped_state_name}):\*\*\s*(.+?)(?=\n\*|$)"

                st.sidebar.write(f"Attempting to find governor for: '{target_state_name_formal}'")
                st.sidebar.write(f"Using Regex Pattern: '{governor_regex}'")
                st.sidebar.write(f"Searching in content starting with: '{full_kb_content_for_key[:100]}...'")
                
                match = re.search(governor_regex, full_kb_content_for_key, re.DOTALL)
                
                if match:
                    governor_info = match.group(2).strip()
                    st.sidebar.write(f"Regex Match Found! Full Match: '{match.group(0)}'")
                    st.sidebar.write(f"Extracted Governor Info: '{governor_info}'")
                    return f"The current {target_state_name_formal} is: {governor_info}."
                else:
                    st.sidebar.write(f"Regex search FAILED for state: '{target_state_name_formal}' with pattern: '{governor_regex}'.")
                    return f"I found information about Nigerian governors, but couldn't pinpoint the specific governor for {target_state_name_formal} from my list. " \
                           "The information might not be precisely formatted or available for direct extraction."
            else:
                st.sidebar.write(f"No specific state name detected in query: '{query_lower}' for governor lookup.")
                return "I have information about Nigerian governors. Please specify which state's governor you are interested in (e.g., 'governor of Lagos State', 'who is the governor of Kano?'). If you'd like to see the full list, please ask for 'all governors' or 'list all governors'."
        
        st.sidebar.write(f"Returning full KB content for matched key: '{matched_kb_original_key}' (not governor list, or no specific state requested).")
        return full_kb_content_for_key
    
    st.sidebar.write(f"No significant KB match found above threshold ({similarity_threshold:.2f}).")
    return None

# --- Streamed response emulator (ASYNCHRONOUS) ---
async def response_generator(response_text):
    for word in response_text.split():
        yield word + " "
        await asyncio.sleep(0.05)

# --- New Function: Get response from OpenAI (ChatGPT) ---
async def get_gpt_response(query_text, chat_history):
    """
    Queries the OpenAI API for a response, based on the user's query and recent chat history.
    Yields chunks for streaming effect.
    """
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. You can answer general questions and engage in conversation. If asked about very specific details of the Nigerian government, you can answer broadly but suggest consulting official sources if information is limited."}
    ]
    
    # Add recent chat history for context (last few turns)
    # Limit history to avoid excessive token usage and maintain focus
    for msg in chat_history[-6:]: # Include last 3 user and 3 assistant messages
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": query_text})

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # You can try "gpt-4" or "gpt-4o" for better quality (and higher cost)
            messages=messages,
            stream=True, # Enable streaming for the typing effect
            temperature=0.7 # Adjust creativity (0.0-1.0)
        )
        
        # Yield content chunks from the OpenAI stream
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except openai.APIError as e:
        st.error(f"OpenAI API error: {e}")
        yield "I'm sorry, I couldn't reach the AI service right now. Please check your API key or try again later."
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        yield "An unexpected error occurred while processing your request. Please try again."


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

    /* Sidebar background and text */
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
    [data-testid="stChatMessage"] div.st-emotion-cache-nahz7x {
        background-color: #E0FFE0; /* Light green for user messages */
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 8px;
        color: #1A1A1A; /* Dark text for readability */
    }

    /* Bot chat message bubble - off-white/light mint background with green border and animation */
    .st-emotion-cache-1c7y2qn [data-testid="stMarkdownContainer"] { /* This class targets the bot message container */
        background-color: #F5FFFA; /* Very light mint/off-white */
        border-left: 5px solid #2E8B57; /* Dark green accent border */
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 8px;
        color: #1A1A1A; /* Dark text for readability */
        animation: fadeIn 1s ease-in-out; /* Apply fade-in animation */
    }

    /* Input widget (text input for chat) */
    .st-emotion-cache-10qj07o { /* Common class for the text input container */
        background-color: white; /* Ensure input area is white */
        border-top: 1px solid #2E8B57; /* Green line above input */
        padding-top: 10px;
    }
    [data-testid="stTextInput"] input {
        border: 2px solid #2E8B57; /* Green border for input field */
        border-radius: 8px;
        padding: 10px;
        color: #2E8B57; /* Green text in input */
        background-color: white;
    }
    [data-testid="stTextInput"] label {
        color: #2E8B57; /* Green label for input */
    }

    /* Buttons (e.g., submit button) */
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


# --- Streamlit Chat UI ---
st.title("🇳🇬 GovFocus AI: Your Guide to the Nigerian Government")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.first_message_displayed = False

# Display initial greeting if it's the first run (and only once per session)
if not st.session_state.first_message_displayed:
    initial_greeting = random.choice(INITIAL_GREETINGS)
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(initial_greeting))
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.first_message_displayed = True
    st.balloons() # Play balloons animation on initial load

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Accept user input
if prompt := st.chat_input("What do you want me to talk to you about:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt, unsafe_allow_html=True)

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."): # Shorter spinner message
            assistant_response_kb = get_response_from_kb(prompt)

        if assistant_response_kb:
            # KB found a response, display it with typing animation
            response_stream_generator = response_generator(assistant_response_kb)
            final_response = st.write_stream(response_stream_generator)
            st.session_state.messages.append({"role": "assistant", "content": final_response})
        else:
            # KB found no response, fall back to ChatGPT
            st.spinner("No specific KB match. Consulting broader AI...") # New spinner message
            try:
                # Pass the chat history to GPT for context
                gpt_stream_generator = get_gpt_response(prompt, st.session_state.messages) 
                final_gpt_response = st.write_stream(gpt_stream_generator)
                st.session_state.messages.append({"role": "assistant", "content": final_gpt_response})
            except Exception as e:
                st.error(f"Failed to get response from AI: {e}")
                fallback_text = "I'm sorry, but I encountered an issue connecting to the broader AI. Please try again later."
                st.session_state.messages.append({"role": "assistant", "content": fallback_text})