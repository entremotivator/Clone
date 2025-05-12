import streamlit as st
import requests
import json
import time
import base64
import pandas as pd
from datetime import datetime
import traceback
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
if "api_errors" not in st.session_state:
    st.session_state.api_errors = []
if "last_api_check" not in st.session_state:
    st.session_state.last_api_check = None

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
        use_mock_data = st.checkbox("Use mock data if API fails", value=True)
    
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
    
    # Add API key instructions
    st.info("To get started, you'll need a Pipio AI API key:")
    st.markdown("""
    1. Sign up for an account at [Pipio AI](https://pipio.ai)
    2. Navigate to your account settings or API section
    3. Generate a new API key
    4. Copy and paste the key into the sidebar
    """)
    
    st.stop()

# Set headers for API requests
headers = {
    "Accept": "application/json",
    "Authorization": f"Key {api_key}"
}

# Function to log API errors
def log_api_error(endpoint, error_type, error_message, response_data=None):
    """Log API errors for troubleshooting"""
    error_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "endpoint": endpoint,
        "error_type": error_type,
        "error_message": error_message,
        "response_data": response_data
    }
    st.session_state.api_errors.append(error_entry)
    return error_entry

# Function to safely get value from dictionary
def safe_get(dictionary, key, default=None):
    """Safely get a value from a dictionary"""
    if dictionary is None:
        return default
    if not isinstance(dictionary, dict):
        return default
    return dictionary.get(key, default)

# Function to create mock avatars
def get_mock_avatars():
    """Generate mock avatar data for testing"""
    return [
        {
            "id": "avatar1",
            "name": "Business Man",
            "previewImageUrl": "https://placeholder.svg?height=150&width=150&query=Business+Man+Avatar",
            "description": "Professional male avatar in business attire"
        },
        {
            "id": "avatar2",
            "name": "Business Woman",
            "previewImageUrl": "https://placeholder.svg?height=150&width=150&query=Business+Woman+Avatar",
            "description": "Professional female avatar in business attire"
        },
        {
            "id": "avatar3",
            "name": "Casual Man",
            "previewImageUrl": "https://placeholder.svg?height=150&width=150&query=Casual+Man+Avatar",
            "description": "Casual male avatar in everyday clothing"
        },
        {
            "id": "avatar4",
            "name": "Casual Woman",
            "previewImageUrl": "https://placeholder.svg?height=150&width=150&query=Casual+Woman+Avatar",
            "description": "Casual female avatar in everyday clothing"
        }
    ]

# Function to create mock voices
def get_mock_voices():
    """Generate mock voice data for testing"""
    return [
        {
            "id": "voice1",
            "name": "James",
            "gender": "Male",
            "language": "English",
            "accent": "American"
        },
        {
            "id": "voice2",
            "name": "Emma",
            "gender": "Female",
            "language": "English",
            "accent": "British"
        },
        {
            "id": "voice3",
            "name": "Michael",
            "gender": "Male",
            "language": "English",
            "accent": "Australian"
        },
        {
            "id": "voice4",
            "name": "Sophia",
            "gender": "Female",
            "language": "English",
            "accent": "American"
        },
        {
            "id": "voice5",
            "name": "Carlos",
            "gender": "Male",
            "language": "Spanish",
            "accent": "Latin American"
        }
    ]

# Function to fetch avatars with caching
@st.cache_data(ttl=600)
def get_avatars(api_key):
    try:
        response = requests.get(
            "https://avatar.pipio.ai/actor",
            headers={"Authorization": f"Key {api_key}", "Accept": "application/json"},
            timeout=10  # Add timeout to prevent hanging
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
        
        # According to Pipio AI documentation, the response should be a list of actors
        # If it's already a list, use it directly
        if isinstance(raw_response, list):
            return raw_response
        
        # If it's a dictionary, look for the 'actors' key (based on documentation)
        if isinstance(raw_response, dict):
            # Check for common keys based on API documentation
            if 'actors' in raw_response:
                return raw_response['actors']
            elif 'data' in raw_response:
                return raw_response['data']
            elif 'results' in raw_response:
                return raw_response['results']
            # If we can't find a specific key, log the error and return empty or mock data
            else:
                error_msg = "Could not find actors in API response. Response keys: " + str(list(raw_response.keys()))
                log_api_error("avatar.pipio.ai/actor", "MissingDataKey", error_msg, raw_response)
                if use_mock_data:
                    return get_mock_avatars()
                return []
        
        # If response is neither a list nor a dictionary, log error and return empty or mock data
        error_msg = f"Unexpected response format: {type(raw_response)}"
        log_api_error("avatar.pipio.ai/actor", "InvalidResponseFormat", error_msg, str(raw_response)[:500])
        if use_mock_data:
            return get_mock_avatars()
        return []
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching avatars: {str(e)}"
        response_text = None
        if hasattr(e, 'response') and e.response:
            try:
                response_text = e.response.text
                error_msg += f" (Status: {e.response.status_code})"
            except:
                pass
        log_api_error("avatar.pipio.ai/actor", "RequestException", error_msg, response_text)
        if use_mock_data:
            return get_mock_avatars()
        return []
    except json.JSONDecodeError as e:
        error_msg = f"Error decoding avatar JSON: {str(e)}"
        log_api_error("avatar.pipio.ai/actor", "JSONDecodeError", error_msg, response.text[:500])
        if use_mock_data:
            return get_mock_avatars()
        return []
    except Exception as e:
        error_msg = f"Unexpected error fetching avatars: {str(e)}"
        log_api_error("avatar.pipio.ai/actor", "UnexpectedException", error_msg, traceback.format_exc())
        if use_mock_data:
            return get_mock_avatars()
        return []

# Function to fetch voices with caching
@st.cache_data(ttl=600)
def get_voices(api_key):
    try:
        response = requests.get(
            "https://avatar.pipio.ai/voice",
            headers={"Authorization": f"Key {api_key}", "Accept": "application/json"},
            timeout=10  # Add timeout to prevent hanging
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
        
        # According to Pipio AI documentation, the response should be a list of voices
        # If it's already a list, use it directly
        if isinstance(raw_response, list):
            return raw_response
        
        # If it's a dictionary, look for the 'voices' key (based on documentation)
        if isinstance(raw_response, dict):
            # Check for common keys based on API documentation
            if 'voices' in raw_response:
                return raw_response['voices']
            elif 'data' in raw_response:
                return raw_response['data']
            elif 'results' in raw_response:
                return raw_response['results']
            # If we can't find a specific key, log the error and return empty or mock data
            else:
                error_msg = "Could not find voices in API response. Response keys: " + str(list(raw_response.keys()))
                log_api_error("avatar.pipio.ai/voice", "MissingDataKey", error_msg, raw_response)
                if use_mock_data:
                    return get_mock_voices()
                return []
        
        # If response is neither a list nor a dictionary, log error and return empty or mock data
        error_msg = f"Unexpected response format: {type(raw_response)}"
        log_api_error("avatar.pipio.ai/voice", "InvalidResponseFormat", error_msg, str(raw_response)[:500])
        if use_mock_data:
            return get_mock_voices()
        return []
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching voices: {str(e)}"
        response_text = None
        if hasattr(e, 'response') and e.response:
            try:
                response_text = e.response.text
                error_msg += f" (Status: {e.response.status_code})"
            except:
                pass
        log_api_error("avatar.pipio.ai/voice", "RequestException", error_msg, response_text)
        if use_mock_data:
            return get_mock_voices()
        return []
    except json.JSONDecodeError as e:
        error_msg = f"Error decoding voice JSON: {str(e)}"
        log_api_error("avatar.pipio.ai/voice", "JSONDecodeError", error_msg, response.text[:500])
        if use_mock_data:
            return get_mock_voices()
        return []
    except Exception as e:
        error_msg = f"Unexpected error fetching voices: {str(e)}"
        log_api_error("avatar.pipio.ai/voice", "UnexpectedException", error_msg, traceback.format_exc())
        if use_mock_data:
            return get_mock_voices()
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
            data=json.dumps(payload),
            timeout=30  # Longer timeout for video generation
        )
        response.raise_for_status()
        response_data = response.json()
        
        # Debug output for response
        if show_debug:
            st.write("Generate Video Response:", response_data)
        
        return response_data
    except requests.exceptions.RequestException as e:
        error_msg = f"Error generating video: {str(e)}"
        response_text = None
        if hasattr(e, 'response') and e.response:
            try:
                response_text = e.response.text
                error_msg += f" (Status: {e.response.status_code})"
            except:
                pass
        log_api_error("generate.pipio.ai/single-clip", "RequestException", error_msg, response_text)
        return None
    except json.JSONDecodeError as e:
        error_msg = f"Error decoding generation JSON: {str(e)}"
        log_api_error("generate.pipio.ai/single-clip", "JSONDecodeError", error_msg, response.text[:500])
        return None
    except Exception as e:
        error_msg = f"Unexpected error generating video: {str(e)}"
        log_api_error("generate.pipio.ai/single-clip", "UnexpectedException", error_msg, traceback.format_exc())
        return None

# Function to check video status
def check_video_status(video_id, api_key):
    try:
        response = requests.get(
            f"https://generate.pipio.ai/single-clip/{video_id}",
            headers={"Authorization": f"Key {api_key}", "Accept": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        response_data = response.json()
        
        # Debug output for response
        if show_debug:
            st.write("Video Status Response:", response_data)
        
        return response_data
    except requests.exceptions.RequestException as e:
        error_msg = f"Error checking video status: {str(e)}"
        response_text = None
        if hasattr(e, 'response') and e.response:
            try:
                response_text = e.response.text
                error_msg += f" (Status: {e.response.status_code})"
            except:
                pass
        log_api_error(f"generate.pipio.ai/single-clip/{video_id}", "RequestException", error_msg, response_text)
        return None
    except json.JSONDecodeError as e:
        error_msg = f"Error decoding status JSON: {str(e)}"
        log_api_error(f"generate.pipio.ai/single-clip/{video_id}", "JSONDecodeError", error_msg, response.text[:500])
        return None
    except Exception as e:
        error_msg = f"Unexpected error checking status: {str(e)}"
        log_api_error(f"generate.pipio.ai/single-clip/{video_id}", "UnexpectedException", error_msg, traceback.format_exc())
        return None

# Function to download video
def download_video(url):
    try:
        response = requests.get(url, timeout=30)  # Longer timeout for video download
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        error_msg = f"Error downloading video: {str(e)}"
        log_api_error(url, "RequestException", error_msg)
        return None
    except Exception as e:
        error_msg = f"Unexpected error downloading video: {str(e)}"
        log_api_error(url, "UnexpectedException", error_msg, traceback.format_exc())
        return None

# Function to add to history
def add_to_history(action, details):
    st.session_state.history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details
    })

# Update last API check time
st.session_state.last_api_check = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
    # Create an error container with custom styling
    st.markdown("""
    <style>
    .error-container {
        background-color: #FFF0F0;
        border-left: 5px solid #FF5555;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .error-title {
        color: #CC0000;
        font-size: 24px;
        margin-bottom: 10px;
    }
    .error-message {
        color: #333333;
        font-size: 16px;
        margin-bottom: 15px;
    }
    .error-detail {
        background-color: #FFEEEE;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        margin-bottom: 15px;
    }
    .troubleshooting-title {
        color: #0066CC;
        font-size: 20px;
        margin: 15px 0 10px 0;
    }
    .troubleshooting-step {
        background-color: #F0F8FF;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 3px solid #0066CC;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="error-container">', unsafe_allow_html=True)
    st.markdown('<div class="error-title">⚠️ API Connection Error</div>', unsafe_allow_html=True)
    
    # Main error message
    st.markdown('<div class="error-message">The application was unable to retrieve avatars and/or voices from the Pipio AI API. This could be due to several reasons:</div>', unsafe_allow_html=True)
    
    # Specific error details
    error_details = []
    if not isinstance(avatars, list):
        error_details.append(f"• Avatar data is not in the expected format: received {type(avatars).__name__} instead of list")
    elif len(avatars) == 0:
        error_details.append("• No avatars were found in the API response")
    
    if not isinstance(voices, list):
        error_details.append(f"• Voice data is not in the expected format: received {type(voices).__name__} instead of list")
    elif len(voices) == 0:
        error_details.append("• No voices were found in the API response")
    
    # Add API error details if available
    if st.session_state.api_errors:
        recent_errors = st.session_state.api_errors[-3:]  # Get the 3 most recent errors
        for error in recent_errors:
            error_details.append(f"• {error['endpoint']}: {error['error_type']} - {error['error_message']}")
    
    st.markdown('<div class="error-detail">' + '<br>'.join(error_details) + '</div>', unsafe_allow_html=True)
    
    # Troubleshooting steps
    st.markdown('<div class="troubleshooting-title">🔍 Troubleshooting Steps</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="troubleshooting-step"><strong>1. Verify your API key</strong><br>Ensure your API key is correct and has not expired. You can find your API key in your Pipio AI account dashboard.</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="troubleshooting-step"><strong>2. Check API access</strong><br>Confirm that your account has access to the Pipio AI avatar and voice APIs. Some features may require specific subscription levels.</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="troubleshooting-step"><strong>3. Test API connection</strong><br>Use the API Tester in the sidebar to check if the API endpoints are responding correctly.</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="troubleshooting-step"><strong>4. Check for service outages</strong><br>Visit the <a href="https://status.pipio.ai" target="_blank">Pipio AI Status Page</a> to see if there are any known service disruptions.</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="troubleshooting-step"><strong>5. Contact support</strong><br>If the issue persists, contact Pipio AI support at <a href="mailto:support@pipio.ai">support@pipio.ai</a> with the error details shown above.</div>', unsafe_allow_html=True)
    
    # Mock data option
    if use_mock_data:
        st.markdown('<div class="troubleshooting-step"><strong>6. Use mock data</strong><br>You can continue using the application with mock data for testing purposes. Note that video generation will not work with mock data.</div>', unsafe_allow_html=True)
        if st.button("Continue with Mock Data", type="primary"):
            avatars = get_mock_avatars()
            voices = get_mock_voices()
            st.success("Mock data loaded successfully. You can now explore the application interface.")
            st.rerun()
    else:
        st.markdown('<div class="troubleshooting-step"><strong>6. Enable mock data</strong><br>You can enable mock data in the Advanced Settings section of the sidebar to test the application interface without a working API connection.</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show API response details in an expander for advanced troubleshooting
    with st.expander("Advanced Troubleshooting Information"):
        st.subheader("API Response Details")
        st.write("Last API check:", st.session_state.last_api_check)
        st.write("API key length:", len(api_key) if api_key else "No API key provided")
        
        st.subheader("Avatar API Response")
        if isinstance(avatars, list):
            st.write("Avatar count:", len(avatars))
            if len(avatars) > 0:
                st.write("Sample avatar:", avatars[0])
        else:
            st.write("Avatar data:", avatars)
        
        st.subheader("Voice API Response")
        if isinstance(voices, list):
            st.write("Voice count:", len(voices))
            if len(voices) > 0:
                st.write("Sample voice:", voices[0])
        else:
            st.write("Voice data:", voices)
        
        st.subheader("Recent API Errors")
        if st.session_state.api_errors:
            for i, error in enumerate(reversed(st.session_state.api_errors[-5:])):  # Show 5 most recent errors
                st.write(f"Error {i+1}:")
                st.write(f"- Timestamp: {error['timestamp']}")
                st.write(f"- Endpoint: {error['endpoint']}")
                st.write(f"- Type: {error['error_type']}")
                st.write(f"- Message: {error['error_message']}")
                if error['response_data']:
                    with st.expander("Response Data"):
                        st.code(str(error['response_data']))
        else:
            st.write("No API errors logged")
        
        # Add curl command for manual testing
        st.subheader("Manual API Testing")
        st.markdown("You can test the API endpoints manually using the following curl commands:")
        
        st.code(f'curl -X GET -H "Authorization: Key {api_key[:3]}...{api_key[-3:] if len(api_key) > 6 else ""}" -H "Accept: application/json" https://avatar.pipio.ai/actor', language="bash")
        st.code(f'curl -X GET -H "Authorization: Key {api_key[:3]}...{api_key[-3:] if len(api_key) > 6 else ""}" -H "Accept: application/json" https://avatar.pipio.ai/voice', language="bash")
        
        # Clear error logs button
        if st.button("Clear Error Logs"):
            st.session_state.api_errors = []
            st.success("Error logs cleared")
            st.rerun()
    
    st.stop()

# Create tabs for different sections
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Select Avatar & Voice", "Generate Video", "Your Videos", "History & Analytics", "API Status"])

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
        # Add search filter
        avatar_search = st.text_input("Search Avatars", "")
        
        # Filter avatars based on search
        filtered_avatar_names = {name: id for name, id in avatar_names.items() 
                               if not avatar_search or avatar_search.lower() in name.lower()}
        
        if not filtered_avatar_names:
            st.warning(f"No avatars found matching '{avatar_search}'")
        else:
            st.success(f"Found {len(filtered_avatar_names)} avatars")
            
            # Calculate number of columns based on screen width
            avatar_cols = st.columns(3)
            
            for i, (avatar_name, avatar_id) in enumerate(filtered_avatar_names.items()):
                avatar = avatar_dict[avatar_id]
                with avatar_cols[i % 3]:
                    # Create a container for each avatar
                    with st.container():
                        st.subheader(avatar_name)
                        avatar_image = safe_get(avatar, "previewImageUrl")
                        if avatar_image:
                            st.image(avatar_image, width=150)
                        else:
                            st.image("https://placeholder.svg?height=150&width=150&query=No+Preview", width=150)
                        
                        # Add description if available
                        avatar_desc = safe_get(avatar, "description")
                        if avatar_desc:
                            st.caption(avatar_desc)
                        
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
        
        # Add search filter
        voice_search = st.text_input("Search Voices", "")
        
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
        
        # Apply search filter
        if voice_search:
            filtered_df = filtered_df[filtered_df["Name"].str.contains(voice_search, case=False) | 
                                     filtered_df["Gender"].str.contains(voice_search, case=False) | 
                                     filtered_df["Language"].str.contains(voice_search, case=False) | 
                                     filtered_df["Accent"].str.contains(voice_search, case=False)]
        
        # Display filtered dataframe
        if len(filtered_df) == 0:
            st.warning("No voices match your filters. Please adjust your search criteria.")
        else:
            st.success(f"Found {len(filtered_df)} voices")
            st.dataframe(filtered_df, use_container_width=True)
            
            # Voice selection
            # Create a dictionary of display names for the filtered dataframe
            filtered_voice_names = {}
            for _, row in filtered_df.iterrows():
                display_name = f"{row['Name']} ({row['Gender']}, {row['Language']})"
                filtered_voice_names[display_name] = row['ID']
            
            if filtered_voice_names:
                selected_voice_name = st.selectbox("Select Voice", options=list(filtered_voice_names.keys()))
                if st.button("Confirm Voice Selection"):
                    st.session_state.selected_voice = filtered_voice_names[selected_voice_name]
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
                
                # Add description if available
                avatar_desc = safe_get(avatar, "description")
                if avatar_desc:
                    st.write(f"**Description:** {avatar_desc}")
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

with tab5:
    st.header("API Status & Diagnostics")
    
    # API Status Overview
    st.subheader("API Connection Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avatar_status = "✅ Connected" if isinstance(avatars, list) and len(avatars) > 0 else "❌ Error"
        st.metric("Avatar API", avatar_status)
    
    with col2:
        voice_status = "✅ Connected" if isinstance(voices, list) and len(voices) > 0 else "❌ Error"
        st.metric("Voice API", voice_status)
    
    with col3:
        last_check = st.session_state.last_api_check if st.session_state.last_api_check else "Never"
        st.metric("Last API Check", last_check)
    
    # API Error Log
    st.subheader("API Error Log")
    
    if not st.session_state.api_errors:
        st.success("No API errors logged")
    else:
        # Convert errors to dataframe
        error_df = pd.DataFrame(st.session_state.api_errors)
        
        # Display error table
        st.dataframe(error_df[["timestamp", "endpoint", "error_type", "error_message"]], use_container_width=True)
        
        # Error details
        if st.button("Clear Error Log"):
            st.session_state.api_errors = []
            st.success("Error log cleared")
            st.rerun()
    
    # API Test Tool
    st.subheader("API Test Tool")
    
    test_col1, test_col2 = st.columns(2)
    
    with test_col1:
        if st.button("Test Avatar API", use_container_width=True):
            with st.spinner("Testing Avatar API..."):
                try:
                    response = requests.get(
                        "https://avatar.pipio.ai/actor",
                        headers={"Authorization": f"Key {api_key}", "Accept": "application/json"},
                        timeout=10
                    )
                    
                    st.write(f"Status Code: {response.status_code}")
                    
                    if response.status_code == 200:
                        st.success("Avatar API connection successful")
                        try:
                            data = response.json()
                            st.write(f"Response Type: {type(data)}")
                            if isinstance(data, dict):
                                st.write(f"Keys: {list(data.keys())}")
                                if 'actors' in data:
                                    st.write(f"Found {len(data['actors'])} avatars")
                                    st.write("Sample avatar:", data['actors'][0] if data['actors'] else "No avatars found")
                            elif isinstance(data, list):
                                st.write(f"Found {len(data)} avatars")
                                st.write("Sample avatar:", data[0] if data else "No avatars found")
                        except json.JSONDecodeError:
                            st.error("Could not parse JSON response")
                            st.code(response.text[:500])
                    else:
                        st.error(f"Avatar API error: {response.status_code}")
                        st.code(response.text[:500])
                except Exception as e:
                    st.error(f"Avatar API test failed: {str(e)}")
    
    with test_col2:
        if st.button("Test Voice API", use_container_width=True):
            with st.spinner("Testing Voice API..."):
                try:
                    response = requests.get(
                        "https://avatar.pipio.ai/voice",
                        headers={"Authorization": f"Key {api_key}", "Accept": "application/json"},
                        timeout=10
                    )
                    
                    st.write(f"Status Code: {response.status_code}")
                    
                    if response.status_code == 200:
                        st.success("Voice API connection successful")
                        try:
                            data = response.json()
                            st.write(f"Response Type: {type(data)}")
                            if isinstance(data, dict):
                                st.write(f"Keys: {list(data.keys())}")
                                if 'voices' in data:
                                    st.write(f"Found {len(data['voices'])} voices")
                                    st.write("Sample voice:", data['voices'][0] if data['voices'] else "No voices found")
                            elif isinstance(data, list):
                                st.write(f"Found {len(data)} voices")
                                st.write("Sample voice:", data[0] if data else "No voices found")
                        except json.JSONDecodeError:
                            st.error("Could not parse JSON response")
                            st.code(response.text[:500])
                    else:
                        st.error(f"Voice API error: {response.status_code}")
                        st.code(response.text[:500])
                except Exception as e:
                    st.error(f"Voice API test failed: {str(e)}")
    
    # API Documentation
    st.subheader("API Documentation")
    
    st.markdown("""
    ### Pipio AI API Endpoints
    
    #### Avatar List
    \`\`\`
    GET https://avatar.pipio.ai/actor
    \`\`\`
    
    #### Voice List
    \`\`\`
    GET https://avatar.pipio.ai/voice
    \`\`\`
    
    #### Generate Video
    \`\`\`
    POST https://generate.pipio.ai/single-clip
    \`\`\`
    
    #### Check Video Status
    \`\`\`
    GET https://generate.pipio.ai/single-clip/{video_id}
    \`\`\`
    
    For more information, visit the [Pipio AI API Documentation](https://docs.pipio.ai).
    """)

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
                    headers={"Authorization": f"Key {api_key}", "Accept": "application/json"},
                    timeout=10
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
                    headers={"Authorization": f"Key {api_key}", "Accept": "application/json"},
                    timeout=10
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
    st.markdown("Version 3.0")
with col2:
    st.markdown("### Powered by")
    st.markdown("[Pipio AI API](https://pipio.ai)")
with col3:
    st.markdown("### Need Help?")
    st.markdown("[Documentation](https://docs.pipio.ai) | [Support](mailto:support@pipio.ai)")
