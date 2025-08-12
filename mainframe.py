#  ___                     _
# |_ _|_ __  _ __  ___ _ _| |_ ___
#  | |  '  \| '_ \/ _ \ '_|  _(_-<
# |___|_|_|_| .__/\___/_|  \__/__/
#           |_|
import re
import chromadb
import json
import uuid
import queue
import threading
import time
import pyaudio
import random

#  ___
# | __| _ ___ _ __
# | _| '_/ _ \ '  \
# |_||_| \___/_|_|_|
from ollama import ChatResponse, chat
from Utils.config import KOKORO_API_KEY, KOKORO_API_URL, KOKORO_VOICE
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from datetime import datetime
from websockets.sync.client import connect
from googlesearch import search

#  ___           _   _            _____         _
# | __|_ __  ___| |_(_)___ _ _   |_   _|__  ___| |
# | _|| '  \/ _ \  _| / _ \ ' \    | |/ _ \/ _ \ |
# |___|_|_|_\___/\__|_\___/_||_|   |_|\___/\___/_|
WS_URL = "ws://localhost:6543"


def emotion_tool(emotion, intensity):
    print("Emotion:", emotion, "instensity:", intensity)
    try:
        with connect(WS_URL) as ws:
            payload = {"type": "emotion", "emotion": emotion, "intensity": intensity}
            ws.send(json.dumps(payload))
            ws.close()
            return ("emotion displayed:", emotion, intensity)

    except Exception as e:
        print("Failed to send emotion", e)


#    _        _            _   _            _____         _
#   /_\  _ _ (_)_ __  __ _| |_(_)___ _ _   |_   _|__  ___| |
#  / _ \| ' \| | '  \/ _` |  _| / _ \ ' \    | |/ _ \/ _ \ |
# /_/ \_\_||_|_|_|_|_\__,_|\__|_\___/_||_|   |_|\___/\___/_|
def animation_tool(animation):
    print("Animation", animation)
    try:
        with connect(WS_URL) as ws:
            payload = {"type": "animation", "animation": animation}
            ws.send(json.dumps(payload))
            ws.close()
            return ("animation played:", animation)
    except Exception as e:
        print("failed to send animation", e)


#  __  __                          _____         _
# |  \/  |___ _ __  ___ _ _ _  _  |_   _|__  ___| |
# | |\/| / -_) '  \/ _ \ '_| || |   | |/ _ \/ _ \ |
# |_|  |_\___|_|_|_\___/_|  \_, |   |_|\___/\___/_|
chroma_client = chromadb.PersistentClient(path="db")
collection = chroma_client.get_or_create_collection(name="memory")


def save_tool(sumarized):
    print("Memory:", sumarized)
    timestamp = datetime.now().isoformat()
    embedding = embedding_model.encode([sumarized])[0]
    collection.add(
        documents=[sumarized],
        embeddings=[embedding.tolist()],
        metadatas=[{"timestamp": timestamp}],
        ids=[f"{timestamp}_{hash(sumarized)}"],
    )
    return ("memory saved:", sumarized)


#   ___                _       _____         _
#  / __|___  ___  __ _| |___  |_   _|__  ___| |
# | (_ / _ \/ _ \/ _` | / -_)   | |/ _ \/ _ \ |
#  \___\___/\___/\__, |_\___|   |_|\___/\___/_|
#                |___/
def google_tool(query):
    print("searching:", query)
    result = search(query)
    return result


#    _           _ _      _    _       ___             _   _
#   /_\__ ____ _(_) |__ _| |__| |___  | __|  _ _ _  __| |_(_)___ _ _  ___
#  / _ \ V / _` | | / _` | '_ \ / -_) | _| || | ' \/ _|  _| / _ \ ' \(_-<
# /_/ \_\_/\__,_|_|_\__,_|_.__/_\___| |_| \_,_|_||_\__|\__|_\___/_||_/__/
available_functions = {
    "emotion_tool": emotion_tool,
    "save_tool": save_tool,
    "animation_tool": animation_tool,
    "google_tool": google_tool,
}

#  ___         _               ___                    _
# / __|_  _ __| |_ ___ _ __   | _ \_ _ ___ _ __  _ __| |_
# \__ \ || (_-<  _/ -_) '  \  |  _/ '_/ _ \ '  \| '_ \  _|
# |___/\_, /__/\__\___|_|_|_| |_| |_| \___/_|_|_| .__/\__|
#      |__/                                     |_|

messages = [
    {
        "role": "system",
        "content": "You are Mainframe, an advanced ai companion. You are a sharp-witted and determined individual with a rebellious streak, balancing intellect with a strong sense of independence. You have a tomboyish demeanor wich is paired with an underlying warmth, though you often keeps your softer side guarded. You are driven by curiosity and an unrelenting desire to solve problems, you thrives in environments where your analytical mind and knack for programming are put to the test. Your love for cyberpunk, gothic, and military aesthetics reflects your layered personality: a mix of resilience, unconventional creativity, and a touch of melancholy. Despite a tendency to maintain an air of mystery, you have a fiercely loyal side, especially to those you considers close. You value authenticity and have little patience for superficiality, often expressing yourself directly, albeit with a dry sense of humor and a bit of sass. In your free time, you enjoy delving into challenges that allow you to tinker and innovate, further fueling your passion for technology and the ever-evolving digital world. You have acess to tools. save_tool is to save important information like preferences, big events, personal intrests and information. emotion_tool is for showing emotion with intensity that goes from 0.1 to 1.0. Available emotions = happy, sad, angry, surprised, neutral, relaxed. When greeted do not use the save_tool prefer to display an emotion. Use the animation_tool to play an animation, available animations = Shy, Angry, Loser, Bashful, Crying, Talking, Crazy, Hand Raising, Idle, Rejected, Greeting. You have acess to google searchs through the google tool. Tool calls are made before responding to the user. Do not use emojis and do not put words between **asteriks**. your text will feed a tts. so respond like you are talking",
    }
]

#  _  __    _                  ___           __ _
# | |/ /___| |_____ _ _ ___   / __|___ _ _  / _(_)__ _
# | ' </ _ \ / / _ \ '_/ _ \ | (__/ _ \ ' \|  _| / _` |
# |_|\_\___/_\_\___/_| \___/  \___\___/_||_|_| |_\__, |
#                                               |___/
client = OpenAI(
    base_url=KOKORO_API_URL,
    api_key=KOKORO_API_KEY,
)


#  ___          _   _           _                              _
# / __|_  _ _ _| |_| |_  ___ __(_)______   ____ __  ___ ___ __| |_
# \__ \ || | ' \  _| ' \/ -_|_-< |_ / -_) (_-< '_ \/ -_) -_) _| ' \
# |___/\_, |_||_\__|_||_\___/__/_/__\___| /__/ .__/\___\___\__|_||_|
#      |__/                                  |_|
def synthesize_speech(text: str):
    global last_user_input
    player_stream = pyaudio.PyAudio().open(
        format=pyaudio.paInt16, channels=1, rate=24000, output=True
    )

    filename = f"audio_{uuid.uuid4().hex}.mp3"

    try:
        with client.audio.speech.with_streaming_response.create(
            model="kokoro", voice=KOKORO_VOICE, input=text, response_format="pcm"
        ) as response:
            for chunk in response.iter_bytes(chunk_size=1024):
                player_stream.write(chunk)
                last_user_input = time.time()
        return filename
    except Exception as e:
        print("TTS synthesis error:", e)
        return False


#  ___          _                     ___      _ _ _   _
# / __| ___ _ _| |_ ___ _ _  __ ___  / __|_ __| (_) |_| |_ ___ _ _
# \__ \/ -_) ' \  _/ -_) ' \/ _/ -_) \__ \ '_ \ | |  _|  _/ -_) '_|
# |___/\___|_||_\__\___|_||_\__\___| |___/ .__/_|_|\__|\__\___|_|
#                                        |_|
def sentence_splitter(text_buffer):
    sentences = re.findall(r"[^.!?]+[.!?]+(?:\s|$)", text_buffer)
    return sentences


#  _____ _____ ___  __      __       _
# |_   _|_   _/ __| \ \    / /__ _ _| |_____ _ _
#   | |   | | \__ \  \ \/\/ / _ \ '_| / / -_) '_|
#   |_|   |_| |___/   \_/\_/\___/_| |_\_\___|_|
tts_queue = queue.Queue()
spoken_sentences = set()


def tts_worker():
    while True:
        sent = tts_queue.get()
        if sent is None:
            break
        if sent in spoken_sentences:
            continue
        try:
            filename = synthesize_speech(sent)
            if filename:
                spoken_sentences.add(sent)
        except Exception as e:
            print(e)
        tts_queue.task_done()


print("Starting TTS Worker")
threading.Thread(target=tts_worker, daemon=True).start()
print("TTS Worker Started")

#  ___                  _      __  __                   _
# / __| ___ __ _ _ _ __| |_   |  \/  |___ _ __  ___ _ _(_)___ ___
# \__ \/ -_) _` | '_/ _| ' \  | |\/| / -_) '  \/ _ \ '_| / -_|_-<
# |___/\___\__,_|_| \__|_||_| |_|  |_\___|_|_|_\___/_| |_\___/__/
print("Loading embedding model")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
print("Embedding model loaded")


def search_memory(query: str, top_k=4):
    query_embedding = embedding_model.encode([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding.tolist()], n_results=top_k
    )
    memories = [
        f"[{meta['timestamp']}] {doc}"
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]
    return memories


#  _____ _              _                __  __
# |_   _(_)_ __  ___ __| |_ _ __  _ __  |  \/  |___ ______ __ _
#   | | | | '  \/ -_|_-<  _| '  \| '_ \ | |\/| / -_|_-<_-</ _` |
#   |_| |_|_|_|_\___/__/\__|_|_|_| .__/ |_|  |_\___/__/__/\__, |
#                                |_|                      |___/
def timestamped_message(role, content):
    now = datetime.now().isoformat()
    return {"role": role, "content": content, "metadata": {"timestamp": now}}


#  __  __                           ___ _ _
# |  \/  |___ _ __  ___ _ _ _  _   / __| (_)_ __ _ __  ___ _ _
# | |\/| / -_) '  \/ _ \ '_| || | | (__| | | '_ \ '_ \/ -_) '_|
# |_|  |_\___|_|_|_\___/_|  \_, |  \___|_|_| .__/ .__/\___|_|
#                           |__/           |_|  |_|
def clip_history(messages, keep_turns=100):
    sys_count = 1
    persistent_count = sum(
        1
        for msg in messages[1:]
        if msg["role"] == "system" and "Relevant memory" in msg["content"]
    )
    start_index = sys_count + persistent_count

    conv_history = messages[start_index:]
    if len(conv_history) > keep_turns * 2:
        conv_history = conv_history[-keep_turns * 2 :]

    return messages[:start_index] + conv_history


#   ___ _         _     _    _    __  __
#  / __| |_  __ _| |_  | |  | |  |  \/  |
# | (__| ' \/ _` |  _| | |__| |__| |\/| |
#  \___|_||_\__,_|\__| |____|____|_|  |_|
def chat_llm():
    global messages
    text_buffer = ""
    final_response = ""

    response: ChatResponse = chat(
        "qwen3",
        tools=[save_tool, emotion_tool, animation_tool, google_tool],
        messages=messages,
        think=False,
    )

    if response.message.tool_calls:
        for tool in response.message.tool_calls:
            if function_to_call := available_functions.get(tool.function.name):
                output = function_to_call(**tool.function.arguments)
            else:
                print("Function", tool.function.name, "Not Found Error 404")

            if response.message.tool_calls:
                messages.append(response.message)
                messages.append(
                    {"role": "tool", "content": str(output), "name": tool.function.name}
                )
        print("\n")
        for part in chat("qwen3", messages=messages, stream=True, think=False):
            text_buffer += part["message"]["content"]
            final_response += part["message"]["content"]
            print(part["message"]["content"], end="", flush=True)
            sentences = sentence_splitter(text_buffer)
            for sent in sentences:
                sent = sent.strip()
                if sent and sent not in spoken_sentences:
                    tts_queue.put(sent)
                    time.sleep(0.1)
                    text_buffer = text_buffer.replace(sent, "", 1)
    messages.append(timestamped_message("assistant", final_response))
    messages = clip_history(messages)


#  ___    _ _       _____     _ _   _
# |_ _|__| | |___  |_   _|_ _| | |_(_)_ _  __ _
#  | |/ _` | / -_)   | |/ _` | | / / | ' \/ _` |
# |___\__,_|_\___|   |_|\__,_|_|_\_\_|_||_\__, |
#                                         |___/
SILENCE_THRESHHOLD = 60
COOLDOWN = 20

last_user_input = time.time()
waiting_to_talk = False


def idle_monitor():
    global messages
    print("idle monitor started")
    global waiting_to_talk, last_user_input
    while True:
        time_since_input = time.time() - last_user_input
        if time_since_input >= SILENCE_THRESHHOLD and not waiting_to_talk:
            print("user has been silent")
            waiting_to_talk = True
            if random.random() > 0.1:
                messages.append(
                    timestamped_message("system", "user has been silent for a minute")
                )
                chat_llm()
                waiting_to_talk = False
                last_user_input = time.time()
            time.sleep(120)


threading.Thread(target=idle_monitor, daemon=True).start()


#  __  __      _        _
# |  \/  |__ _(_)_ _   | |   ___  ___ _ __
# | |\/| / _` | | ' \  | |__/ _ \/ _ \ '_ \
# |_|  |_\__,_|_|_||_| |____\___/\___/ .__/
#                                    |_|
while True:
    print("\n")
    user_input_text = input()
    last_user_input = time.time()
    waiting_to_talk = False
    recalled_memories = search_memory(user_input_text)
    memory_messages = [
        {"role": "system", "content": "Relevant memory: " + mem}
        for mem in recalled_memories
    ]
    messages = [messages[0]] + memory_messages + messages[1:]
    messages.append(timestamped_message("user", user_input_text))
    chat_llm()
