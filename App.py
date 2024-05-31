import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled
import re
from googletrans import Translator, LANGUAGES

# Importing the google module
import google

load_dotenv()  # Load all the environment variables

# Configure the API key for Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

prompt = """You are a YouTube video summarizer. You will be taking the transcript text
and summarizing the entire video and providing the important summary in points
within 250 words. Please provide the summary of the text given here: """

# Function to extract video ID from YouTube URL
def extract_video_id(youtube_video_url):
    video_id = None
    patterns = [
        r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+v=([a-zA-Z0-9_-]{11}).*$',  # Full URL
        r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/([a-zA-Z0-9_-]{11}).*$',  # Short URL
    ]
    for pattern in patterns:
        match = re.match(pattern, youtube_video_url)
        if match:
            video_id = match.groups()[-1]
            break
    return video_id

# Function to get the transcript details from a YouTube video
def extract_transcript_details(youtube_video_url):
    try:
        video_id = extract_video_id(youtube_video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([i["text"] for i in transcript_text])
        return transcript

    except TranscriptsDisabled:
        st.error("Subtitles are disabled for this video.")
        return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        raise e

# Function to generate summary using Google Gemini Pro
def generate_gemini_content(transcript_text, prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt + transcript_text)
    return response.text

# Function to translate text using Google Translate
def translate_text(text, target_language):
    try:
        translator = Translator()
        translation = translator.translate(text, dest=target_language)
        return translation.text
    except Exception as e:
        st.error(f"An error occurred during translation: {e}")
        return None

# Apply custom CSS to style the button
st.markdown(
    """
    <style>
    .small-button {
        display: inline-flex;
        align-items: center;
        margin-top: 1.5rem;
    }
    .small-button button {
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("YouTube Transcript to Detailed Notes Converter")

# Creating form for YouTube link input and button
with st.form(key="youtube_form"):
    youtube_link = st.text_input("Enter YouTube Video Link:")
    target_language = st.selectbox("Select Target Language:", list(LANGUAGES.values()))  # Language selection
    submit_button = st.form_submit_button(label="Press Here to Apply", help="Click to apply the YouTube link")

if submit_button:
    st.session_state['youtube_link'] = youtube_link
    st.session_state['target_language'] = target_language

if 'youtube_link' in st.session_state:
    youtube_link = st.session_state['youtube_link']
    target_language = st.session_state['target_language']
    video_id = extract_video_id(youtube_link)
    
    if video_id:
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

        # Display button to get detailed notes
        if st.button("Get Detailed Notes"):
            try:
                transcript_text = extract_transcript_details(youtube_link)
                if transcript_text:
                    summary = generate_gemini_content(transcript_text, prompt)
                    if summary and target_language != 'en':
                        translated_summary = translate_text(summary, target_language)
                        st.markdown("## Detailed Notes:")
                        st.write(translated_summary)
                    else:
                        st.markdown("## Detailed Notes:")
                        st.write(summary)
            except google.api_core.exceptions.ResourceExhausted:
                st.error("API quota exceeded. Please try again later.")
            except Exception as e:
                st.error(f"An error occurred: {e}") 
