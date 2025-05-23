import streamlit as st
import random
import time
import re
import asyncio
import os

# NLTK Imports for NLP processing
import nltk
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# --- NLTK Data Path Configuration (Crucial for Streamlit Cloud Deployment) ---
# This tells NLTK where to look for data files within the cloned repository.
# Assumes 'nltk_data' folder is in your project's root and is tracked by Git.
nltk_data_path = os.path.join(os.getcwd(), "nltk_data") # This will point to /mount/src/gf/nltk_data on Streamlit Cloud
if nltk_data_path not in nltk.data.path:
    nltk.data.path.append(nltk_data_path)

# ... rest of your imports and code ...

# --- Initialize NLTK tools ---
lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer() # Ensure this is PorterStemmer(), not PorterNetStemmer()
STOPWORDS = set(stopwords.words('english'))


# --- Helper functions for NLP processing ---
def preprocess_text_for_matching(text, use_stemming=False):
    """
    Tokenizes, converts to lowercase, removes stopwords, and then either
    lemmatizes or stems the text. Returns a space-separated string of processed words.
    This format is required by TfidfVectorizer.
    """
    tokens = word_tokenize(text.lower())
    processed_tokens = []
    for token in tokens:
        if token.isalpha() and token not in STOPWORDS:
            if use_stemming:
                processed_tokens.append(stemmer.stem(token))
            else:
                processed_tokens.append(lemmatizer.lemmatize(token))
    return " ".join(processed_tokens) # Return as a single string for TfidfVectorizer


# --- 1. Define Initial Greetings ---
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

vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split(), lowercase=False)

# --- Define the Knowledge Base (Replace with your actual data) ---
RAW_KNOWLEDGE_BASE = {
    "What is the capital of Nigeria?": "The capital of Nigeria is Abuja.",
    "Who is the president of Nigeria?": "As of 2024, the president of Nigeria is Bola Ahmed Tinubu.",
    "What is the population of Nigeria?": "Nigeria has an estimated population of over 200 million people.",
    # Add more question-answer pairs as needed
}

processed_kb_keys_list = [
    preprocess_text_for_matching(key, use_stemming=False)
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
    processed_user_query_str = preprocess_text_for_matching(query, use_stemming=False)

    # Debugging: Show raw and processed user query (uncomment if needed)
    # st.sidebar.text(f"User Query (Raw): {query}")
    # st.sidebar.text(f"User Query (Processed Str): '{processed_user_query_str}'")

    if not processed_user_query_str.strip():
        # st.sidebar.text("No meaningful words in processed user query.")
        return None

    user_query_vector = vectorizer.transform([processed_user_query_str])

    similari = cosine_similarity(user_query_vector, kb_vectors)

    best_match_index = similari.argmax()
    highest_similarity_score = similari[0, best_match_index]

    # Debugging: Show similarity scores (uncomment if needed)
    # st.sidebar.text(f"All Similarities: {similari[0]}")
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