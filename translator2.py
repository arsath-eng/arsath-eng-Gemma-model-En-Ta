import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
import json
from typing import List, Dict
import time

# Load environment variables from .env file
load_dotenv()

# Initialize the Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class TranslationManager:
    def __init__(self):
        self.chunk_size = 1500
        self.overlap_size = 200
        self.context_window = []
        
    def chunk_text_with_context(self, text: str) -> List[Dict]:
        """Split text into chunks while maintaining context"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for i, word in enumerate(words):
            current_chunk.append(word)
            current_length += len(word) + 1
            
            # Check if chunk size is reached
            if current_length >= self.chunk_size:
                # Add overlap from next words if available
                overlap_words = words[i+1:i+1+self.overlap_size] if i+1 < len(words) else []
                
                chunks.append({
                    'main_text': ' '.join(current_chunk),
                    'overlap_text': ' '.join(overlap_words),
                    'position': len(chunks)
                })
                
                # Start new chunk with some overlap
                current_chunk = words[max(0, i-50):i+1]
                current_length = sum(len(w) + 1 for w in current_chunk)
        
        # Add remaining text as last chunk
        if current_chunk:
            chunks.append({
                'main_text': ' '.join(current_chunk),
                'overlap_text': '',
                'position': len(chunks)
            })
        
        return chunks

    def create_translation_prompt(self, chunk: Dict, mode: str, domain: str = None) -> str:
        """Create appropriate prompt based on translation mode"""
        if mode == "normal":
            prompt = f"""Translate the following English text to Tamil.
            Provide only the Tamil translation without any other text.
            
            English text: {chunk['main_text']}"""
        else:  # contextual
            context = f"Domain: {domain}\n" if domain else ""
            previous_context = self.context_window[-1] if self.context_window else ""
            
            prompt = f"""Perform a contextual translation from English to Tamil.
            Consider the following aspects:
            {context}
            Previous context: {previous_context}
            
            Maintain the following in your translation:
            - Preserve domain-specific terminology
            - Maintain consistent style and tone
            - Ensure contextual coherence with previous translations
            - Adapt idiomatic expressions appropriately
            
            Text to translate: {chunk['main_text']}
            
            Overlap context: {chunk['overlap_text']}
            
            Provide only the Tamil translation without any explanations."""
        
        return prompt

    def translate_chunk(self, chunk: Dict, mode: str, domain: str = None) -> str:
        """Translate a single chunk of text"""
        prompt = self.create_translation_prompt(chunk, mode, domain)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                completion = client.chat.completions.create(
                    model="Gemma2-9b-It",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3 if mode == "normal" else 0.4,
                    max_tokens=2048,
                    top_p=1,
                    stream=True,
                    stop=None,
                )
                
                translation = ""
                for chunk_response in completion:
                    translation += chunk_response.choices[0].delta.content or ""
                
                # Update context window for contextual translation
                if mode == "contextual":
                    self.context_window.append(translation)
                    if len(self.context_window) > 3:
                        self.context_window.pop(0)
                
                return translation
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)  # Wait before retry
                
        return ""

def main():
    st.set_page_config(page_title="Advanced Tamil Translator", layout="wide")
    
    # Initialize translation manager
    if 'translation_manager' not in st.session_state:
        st.session_state.translation_manager = TranslationManager()
    
    if 'translation_history' not in st.session_state:
        st.session_state.translation_history = []

    st.title("Advanced English to Tamil Translator")
    
    # Translation settings
    with st.expander("Translation Settings", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            translation_mode = st.radio(
                "Translation Mode",
                ["Normal", "Contextual"],
                help="Normal: Direct translation\nContextual: Context-aware translation with domain specificity"
            )
        
        with col2:
            if translation_mode == "Contextual":
                domain = st.selectbox(
                    "Select Domain",
                    ["General", "Technical", "Medical", "Legal", "Literary", "Business", "Academic"],
                    help="Select the domain to improve translation accuracy"
                )
            
    # Input area
    st.subheader("Enter Text")
    english_input = st.text_area("Enter English text of any length:", height=200)
    
    # Translation button
    if st.button("Translate"):
        if not english_input:
            st.error("Please enter some text to translate.")
            return
        
        try:
            # Initialize progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Reset context window for new translation
            st.session_state.translation_manager.context_window = []
            
            # Chunk the input text
            chunks = st.session_state.translation_manager.chunk_text_with_context(english_input)
            translated_chunks = []
            
            # Translate each chunk
            for i, chunk in enumerate(chunks):
                status_text.text(f"Translating part {i+1} of {len(chunks)}...")
                
                translation = st.session_state.translation_manager.translate_chunk(
                    chunk,
                    mode=translation_mode.lower(),
                    domain=domain if translation_mode == "Contextual" else None
                )
                
                translated_chunks.append(translation)
                progress_bar.progress((i + 1) / len(chunks))
            
            # Combine translations
            final_translation = ' '.join(translated_chunks)
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Original Text")
                st.write(english_input)
                st.info(f"Word count: {len(english_input.split())}")
            
            with col2:
                st.subheader("Tamil Translation")
                st.write(final_translation)
                
            # Add to history
            st.session_state.translation_history.append({
                'english': english_input,
                'tamil': final_translation,
                'mode': translation_mode,
                'domain': domain if translation_mode == "Contextual" else "N/A",
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Download options
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "Download Translation",
                    final_translation,
                    file_name=f"tamil_translation_{translation_mode.lower()}.txt",
                    mime="text/plain"
                )
            
            with col2:
                # Export translation with metadata
                export_data = {
                    'original': english_input,
                    'translation': final_translation,
                    'mode': translation_mode,
                    'domain': domain if translation_mode == "Contextual" else "N/A",
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                }
                st.download_button(
                    "Export with Metadata",
                    json.dumps(export_data, indent=2),
                    file_name="translation_with_metadata.json",
                    mime="application/json"
                )
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            
        finally:
            progress_bar.empty()
            status_text.empty()
    
    # Translation History
    if st.session_state.translation_history:
        with st.expander("Translation History"):
            for i, entry in enumerate(reversed(st.session_state.translation_history[-5:])):
                st.write(f"Translation {len(st.session_state.translation_history)-i}")
                st.write(f"Mode: {entry['mode']}")
                if entry['domain'] != "N/A":
                    st.write(f"Domain: {entry['domain']}")
                st.write(f"Timestamp: {entry['timestamp']}")
                st.write("English:", entry['english'][:100] + "..." if len(entry['english']) > 100 else entry['english'])
                st.write("Tamil:", entry['tamil'][:100] + "..." if len(entry['tamil']) > 100 else entry['tamil'])
                st.markdown("---")

if __name__ == "__main__":
    main()