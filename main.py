import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# Initialize the Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define a function to interact with the Groq model and get a response
def get_groq_response(user_input):
    completion = client.chat.completions.create(
        model="llama3-8b-8192",  # Model version
        messages=[
            {
                "role": "user",
                "content": user_input
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )
    
    # Collect the response text from the API stream
    response_text = ""
    for chunk in completion:
        response_text += chunk.choices[0].delta.content or ""
    
    return response_text

# Streamlit app layout
st.title("Llama 3.2 Chatbot")

st.write("This app interacts with the Llama 3.2 model to generate responses.")

# Input text box
user_input = st.text_input("Enter your message:")

# When the user clicks the button, get the Groq response
if st.button("Generate Response"):
    if user_input:
        with st.spinner('Generating response...'):
            response = get_groq_response(user_input)
            st.write(response)
    else:
        st.error("Please enter a message.")
