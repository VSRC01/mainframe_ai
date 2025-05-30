# ----------- VOICE INPUT -----------

def listen_to_mic(timeout=20, phrase_time_limit=40):
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.8
    recognizer.energy_threshold = 300
    with sr.Microphone() as source:
        print("Listening... Speak now.")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"Speech recognition error: {e}")
        return ""
    
#------------ press key to talk ------------

def listen_push_to_talk(key='backslash', timeout=20, phrase_time_limit=40):
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.8
    recognizer.energy_threshold = 300
    p = pyaudio.PyAudio()

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    WAVE_OUTPUT_FILENAME = "ptt_audio.wav"

    print(f"Press and hold '{key}' to talk...")

    while True:
        if keyboard.is_pressed(key):
            print("Recording...")
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)
            frames = []
            while keyboard.is_pressed(key):
                data = stream.read(CHUNK)
                frames.append(data)
            stream.stop_stream()
            stream.close()
            print("Stopped recording")

            wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            with sr.AudioFile(WAVE_OUTPUT_FILENAME) as source:
                audio = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
            except sr.UnknownValueError:
                print("Could not understand audio.")
                return ""
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")
                return ""
        else:
            time.sleep(0.1)
