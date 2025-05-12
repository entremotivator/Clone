import streamlit as st
import requests
import json
import time
import base64
import pandas as pd
import os
from datetime import datetime
from PIL import Image
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="Pipio AI Avatar Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if "videos" not in st.session_state:
    st.session_state.videos = []
if "selected_avatar" not in st.session_state:
    st.session_state.selected_avatar = None
if "selected_voice" not in st.session_state:
    st.session_state.selected_voice = None
if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar for API key and settings
with st.sidebar:
    st.image("https://placeholder.svg?height=100&width=200&query=Pipio+AI+Logo", width=200)
    st.title("Settings")
    
    # API key input in sidebar
    api_key = st.text_input("Enter your Pipio AI API Key", type="password")
    st.caption("Your API key is securely stored in the session and not saved permanently.")
    
    # Advanced settings
    with st.expander("Advanced Settings"):
        cache_ttl = st.slider("Cache TTL (minutes)", 5, 60, 10)
        auto_refresh = st.checkbox("Auto-refresh video status", value=True)
        refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 15)
        show_debug = st.checkbox("Show debug information", value=False)
    
    # About section
    with st.expander("About"):
        st.markdown("""
        # About Pipio AI
        This app uses the Pipio AI API to generate avatar videos with realistic voices.
        
        - [Pipio AI Website](https://pipio.ai)
        - [API Documentation](https://docs.pipio.ai)
        """)

# Main app title
st.title("🎬 Pipio AI Avatar Video Generator")
st.markdown("Generate professional avatar videos using Pipio AI's advanced API")

# Check for API key
if not api_key:
    st.warning("⚠️ Please enter your API key in the sidebar to continue")
    
    # Show demo section
    st.subheader("How it works")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 1. Select Avatar")
        st.image("https://placeholder.svg?height=150&width=150&query=Select+Avatar", width=150)
        st.markdown("Choose from a variety of realistic avatars")
    with col2:
        st.markdown("### 2. Choose Voice")
        st.image("https://placeholder.svg?height=150&width=150&query=Select+Voice", width=150)
        st.markdown("Pick the perfect voice for your message")
    with col3:
        st.markdown("### 3. Generate Video")
        st.image("https://placeholder.svg?height=150&width=150&query=Generate+Video", width=150)
        st.markdown("Create professional videos in minutes")
    
    st.stop()

# Set headers for API requests
headers = {
    "Accept": "application/json",
    "Authorization": f"Key {api_key}"
}

# Function to fetch avatars with caching
@st.cache_data(ttl=600)
def get_avatars(api_key):
    try:
        response = requests.get(
            "https://avatar.pipio.ai/actor",
            headers={"Authorization": f"Key {api_key}", "Accept": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching avatars: {str(e)}")
        return []

# Function to fetch voices with caching
@st.cache_data(ttl=600)
def get_voices(api_key):
    try:
        response = requests.get(
            "https://avatar.pipio.ai/voice",
            headers={"Authorization": f"Key {api_key}", "Accept": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching voices: {str(e)}")
        return []

# Function to generate video
def generate_video(actor_id, voice_id, script, api_key, additional_params=None):
    try:
        payload = {
            "actorId": actor_id,
            "voiceId": voice_id,
            "script": script
        }
        
        # Add any additional parameters
        if additional_params and isinstance(additional_params, dict):
            payload.update(additional_params)
        
        response = requests.post(
            "https://generate.pipio.ai/single-clip",
            headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating video: {str(e)}")
        if show_debug and hasattr(e, 'response') and e.response:
            st.error(f"Response: {e.response.text}")
        return None

# Function to check video status
def check_video_status(video_id, api_key):
    try:
        response = requests.get(
            f"https://generate.pipio.ai/single-clip/{video_id}",
            headers={"Authorization": f"Key {api_key}", "Accept": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error checking video status: {str(e)}")
        return None

# Function to download video
def download_video(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"Error downloading video: {str(e)}")
        return None

# Function to add to history
def add_to_history(action, details):
    st.session_state.history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details
    })

# Load avatars and voices
with st.spinner("Loading avatars and voices..."):
    avatars = get_avatars(api_key)
    voices = get_voices(api_key)

if not avatars or not voices:
    st.error("Failed to load avatars or voices. Please check your API key and try again.")
    st.stop()

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Select Avatar & Voice", "Generate Video", "Your Videos", "History & Analytics"])

with tab1:
    st.header("Available Avatars")
    
    # Create dictionaries for easy lookup
    avatar_dict = {avatar.get("id"): avatar for avatar in avatars}
    avatar_names = {avatar.get("name", f"Unknown-{avatar.get('id')}"): avatar.get("id") for avatar in avatars}
    
    # Display avatars in a grid with selection
    avatar_cols = st.columns(4)
    
    for i, avatar in enumerate(avatars):
        with avatar_cols[i % 4]:
            avatar_id = avatar.get("id")
            avatar_name = avatar.get("name", "Unknown")
            avatar_image = avatar.get("previewImageUrl")
            
            # Create a container for each avatar
            with st.container():
                st.subheader(avatar_name)
                if avatar_image:
                    st.image(avatar_image, width=150)
                else:
                    st.image("https://placeholder.svg?height=150&width=150&query=No+Preview", width=150)
                
                # Selection button
                if st.button(f"Select {avatar_name}", key=f"select_avatar_{i}"):
                    st.session_state.selected_avatar = avatar_id
                    add_to_history("Selected Avatar", avatar_name)
                    st.success(f"Selected avatar: {avatar_name}")
    
    st.header("Available Voices")
    
    # Create voice dictionaries
    voice_dict = {voice.get("id"): voice for voice in voices}
    voice_names = {f"{voice.get('name', 'Unknown')} ({voice.get('gender', 'Not specified')}, {voice.get('language', 'Not specified')})": voice.get("id") for voice in voices}
    
    # Create a dataframe for better display
    voice_data = []
    for voice in voices:
        voice_id = voice.get("id")
        voice_name = voice.get("name", "Unknown")
        voice_gender = voice.get("gender", "Not specified")
        voice_language = voice.get("language", "Not specified")
        voice_accent = voice.get("accent", "Not specified")
        
        voice_data.append({
            "Name": voice_name,
            "Gender": voice_gender,
            "Language": voice_language,
            "Accent": voice_accent,
            "ID": voice_id
        })
    
    # Convert to dataframe
    df = pd.DataFrame(voice_data)
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        gender_filter = st.multiselect("Filter by Gender", options=df["Gender"].unique(), default=[])
    with col2:
        language_filter = st.multiselect("Filter by Language", options=df["Language"].unique(), default=[])
    with col3:
        accent_filter = st.multiselect("Filter by Accent", options=df["Accent"].unique(), default=[])
    
    # Apply filters
    filtered_df = df
    if gender_filter:
        filtered_df = filtered_df[filtered_df["Gender"].isin(gender_filter)]
    if language_filter:
        filtered_df = filtered_df[filtered_df["Language"].isin(language_filter)]
    if accent_filter:
        filtered_df = filtered_df[filtered_df["Accent"].isin(accent_filter)]
    
    # Display filtered dataframe
    st.dataframe(filtered_df, use_container_width=True)
    
    # Voice selection
    selected_voice_name = st.selectbox("Select Voice", options=list(voice_names.keys()))
    if st.button("Confirm Voice Selection"):
        st.session_state.selected_voice = voice_names[selected_voice_name]
        add_to_history("Selected Voice", selected_voice_name)
        st.success(f"Selected voice: {selected_voice_name}")

with tab2:
    st.header("Generate Avatar Video")
    
    # Show current selections
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Selected Avatar")
        if st.session_state.selected_avatar:
            avatar = avatar_dict.get(st.session_state.selected_avatar)
            if avatar:
                st.write(f"**Name:** {avatar.get('name', 'Unknown')}")
                if avatar.get("previewImageUrl"):
                    st.image(avatar.get("previewImageUrl"), width=200)
                st.write(f"**ID:** {st.session_state.selected_avatar}")
        else:
            st.warning("No avatar selected. Please go to the 'Select Avatar & Voice' tab.")
    
    with col2:
        st.subheader("Selected Voice")
        if st.session_state.selected_voice:
            voice = voice_dict.get(st.session_state.selected_voice)
            if voice:
                st.write(f"**Name:** {voice.get('name', 'Unknown')}")
                st.write(f"**Gender:** {voice.get('gender', 'Not specified')}")
                st.write(f"**Language:** {voice.get('language', 'Not specified')}")
                st.write(f"**Accent:** {voice.get('accent', 'Not specified')}")
                st.write(f"**ID:** {st.session_state.selected_voice}")
        else:
            st.warning("No voice selected. Please go to the 'Select Avatar & Voice' tab.")
    
    # Script input
    st.subheader("Enter Your Script")
    
    # Script templates
    script_templates = {
        "Introduction": "Hello, my name is [Name] and I'm excited to tell you about [Topic].",
        "Product Demo": "Today I'll be demonstrating our new product, [Product Name]. This innovative solution helps you [Benefit].",
        "Tutorial": "In this tutorial, I'll show you how to [Task]. This is a simple process that will help you [Benefit].",
        "Announcement": "I'm pleased to announce that [Announcement]. This is exciting news because [Reason].",
        "Custom": ""
    }
    
    template_choice = st.selectbox("Choose a template or create custom script", options=list(script_templates.keys()))
    
    if template_choice != "Custom":
        script_template = script_templates[template_choice]
    else:
        script_template = ""
    
    script = st.text_area("Script (max 5000 characters)", 
                         script_template, 
                         max_chars=5000,
                         height=200)
    
    # Character count
    st.caption(f"Character count: {len(script)}/5000")
    
    # Advanced options
    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)
        with col1:
            video_format = st.selectbox("Video Format", ["mp4", "webm"], index=0)
            resolution = st.selectbox("Resolution", ["720p", "1080p"], index=0)
        with col2:
            background_color = st.color_picker("Background Color", "#FFFFFF")
            speed_factor = st.slider("Speech Speed", 0.5, 1.5, 1.0, 0.1)
    
    # Additional parameters
    additional_params = {
        "format": video_format,
        "resolution": resolution,
        "backgroundColor": background_color,
        "speedFactor": speed_factor
    }
    
    # Generate button
    if st.button("Generate Video", type="primary", use_container_width=True):
        if not st.session_state.selected_avatar or not st.session_state.selected_voice:
            st.error("Please select both an avatar and a voice before generating a video.")
        elif not script:
            st.error("Please enter a script.")
        else:
            with st.spinner("Generating video..."):
                avatar_id = st.session_state.selected_avatar
                voice_id = st.session_state.selected_voice
                
                # Generate video
                result = generate_video(avatar_id, voice_id, script, api_key, additional_params)
                
                if result and "id" in result:
                    video_id = result["id"]
                    st.success(f"Video generation started! Video ID: {video_id}")
                    
                    # Get avatar and voice names for display
                    avatar_name = avatar_dict.get(avatar_id, {}).get("name", "Unknown Avatar")
                    voice_name = voice_dict.get(voice_id, {}).get("name", "Unknown Voice")
                    
                    # Save video ID to session state for tracking
                    st.session_state.videos.append({
                        "id": video_id,
                        "avatar_id": avatar_id,
                        "avatar_name": avatar_name,
                        "voice_id": voice_id,
                        "voice_name": voice_name,
                        "script": script,
                        "status": "processing",
                        "url": None,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "additional_params": additional_params
                    })
                    
                    add_to_history("Generated Video", f"ID: {video_id}, Avatar: {avatar_name}, Voice: {voice_name}")
                    
                    st.info("Your video is being processed. Go to the 'Your Videos' tab to check status.")
                else:
                    st.error("Failed to generate video. Please try again.")

with tab3:
    st.header("Your Videos")
    
    if not st.session_state.videos:
        st.info("No videos generated yet. Go to the 'Generate Video' tab to create one.")
    else:
        # Refresh button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"You have {len(st.session_state.videos)} videos")
        with col2:
            if st.button("Refresh All Statuses", use_container_width=True):
                st.success("Refreshing video statuses...")
        
        # Filter options
        status_filter = st.multiselect(
            "Filter by Status",
            options=["processing", "completed", "failed"],
            default=[]
        )
        
        # Apply filters
        filtered_videos = st.session_state.videos
        if status_filter:
            filtered_videos = [v for v in filtered_videos if v["status"] in status_filter]
        
        # Display videos
        for i, video in enumerate(filtered_videos):
            with st.expander(f"Video {i+1}: {video['avatar_name']} with {video['voice_name']} - {video['status'].upper()} - {video['created_at']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Created:** {video['created_at']}")
                    st.markdown(f"**Avatar:** {video['avatar_name']} (ID: {video['avatar_id']})")
                    st.markdown(f"**Voice:** {video['voice_name']} (ID: {video['voice_id']})")
                    st.markdown(f"**Status:** {video['status'].upper()}")
                    st.markdown(f"**Video ID:** {video['id']}")
                    
                    # Script preview
                    with st.expander("View Script"):
                        st.write(video['script'])
                
                with col2:
                    # Check status button
                    if st.button(f"Check Status", key=f"check_status_{i}"):
                        with st.spinner("Checking status..."):
                            status_data = check_video_status(video['id'], api_key)
                            
                            if status_data:
                                current_status = status_data.get("status", "unknown")
                                st.session_state.videos[i]["status"] = current_status
                                
                                if current_status == "completed":
                                    video_url = status_data.get("videoUrl")
                                    st.session_state.videos[i]["url"] = video_url
                                    st.success(f"Status updated: {current_status}")
                                    add_to_history("Video Completed", f"ID: {video['id']}")
                                elif current_status == "processing":
                                    st.info(f"Status updated: {current_status}")
                                elif current_status == "failed":
                                    st.error(f"Status updated: {current_status}")
                                    add_to_history("Video Failed", f"ID: {video['id']}")
                                else:
                                    st.warning(f"Unknown status: {current_status}")
                            else:
                                st.error("Failed to check video status")
                
                # Video preview and download
                if video['status'] == "completed" and video['url']:
                    st.video(video['url'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        # Download button
                        video_content = download_video(video['url'])
                        if video_content:
                            b64_video = base64.b64encode(video_content).decode()
                            download_filename = f"pipio_video_{video['id']}.mp4"
                            href = f'<a href="data:video/mp4;base64,{b64_video}" download="{download_filename}" class="button">Download Video</a>'
                            st.markdown(href, unsafe_allow_html=True)
                    
                    with col2:
                        # Copy video URL button
                        st.text_input("Video URL", video['url'], key=f"url_{i}")
                
                elif video['status'] == "processing":
                    st.info("Video is still processing. Please check back later or click 'Check Status'.")
                    
                    # Progress animation
                    progress_placeholder = st.empty()
                    progress_bar = progress_placeholder.progress(0)
                    for percent_complete in range(100):
                        time.sleep(0.05)
                        progress_bar.progress(percent_complete + 1)
                    progress_placeholder.empty()
                    
                    st.info("Note: This progress bar is an animation and does not reflect actual processing time.")
                
                elif video['status'] == "failed":
                    st.error("Video generation failed. Please try again with different parameters.")
                
                # Delete video from list
                if st.button(f"Remove from List", key=f"delete_{i}"):
                    if st.session_state.videos[i]["status"] == "completed":
                        add_to_history("Removed Video", f"ID: {video['id']}, Status: Completed")
                    else:
                        add_to_history("Removed Video", f"ID: {video['id']}, Status: {video['status']}")
                    
                    st.session_state.videos.pop(i)
                    st.success("Video removed from list")
                    st.rerun()

with tab4:
    st.header("History & Analytics")
    
    # Display history
    if not st.session_state.history:
        st.info("No history available yet. Generate some videos to see your activity.")
    else:
        # Convert history to dataframe
        history_df = pd.DataFrame(st.session_state.history)
        
        # Display history table
        st.subheader("Activity History")
        st.dataframe(history_df, use_container_width=True)
        
        # Analytics
        st.subheader("Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_videos = len([v for v in st.session_state.videos if v["status"] == "completed"])
            st.metric("Completed Videos", total_videos)
        
        with col2:
            processing_videos = len([v for v in st.session_state.videos if v["status"] == "processing"])
            st.metric("Processing Videos", processing_videos)
        
        with col3:
            failed_videos = len([v for v in st.session_state.videos if v["status"] == "failed"])
            st.metric("Failed Videos", failed_videos)
        
        # Action counts
        if len(history_df) > 0:
            action_counts = history_df["action"].value_counts().reset_index()
            action_counts.columns = ["Action", "Count"]
            
            st.subheader("Action Breakdown")
            st.bar_chart(action_counts, x="Action", y="Count")
        
        # Export history
        if st.button("Export History to CSV"):
            csv = history_df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="pipio_history.csv">Download CSV File</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.success("History exported to CSV")
        
        # Clear history
        if st.button("Clear History"):
            st.session_state.history = []
            st.success("History cleared")
            st.rerun()

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### Pipio AI Avatar Generator")
    st.markdown("Version 2.0")
with col2:
    st.markdown("### Powered by")
    st.markdown("[Pipio AI API](https://pipio.ai)")
with col3:
    st.markdown("### Need Help?")
    st.markdown("[Documentation](https://docs.pipio.ai) | [Support](mailto:support@pipio.ai)")
