import streamlit as st
import requests
import json
import time
import base64
import pandas as pd
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
        show_debug = st.checkbox("Show debug information", value=True)  # Set to True by default for now
    
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

# Function to extract data from API response
def extract_data_from_response(response, api_name="API"):
    """Extract data from API response, handling different possible formats"""
    if isinstance(response, list):
        return response
    elif isinstance(response, dict):
        # Check common JSON response patterns
        if "data" in response:
            return response["data"]
        elif "results" in response:
            return response["results"]
        elif "items" in response:
            return response["items"]
        elif "response" in response:
            return extract_data_from_response(response["response"], api_name)
        elif "actors" in response and api_name.lower() == "avatar":
            return response["actors"]
        elif "voices" in response and api_name.lower() == "voice":
            return response["voices"]
        # Special case for Pipio API - check if the dictionary contains items that look like avatars/voices
        elif all(key in response for key in ["id", "name"]):
            return [response]  # It's a single item, wrap in list
        else:
            # If we can find any array in the response with typical fields, use that
            for key, value in response.items():
                if isinstance(value, list) and len(value) > 0:
                    if isinstance(value[0], dict) and "id" in value[0]:
                        return value
            # Last resort: just return the dictionary keys as items
            if show_debug:
                st.write(f"Could not find a list in response, keys found: {list(response.keys())}")
            return []
    return []

# Function to safely get value from dictionary
def safe_get(dictionary, key, default=None):
    """Safely get a value from a dictionary"""
    if dictionary is None:
        return default
    if not isinstance(dictionary, dict):
        return default
    return dictionary.get(key, default)

# Function to fetch avatars with caching
@st.cache_data(ttl=600)
def get_avatars(api_key):
    try:
        response = requests.get(
            "https://avatar.pipio.ai/actor",
            headers={"Authorization": f"Key {api_key}", "Accept": "application/json"}
        )
        response.raise_for_status()
        
        # Get raw response
        raw_response = response.json()
        
        # Debug output for the raw API response
        if show_debug:
            st.write("Raw Avatar API Response:", raw_response)
            st.write("Avatar Response Type:", type(raw_response))
            if isinstance(raw_response, dict):
                st.write("Avatar Response Keys:", list(raw_response.keys()))
        
        # Extract the actual data from the response
        data = extract_data_from_response(raw_response, "avatar")
        
        # Additional debug info about extracted data
        if show_debug:
            st.write("Extracted Avatar Data Type:", type(data))
            st.write("Extracted Avatar Data Length:", len(data) if isinstance(data, list) else "N/A")
            if isinstance(data, list) and len(data) > 0:
                st.write("Sample Avatar Item:", data[0])
        
        # If we couldn't extract a list, try to directly use the raw response
        if not isinstance(data, list):
            st.warning(f"Avatar API returned unexpected format, attempting to use raw response")
            # Create a simple list with the raw response as an item if it has an ID
            if isinstance(raw_response, dict) and "id" in raw_response:
                return [raw_response]
            else:
                # Mock data for testing if API doesn't work
                st.error("Using mock avatar data for testing purposes")
                return [
                    {"id": "avatar1", "name": "Test Avatar 1", "previewImageUrl": "https://placeholder.svg?height=150&width=150&query=Avatar+1"},
                    {"id": "avatar2", "name": "Test Avatar 2", "previewImageUrl": "https://placeholder.svg?height=150&width=150&query=Avatar+2"}
                ]
        
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching avatars: {str(e)}")
        if show_debug and hasattr(e, 'response') and e.response:
            try:
                st.error(f"Response status code: {e.response.status_code}")
                st.error(f"Response: {e.response.text}")
            except:
                st.error("Could not parse error response")
        return []
    except json.JSONDecodeError as e:
        st.error(f"Error decoding avatar JSON: {str(e)}")
        if show_debug:
            st.write("Raw response:", response.text[:500] + "..." if len(response.text) > 500 else response.text)
        return []
    except Exception as e:
        st.error(f"Unexpected error fetching avatars: {str(e)}")
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
        
        # Get raw response
        raw_response = response.json()
        
        # Debug output for the raw API response
        if show_debug:
            st.write("Raw Voice API Response:", raw_response)
            st.write("Voice Response Type:", type(raw_response))
            if isinstance(raw_response, dict):
                st.write("Voice Response Keys:", list(raw_response.keys()))
        
        # Extract the actual data from the response
        data = extract_data_from_response(raw_response, "voice")
        
        # Additional debug info about extracted data
        if show_debug:
            st.write("Extracted Voice Data Type:", type(data))
            st.write("Extracted Voice Data Length:", len(data) if isinstance(data, list) else "N/A")
            if isinstance(data, list) and len(data) > 0:
                st.write("Sample Voice Item:", data[0])
        
        # If we couldn't extract a list, try to directly use the raw response
        if not isinstance(data, list):
            st.warning(f"Voice API returned unexpected format, attempting to use raw response")
            # Create a simple list with the raw response as an item if it has an ID
            if isinstance(raw_response, dict) and "id" in raw_response:
                return [raw_response]
            else:
                # Mock data for testing if API doesn't work
                st.error("Using mock voice data for testing purposes")
                return [
                    {"id": "voice1", "name": "Test Voice 1", "gender": "Male", "language": "English", "accent": "American"},
                    {"id": "voice2", "name": "Test Voice 2", "gender": "Female", "language": "English", "accent": "British"}
                ]
        
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching voices: {str(e)}")
        if show_debug and hasattr(e, 'response') and e.response:
            try:
                st.error(f"Response status code: {e.response.status_code}")
                st.error(f"Response: {e.response.text}")
            except:
                st.error("Could not parse error response")
        return []
    except json.JSONDecodeError as e:
        st.error(f"Error decoding voice JSON: {str(e)}")
        if show_debug:
            st.write("Raw response:", response.text[:500] + "..." if len(response.text) > 500 else response.text)
        return []
    except Exception as e:
        st.error(f"Unexpected error fetching voices: {str(e)}")
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
        
        # Debug output
        if show_debug:
            st.write("Generate Video Payload:", payload)
        
        response = requests.post(
            "https://generate.pipio.ai/single-clip",
            headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        response.raise_for_status()
        response_data = response.json()
        
        # Debug output for response
        if show_debug:
            st.write("Generate Video Response:", response_data)
        
        return response_data
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating video: {str(e)}")
        if show_debug and hasattr(e, 'response') and e.response:
            try:
                st.error(f"Response status code: {e.response.status_code}")
                st.error(f"Response: {e.response.text}")
            except:
                st.error("Could not parse error response")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Error decoding generation JSON: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error generating video: {str(e)}")
        return None

# Function to check video status
def check_video_status(video_id, api_key):
    try:
        response = requests.get(
            f"https://generate.pipio.ai/single-clip/{video_id}",
            headers={"Authorization": f"Key {api_key}", "Accept": "application/json"}
        )
        response.raise_for_status()
        response_data = response.json()
        
        # Debug output for response
        if show_debug:
            st.write("Video Status Response:", response_data)
        
        return response_data
    except requests.exceptions.RequestException as e:
        st.error(f"Error checking video status: {str(e)}")
        if show_debug and hasattr(e, 'response') and e.response:
            try:
                st.error(f"Response status code: {e.response.status_code}")
                st.error(f"Response: {e.response.text}")
            except:
                st.error("Could not parse error response")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Error decoding status JSON: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error checking status: {str(e)}")
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
    except Exception as e:
        st.error(f"Unexpected error downloading video: {str(e)}")
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

# Check if we got valid data
if show_debug:
    st.write(f"Avatars type: {type(avatars)}, length: {len(avatars) if isinstance(avatars, list) else 'N/A'}")
    st.write(f"Voices type: {type(voices)}, length: {len(voices) if isinstance(voices, list) else 'N/A'}")

# Verify we have valid lists - treat empty lists as failed too
if not isinstance(avatars, list) or not isinstance(voices, list) or len(avatars) == 0 or len(voices) == 0:
    st.error("Failed to load avatars or voices. Please check your API key and try again.")
    # Provide more specific error messages
    if not isinstance(avatars, list):
        st.error(f"Avatar data is not a list: {type(avatars)}")
    elif len(avatars) == 0:
        st.error("No avatars found in the response")
    if not isinstance(voices, list):
        st.error(f"Voice data is not a list: {type(voices)}")
    elif len(voices) == 0:
        st.error("No voices found in the response")
    
    # Show some alternative options
    st.info("You can try the following:")
    st.info("1. Check that your API key is correct")
    st.info("2. Ensure you have access to the Pipio AI API")
    st.info("3. Try again later as the API may be temporarily unavailable")
    
    if show_debug:
        st.subheader("Debug Information")
        st.write("API key length:", len(api_key) if api_key else "No API key provided")
        if isinstance(avatars, list):
            st.write("Avatar sample:", avatars[:1])
        else:
            st.write("Avatars:", avatars)
        if isinstance(voices, list):
            st.write("Voice sample:", voices[:1])
        else:
            st.write("Voices:", voices)
    
    st.stop()

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Select Avatar & Voice", "Generate Video", "Your Videos", "History & Analytics"])

with tab1:
    st.header("Available Avatars")
    
    # Create dictionaries for easy lookup - with safe access
    avatar_dict = {}
    avatar_names = {}
    
    for avatar in avatars:
        if isinstance(avatar, dict):
            avatar_id = safe_get(avatar, "id")
            if avatar_id:
                avatar_dict[avatar_id] = avatar
                avatar_name = safe_get(avatar, "name", f"Unknown-{avatar_id}")
                avatar_names[avatar_name] = avatar_id
    
    # Display avatars in a grid with selection
    if not avatar_dict:
        st.warning("No valid avatars found. Please check your API key or try again later.")
    else:
        avatar_cols = st.columns(4)
        
        for i, (avatar_name, avatar_id) in enumerate(avatar_names.items()):
            avatar = avatar_dict[avatar_id]
            with avatar_cols[i % 4]:
                # Create a container for each avatar
                with st.container():
                    st.subheader(avatar_name)
                    avatar_image = safe_get(avatar, "previewImageUrl")
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
    
    # Create voice dictionaries - with safe access
    voice_dict = {}
    voice_names = {}
    
    for voice in voices:
        if isinstance(voice, dict):
            voice_id = safe_get(voice, "id")
            if voice_id:
                voice_dict[voice_id] = voice
                voice_name = safe_get(voice, "name", "Unknown")
                voice_gender = safe_get(voice, "gender", "Not specified")
                voice_language = safe_get(voice, "language", "Not specified")
                display_name = f"{voice_name} ({voice_gender}, {voice_language})"
                voice_names[display_name] = voice_id
    
    # Create a dataframe for better display
    if not voice_dict:
        st.warning("No valid voices found. Please check your API key or try again later.")
    else:
        voice_data = []
        for voice_id, voice in voice_dict.items():
            voice_data.append({
                "Name": safe_get(voice, "name", "Unknown"),
                "Gender": safe_get(voice, "gender", "Not specified"),
                "Language": safe_get(voice, "language", "Not specified"),
                "Accent": safe_get(voice, "accent", "Not specified"),
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
        if voice_names:
            selected_voice_name = st.selectbox("Select Voice", options=list(voice_names.keys()))
            if st.button("Confirm Voice Selection"):
                st.session_state.selected_voice = voice_names[selected_voice_name]
                add_to_history("Selected Voice", selected_voice_name)
                st.success(f"Selected voice: {selected_voice_name}")
        else:
            st.warning("No voices available for selection.")

with tab2:
    st.header("Generate Avatar Video")
    
    # Show current selections
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Selected Avatar")
        if st.session_state.selected_avatar and st.session_state.selected_avatar in avatar_dict:
            avatar = avatar_dict.get(st.session_state.selected_avatar)
            if avatar:
                st.write(f"**Name:** {safe_get(avatar, 'name', 'Unknown')}")
                avatar_image = safe_get(avatar, "previewImageUrl")
                if avatar_image:
                    st.image(avatar_image, width=200)
                st.write(f"**ID:** {st.session_state.selected_avatar}")
        else:
            st.warning("No avatar selected. Please go to the 'Select Avatar & Voice' tab.")
    
    with col2:
        st.subheader("Selected Voice")
        if st.session_state.selected_voice and st.session_state.selected_voice in voice_dict:
            voice = voice_dict.get(st.session_state.selected_voice)
            if voice:
                st.write(f"**Name:** {safe_get(voice, 'name', 'Unknown')}")
                st.write(f"**Gender:** {safe_get(voice, 'gender', 'Not specified')}")
                st.write(f"**Language:** {safe_get(voice, 'language', 'Not specified')}")
                st.write(f"**Accent:** {safe_get(voice, 'accent', 'Not specified')}")
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
                
                if result and isinstance(result, dict) and "id" in result:
                    video_id = result["id"]
                    st.success(f"Video generation started! Video ID: {video_id}")
                    
                    # Get avatar and voice names for display
                    avatar_name = safe_get(avatar_dict.get(avatar_id, {}), "name", "Unknown Avatar")
                    voice_name = safe_get(voice_dict.get(voice_id, {}), "name", "Unknown Voice")
                    
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
                    if show_debug and result:
                        st.write("API Response:", result)

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
                            
                            if status_data and isinstance(status_data, dict):
                                current_status = safe_get(status_data, "status", "unknown")
                                st.session_state.videos[i]["status"] = current_status
                                
                                if current_status == "completed":
                                    video_url = safe_get(status_data, "videoUrl")
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
                                if show_debug and status_data:
                                    st.write("Status Response:", status_data)
                
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
                        time.sleep(0.01)  # Reduced sleep time for faster animation
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

# Add API tester section
with st.sidebar:
    with st.expander("API Tester"):
        st.subheader("Test API Endpoints")
        test_button = st.button("Test API Connection")
        if test_button:
            st.write("Testing API connection...")
            
            # Test avatar endpoint
            try:
                avatar_response = requests.get(
                    "https://avatar.pipio.ai/actor",
                    headers={"Authorization": f"Key {api_key}", "Accept": "application/json"}
                )
                st.write(f"Avatar API Status Code: {avatar_response.status_code}")
                if avatar_response.status_code == 200:
                    st.success("Avatar API connection successful")
                    try:
                        data = avatar_response.json()
                        st.write(f"Response Type: {type(data)}")
                        if isinstance(data, dict):
                            st.write(f"Keys: {list(data.keys())}")
                        elif isinstance(data, list):
                            st.write(f"List length: {len(data)}")
                            if len(data) > 0:
                                st.write("First item:", data[0])
                    except:
                        st.error("Could not parse JSON response")
                else:
                    st.error(f"Avatar API error: {avatar_response.status_code}")
            except Exception as e:
                st.error(f"Avatar API test failed: {str(e)}")
            
            # Test voice endpoint
            try:
                voice_response = requests.get(
                    "https://avatar.pipio.ai/voice",
                    headers={"Authorization": f"Key {api_key}", "Accept": "application/json"}
                )
                st.write(f"Voice API Status Code: {voice_response.status_code}")
                if voice_response.status_code == 200:
                    st.success("Voice API connection successful")
                    try:
                        data = voice_response.json()
                        st.write(f"Response Type: {type(data)}")
                        if isinstance(data, dict):
                            st.write(f"Keys: {list(data.keys())}")
                        elif isinstance(data, list):
                            st.write(f"List length: {len(data)}")
                            if len(data) > 0:
                                st.write("First item:", data[0])
                    except:
                        st.error("Could not parse JSON response")
                else:
                    st.error(f"Voice API error: {voice_response.status_code}")
            except Exception as e:
                st.error(f"Voice API test failed: {str(e)}")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### Pipio AI Avatar Generator")
    st.markdown("Version 2.2")
with col2:
    st.markdown("### Powered by")
    st.markdown("[Pipio AI API](https://pipio.ai)")
with col3:
    st.markdown("### Need Help?")
    st.markdown("[Documentation](https://docs.pipio.ai) | [Support](mailto:support@pipio.ai)")
