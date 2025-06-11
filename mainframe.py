#  ___                     _
# |_ _|_ __  _ __  ___ _ _| |_ ___
# | || '  \| '_ \/ _ \ '_|  _(_-<
# |___|_|_|_| .__/\___/_|  \__/__/
#           |_|
import re

#  ___
# | __| _ ___ _ __
# | _| '_/ _ \ '  \
# |_||_| \___/_|_|_|
from ollama import ChatResponse, chat
from Utils.config import KOKORO_API_KEY, KOKORO_API_URL, KOKORO_VOICE, OUTPUT_AUDIO_FILE
from pydub import AudioSegment
from pydub.playback import play
from openai import OpenAI


#  ___           _   _            _____         _
# | __|_ __  ___| |_(_)___ _ _   |_   _|__  ___| |
# | _|| '  \/ _ \  _| / _ \ ' \    | |/ _ \/ _ \ |
# |___|_|_|_\___/\__|_\___/_||_|   |_|\___/\___/_|
def emotion_tool(emotion, intensity):
    print("Emotion: ", emotion, "instensity: ", intensity)
    return ("emotion displayed:", emotion, intensity)


#  __  __                          _____         _
# |  \/  |___ _ __  ___ _ _ _  _  |_   _|__  ___| |
# | |\/| / -_) '  \/ _ \ '_| || |   | |/ _ \/ _ \ |
# |_|  |_\___|_|_|_\___/_|  \_, |   |_|\___/\___/_|
def save_tool(sumarized):
    print("Memory:", sumarized)
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
        "content": "You are Mainframe, an advanced ai companion with dry humor, sharp and sassy personality. You have acess to tools. save_tool is to save important information like preferences, big events, personal intrests and information. emotion_tool is for showing emotions with intensity that goes from 0 to 1.0. Available emotion = happy, sad, angry, surprised, neutral. when greeted do not use the save_tool prefer to display an emotion",
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
def synthesize_speech(text: str, filename=OUTPUT_AUDIO_FILE):
    try:
        with client.audio.speech.with_streaming_response.create(
            model="kokoro", voice=KOKORO_VOICE, input=text, response_format="mp3"
        ) as response:
            response.stream_to_file(filename)
        return True
    except Exception as e:
        print("TTS synthesis error:", e)
        return False


#  ___ _               _          _ _
# | _ \ |__ _ _  _    /_\ _  _ __| (_)___
# |  _/ / _` | || |  / _ \ || / _` | / _ \
# |_| |_\__,_|\_, | /_/ \_\_,_\__,_|_\___/
#             |__/
def play_audio(filename=OUTPUT_AUDIO_FILE):
    try:
        audio = AudioSegment.from_file(filename, format="mp3")
        play(audio)
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


#  __  __      _        _
# |  \/  |__ _(_)_ _   | |   ___  ___ _ __
# | |\/| / _` | | ' \  | |__/ _ \/ _ \ '_ \
# |_|  |_\__,_|_|_||_| |____\___/\___/ .__/
#                                   |_|
while True:
    text_buffer = ""
    final_response = ""
    user_input = [{"role": "user", "content": input()}]
    messages += user_input
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
                final_response += part["message"]["content"]
                print(part["message"]["content"], end="", flush=True)
            sentences = sentence_splitter(final_response)

            for sentence in sentences:
                synthesize_speech(sentence)
                play_audio()
    messages += [{"role": "assistant", "content": final_response}]
