# voice_client.py
import requests
import json
import speech_recognition as sr
from gtts import gTTS
import sounddevice as sd
from scipy.io import wavfile
import tempfile
import os
import time

# --- Configuration ---
AGENT_API_URL = "http://localhost:8000/query"
DEFAULT_COLLECTION = "customers"
LISTEN_TIMEOUT = 10
PHRASE_TIME_LIMIT = 15

def speak_text(text):
    """Converts text to speech and speaks it using gTTS and sounddevice."""
    print(f"🤖 Agent: {text}")
    try:
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            wav_path = fp.name.replace('.mp3', '.wav')
            # Convert mp3 to wav for playback
            os.system(f"ffmpeg -y -i {fp.name} {wav_path} > /dev/null 2>&1")
            samplerate, data = wavfile.read(wav_path)
            sd.play(data, samplerate)
            sd.wait()
            os.remove(fp.name)
            os.remove(wav_path)
    except Exception as e:
        print(f"Error in gTTS speak_text: {e}")

# --- Initialize Speech-to-Text Recognizer ---
recognizer = sr.Recognizer()
recognizer.energy_threshold = 4000
recognizer.dynamic_energy_threshold = True

def listen_to_user():
    """Captures audio from the microphone and transcribes it to text."""
    with sr.Microphone() as source:
        speak_text("Listening... please speak your query.")
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=LISTEN_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT)
        except sr.WaitTimeoutError:
            speak_text("I didn't hear anything. Please try again when you're ready.")
            return None

    try:
        print("🔍 Recognizing...")
        user_input = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {user_input}")
        return user_input
    except sr.UnknownValueError:
        speak_text("Sorry, I didn't catch that. Could you please repeat?")
        return None
    except sr.RequestError as e:
        speak_text(f"My speech recognition service seems to be down. Error: {e}")
        return None

def summarize_for_speech(response_json):
    """Creates a natural language summary of the agent's JSON response."""
    if response_json.get("error"):
        return f"I encountered an error: {response_json['error']}"

    data = response_json.get("data", [])
    count = len(data)

    if count == 0:
        return "I couldn't find any matching results for your query."
    
    summary = f"I found {count} matching results. "
    
    if 0 < count <= 3:
        summary += "Here they are: "
        detailed_items = []
        for item in data:
            if 'name' in item:
                detailed_items.append(item['name'])
            elif 'account_id' in item:
                detailed_items.append(f"account ID {item['account_id']}")
            else:
                detailed_items.append(f"an item with ID {item.get('_id')}")
        summary += ", ".join(detailed_items)
    
    return summary

def main_loop():
    """The main conversation loop for the voice client."""
    session_id = None
    speak_text("Hello! I'm your conversational database agent. How can I help you?")

    while True:
        user_query = listen_to_user()

        if user_query is None:
            continue

        if user_query.lower() in ["goodbye", "exit", "stop", "quit"]:
            speak_text("Goodbye!")
            break
        
        payload = { "collection": DEFAULT_COLLECTION, "query_text": user_query }
        if session_id:
            payload["session_id"] = session_id
        
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(AGENT_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            response_json = response.json()
            session_id = response_json.get("session_id")
            speech_summary = summarize_for_speech(response_json)
            speak_text(speech_summary)
        except requests.exceptions.RequestException as e:
            speak_text(f"I couldn't connect to my brain. Please check the server. Error: {e}")
        except Exception as e:
            speak_text(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main_loop()