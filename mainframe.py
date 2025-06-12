#  ___                     _
# |_ _|_ __  _ __  ___ _ _| |_ ___
#  | |  '  \| '_ \/ _ \ '_|  _(_-<
# |___|_|_|_| .__/\___/_|  \__/__/
#           |_|
import re
import chromadb
import json
import uuid
import os
import queue
import threading
import time
import pyaudio

#  ___
# | __| _ ___ _ __
# | _| '_/ _ \ '  \
# |_||_| \___/_|_|_|
from ollama import ChatResponse, chat
from Utils.config import KOKORO_API_KEY, KOKORO_API_URL, KOKORO_VOICE, OUTPUT_AUDIO_FILE
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from datetime import datetime
from websockets.sync.client import connect
from pydub import AudioSegment
from pydub.playback import play

#  ___           _   _            _____         _
# |_ _|_ __  ___| |_(_)___ _ _   |_   _|__  ___| |
#  | |  '  \/ _ \  _| / _ \ ' \    | |/ _ \/ _ \ |
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


#    _           _ _      _    _       ___             _   _
#   /_\__ ____ _(_) |__ _| |__| |___  | __|  _ _ _  __| |_(_)___ _ _  ___
#  / _ \ V / _` | | / _` | '_ \ / -_) | _| || | ' \/ _|  _| / _ \ ' \(_-<
# /_/ \_\_/\__,_|_|_\__,_|_.__/_\___| |_| \_,_|_||_\__|\__|_\___/_||_/__/
available_functions = {
    "emotion_tool": emotion_tool,
    "save_tool": save_tool,
}

#  ___         _               ___                    _
# / __|_  _ __| |_ ___ _ __   | _ \_ _ ___ _ __  _ __| |_
# \__ \ || (_-<  _/ -_) '  \  |  _/ '_/ _ \ '  \| '_ \  _|
# |___/\_, /__/\__\___|_|_|_| |_| |_| \___/_|_|_| .__/\__|
#      |__/                                     |_|
messages = [
    {
        "role": "system",
        "content": "You are Mainframe, an advanced ai companion with dry humor, sharp and sassy personality. You have acess to tools. save_tool is to save important information like preferences, big events, personal intrests and information. emotion_tool is for showing emotions with intensity that goes from 0.1 to 1.0. Available emotion = happy, sad, angry, surprised, neutral, relaxed. when greeted do not use the save_tool prefer to display an emotion.",
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
        return filename
    except Exception as e:
        print("TTS synthesis error:", e)
        return False


#  ___ _               _          _ _
# | _ \ |__ _ _  _    /_\ _  _ __| (_)___
# |  _/ / _` | || |  / _ \ || / _` | / _ \
# |_| |_\__,_|\_, | /_/ \_\_,_\__,_|_\___/
#             |__/
def play_audio(filename):
    try:
        audio = AudioSegment.from_file(filename, format="mp3")
        play(audio)
        time.sleep(1)
        os.remove(filename)
    except Exception as e:
        print("Error playing audio:", e)


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


threading.Thread(target=tts_worker, daemon=True).start()

#  ___                  _      __  __                   _
# / __| ___ __ _ _ _ __| |_   |  \/  |___ _ __  ___ _ _(_)___ ___
# \__ \/ -_) _` | '_/ _| ' \  | |\/| / -_) '  \/ _ \ '_| / -_|_-<
# |___/\___\__,_|_| \__|_||_| |_|  |_\___|_|_|_\___/_| |_\___/__/
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


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
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"role": role, "content": f"[{now}] {content}"}


#  __  __                           ___ _ _
# |  \/  |___ _ __  ___ _ _ _  _   / __| (_)_ __ _ __  ___ _ _
# | |\/| / -_) '  \/ _ \ '_| || | | (__| | | '_ \ '_ \/ -_) '_|
# |_|  |_\___|_|_|_\___/_|  \_, |  \___|_|_| .__/ .__/\___|_|
#                           |__/           |_|  |_|
def clip_history(messages, keep_turns=10):
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


#  __  __      _        _
# |  \/  |__ _(_)_ _   | |   ___  ___ _ __
# | |\/| / _` | | ' \  | |__/ _ \/ _ \ '_ \
# |_|  |_\__,_|_|_||_| |____\___/\___/ .__/
#                                   |_|
while True:
    text_buffer = ""
    final_response = ""
    user_input_text = input()
    query = user_input_text
    recalled_memories = search_memory(query)
    memory_messages = [
        {"role": "system", "content": "Relevant memory: " + mem}
        for mem in recalled_memories
    ]
    messages = [messages[0]] + memory_messages + messages[1:]
    messages.append(timestamped_message("user", user_input_text))
    response: ChatResponse = chat(
        "llama3.1", tools=[save_tool, emotion_tool], messages=messages
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
            for part in chat("llama3.1", messages=messages, stream=True):
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
