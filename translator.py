import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# Initialize the Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define a function to interact with the Groq model and get translation
def translate_to_tamil(english_text):
    # Create a prompt that specifically asks for Tamil translation
    prompt = f"""Translate the following English text to Tamil. 
    Provide only the Tamil translation without any other text.
    
    English text: {english_text}"""
    
    completion = client.chat.completions.create(
        model="Gemma2-9b-It",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,  # Lower temperature for more consistent translations
        max_tokens=2048,
        top_p=1,
        stream=True,
        stop=None,
    )
    
    # Collect the response text from the API stream
    translation = ""
    for chunk in completion:
        translation += chunk.choices[0].delta.content or ""
    
    return translation

# Streamlit app layout
st.title("English to Tamil Translator")
st.write("Enter English text below to get its Tamil translation.")

# Input text area for better multi-line support
english_input = st.text_area("Enter English text:", height=100)

# Add a translate button
if st.button("Translate to Tamil"):
    if english_input:
        with st.spinner('Translating...'):
            try:
                tamil_translation = translate_to_tamil(english_input)
                
                # Create two columns for side-by-side display
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("English Text:")
                    st.write(english_input)
                
                with col2:
                    st.subheader("Tamil Translation:")
                    st.write(tamil_translation)
                
                # Add a copy button for the Tamil translation
                st.button("Copy Translation", 
                         on_click=lambda: st.write(f"Translation copied to clipboard: {tamil_translation}"))
                
            except Exception as e:
                st.error(f"An error occurred during translation: {str(e)}")
    else:
        st.error("Please enter some text to translate.")

# Add footer with usage instructions
st.markdown("---")
st.markdown("""
### Usage Tips:
- Enter your English text in the text area above
- Click 'Translate to Tamil' to get the translation
- Use the copy button to copy the translation
- For best results, use clear and simple English sentences
""")