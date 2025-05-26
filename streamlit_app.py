import streamlit as st
import random
import time
import re
import asyncio
import os
import spacy

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
        st.sidebar.write(f"Processed Text: '{text}' -> '{' '.join(processed_tokens)}'")
    return " ".join(processed_tokens) # Return as a single string for TfidfVectorizer
# --- 
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

vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split(), lowercase=False)


processed_kb_keys_list = [
    preprocess_text_for_matching(key) # Removed use_stemming=False
    for key in RAW_KNOWLEDGE_BASE.keys()
]


kb_vectors = vectorizer.fit_transform(processed_kb_keys_list)

KB_ENTRIES_FOR_MATCHING = list(RAW_KNOWLEDGE_BASE.items())

# Debugging: Show processed KB keys and vocabulary (uncomment if needed)
# st.sidebar.header("Debugging: Processed KB Keys (for TF-IDF)")
# for pk_str in processed_kb_keys_list:
#     st.sidebar.write(f"Processed KB Key: '{pk_str}'")
# st.sidebar.write(f"TF-IDF Vocabulary: {vectorizer.get_feature_names_out()}")


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

    # Debugging: Show raw and processed user query (uncomment if needed)
    # st.sidebar.text(f"User Query (Raw): {query}")
    # st.sidebar.text(f"User Query (Processed Str): '{processed_user_query_str}'")

    if not processed_user_query_str.strip():
        # st.sidebar.text("No meaningful words in processed user query.")
        return None

    user_query_vector = vectorizer.transform([processed_user_query_str])

    similarity = cosine_similarity(user_query_vector, kb_vectors)

    best_match_index = similarity.argmax()
    highest_similarity_score = similarity[0, best_match_index]

    st.sidebar.write(f"Highest Similarity Score: {highest_similarity_score:.2f}") # ADD THIS LINE
    st.sidebar.write(f"Matching KB Original Key: {KB_ENTRIES_FOR_MATCHING[best_match_index][0]}") # ADD THIS LINE
    st.sidebar.write(f"Matching KB Processed Key: {processed_kb_keys_list[best_match_index]}") # ADD THIS LINE

    # Debugging: Show similarity scores (uncomment if needed)
    # st.sidebar.text(f"All Similarities: {similarity[0]}")
    # st.sidebar.text(f"Highest Similarity Score: {highest_similarity_score} at index {best_match_index}")
    # st.sidebar.text(f"Matching KB Original Key: {KB_ENTRIES_FOR_MATCHING[best_match_index][0]}")

    if highest_similarity_score >= similarity_threshold:
        return KB_ENTRIES_FOR_MATCHING[best_match_index][1]

    # st.sidebar.text("No significant KB match found above threshold.")
    return None

# --- Streamed response emulator (ASYNCHRONOUS) ---
async def response_generator(response_text):
    for word in response_text.split():
        yield word + " "
        await asyncio.sleep(0.05)

st.title("GovFocus AI")
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

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Accept user input
if prompt := st.chat_input("Your query:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Determine assistant response based on hierarchy: Greeting -> KB -> Fallback ---
    assistant_response = None

    # 1. Check for user greetings first
    greeting_response = check_for_user_greeting(prompt)
    if greeting_response:
        assistant_response = greeting_response
    else:
        # 2. If no greeting, check knowledge base using processed query
        assistant_response = get_response_from_kb(prompt)

    # 3. If still no response, use fallback
    if not assistant_response:
        assistant_response = "I can not respond to this now. In future iterations, I will be able to provide an answer. I am still a work in progress."

    # Display the chosen assistant response
    with st.chat_message("assistant"):
        response_stream = response_generator(assistant_response)
        response = st.write_stream(response_stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
