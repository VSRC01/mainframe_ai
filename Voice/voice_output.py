


# ----------- VOICE OUTPUT (KokoroAPI) -----------

client = OpenAI(
    base_url=KOKORO_API_URL,
    api_key=KOKORO_API_KEY,
)

def synthesize_speech(text: str, filename=OUTPUT_AUDIO_FILE):
    try:
        print("Synthesizing voice...")
        with client.audio.speech.with_streaming_response.create(
            model="kokoro",
            voice=KOKORO_VOICE,
            input=text,
            response_format="mp3"
        ) as response:
            response.stream_to_file(filename)
        return True
    except Exception as e:
        print("TTS synthesis error:", e)
        return False

def play_audio(filename=OUTPUT_AUDIO_FILE):
    try:
        audio = AudioSegment.from_file(filename, format="mp3")
        play(audio)
    except Exception as e:
        print("Error playing audio:", e)

# ---------- sentence splitter

def sentence_splitter(text_buffer):
    # Split on punctuation followed by space or end of string
    sentences = re.findall(r'[^.!?]+[.!?]+(?:\s|$)', text_buffer)
    return sentences