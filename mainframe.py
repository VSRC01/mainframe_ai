import time
import requests
import speech_recognition as sr
import pyaudio
import wave
import keyboard
import time
import socket
import threading
import json
import queue
import re
import time
import math

from playsound import playsound
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.llms import Ollama
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play
from langchain.vectorstores import Chroma
from langchain.embeddings.base import Embeddings
from langchain.docstore.document import Document
from langchain_community.vectorstores.utils import filter_complex_metadata

# ----------- MAIN FUNCTION -----------

def main():
    print("Loading embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vectorstore = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )   

    memory = MemoryManager(db=vectorstore, embeddings=embeddings)

    print("Booting up Mainframe (Ollama)...")
    llm = Ollama(model="mainframe:latest")

    print("Mainframe Online. Say 'exit' to stop.")

    audio_queue = queue.Queue()
    buffer = ""
    full_response = ""
    def audio_thread():
        while True:
            text = audio_queue.get()
            if not text:
                continue
            print(f"[TTS] Speaking: {text.strip()}")
            if synthesize_speech(text.strip()):
                play_audio()
            else:
                print("Failed to generate voice.")

    threading.Thread(target=audio_thread, daemon=True).start()
    chat_history = []
    while True:
        user_text = listen_push_to_talk()
        if not user_text:
            continue
        if user_text.lower() in ["exit", "quit", "stop"]:
            print("Shutting down Mainframe...")
            vectorstore.persist()
            break
        
        chat_history_formatted = "\n".join([f"User said: {u}. assistant responded:{a}" for u, a in chat_history])
        context_memories = memory.retrieve(user_text, top_k=5)
        context = "\n".join([m.page_content for m in context_memories])
        
        full_prompt = (f"""#prompt:{user_text}, \n\n #memories: {context}, \n\n #chat history: {chat_history_formatted}""")
        print(full_prompt)
        print("[Mainframe] Streaming response...")
        response_iter = llm.stream(full_prompt)

        for chunk in response_iter:
            buffer += chunk
            full_response += chunk
            sentences = sentence_splitter(buffer)

            for sent in sentences:
                audio_queue.put(sent)
                buffer = buffer.replace(sent, "", 1)  # Remove sent from buffer

        memory.save_memory(f"User said: {user_text}, assistant responded: {full_response}", score=0.5, memory_type= "chat")
        chat_history.append((user_text,full_response))
        if len(chat_history) > 5:
            chat_history.pop(0)


if __name__ == "__main__":
    main()