# Import necessary libraries
import os
import openai
import streamlit as st
from langchain_google_community import GoogleSearchAPIWrapper

# Set up API keys
os.environ["OPENAI_API_KEY"] = "your_openai_api_key_here"
os.environ["GOOGLE_API_KEY"] = "your_google_api_key_here"
os.environ["GOOGLE_CSE_ID"] = "your_cse_id_here"

# Initialize OpenAI and Google Search clients
openai.api_key = os.getenv("OPENAI_API_KEY")
search = GoogleSearchAPIWrapper()

# Function to fetch information using Google Search
def fetch_information_from_url(query):
    try:
        results = search.results(query, 5)
        search_results = [(result['link'], result['snippet']) for result in results]
        return search_results
    except Exception as e:
        st.write(f"HTTP error occurred: {e}")
        return []

# Function to check if the query is a greeting
def is_greeting(query):
    messages = [
        {"role": "system", "content": "Determine if the following text is a greeting. Respond with 'yes' or 'no'."},
        {"role": "user", "content": query}
    ]
    
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=5
    )
    
    return response.choices[0].message.content.strip().lower() == "yes"

# Function to check if the query is related to CGU
def is_related_to_cgu(query, conversation_history):
    messages = [
        {"role": "system", "content": "Determine if the following conversation, considering the history and current message, is talking about Claremont Graduate University (CGU) or if it is getting too general. Respond with 'cgu' or 'general'."},
        {"role": "user", "content": f"Conversation history: {conversation_history}\nCurrent message: {query}"}
    ]
    
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=5
    )
    
    return response.choices[0].message.content.strip().lower() == "cgu"

# Function to process incoming queries
def process_query(query, conversation_history):
    if is_greeting(query) and len(query.split()) <= 3:
        return "greeting"
    
    if not is_related_to_cgu(query, conversation_history):
        return "not_related"
    
    return query

# Function to generate response using the language model
def generate_response(query, conversation_history):
    if query == "greeting":
        messages = [
            {"role": "system", "content": "Generate a friendly greeting response."},
            {"role": "user", "content": ""}
        ]
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            max_tokens=150  # Increase token limit for greeting responses
        )
        return response.choices[0].message.content.strip()
    
    if query == "not_related":
        messages = [
            {"role": "system", "content": "Respond to the user by stating that you can only answer questions related to Claremont Graduate University. Provide some example queries related to CGU."},
            {"role": "user", "content": ""}
        ]
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            max_tokens=150  # Increase token limit for non-related responses
        )
        return response.choices[0].message.content.strip()
    
    # Fetch information using Google Search
    search_results = fetch_information_from_url(query)
    
    # Use the language model to generate a response using the search results
    combined_search_results = "\n".join([f"{url}: {content}" for url, content in search_results])
    messages = [
        {"role": "system", "content": "Answer the following question using the information provided, include relevant links and detailed steps where applicable."},
        {"role": "user", "content": f"Question: {query}\n\nInformation:\n{combined_search_results}"}
    ]
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=800  # Drastically increase token limit for detailed responses
    )
    
    return response.choices[0].message.content.strip()

# Main function to handle incoming messages
def handle_message(message, conversation_history):
    # Process the incoming message/query
    processed_query = process_query(message, conversation_history)
    
    # Generate a response for the processed query
    response = generate_response(processed_query, conversation_history)
    
    # Update conversation history
    conversation_history += f"User: {message}\nAssistant: {response}\n"
    
    # Return the generated response and updated conversation history
    return response, conversation_history

# Set up the chatbot using Streamlit for basic display and testing
if __name__ == "__main__":
    # Streamlit UI setup
    st.title("Claremont Graduate University Chatbot")
    user_input = st.text_input("Ask a question about Claremont Graduate University:")
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = ""

    if user_input:
        response, st.session_state.conversation_history = handle_message(user_input, st.session_state.conversation_history)
        st.write("Response:", response)
