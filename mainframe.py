#  ___                     _
# |_ _|_ __  _ __  ___ _ _| |_ ___
# | || '  \| '_ \/ _ \ '_|  _(_-<
# |___|_|_|_| .__/\___/_|  \__/__/
#           |_|
import re
import json

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


# ___                          _   _____         _
# | _ \___ ____ __  ___ _ _  __| | |_   _|__  ___| |
# |   / -_|_-< '_ \/ _ \ ' \/ _` |   | |/ _ \/ _ \ |
# |_|_\___/__/ .__/\___/_||_\__,_|   |_|\___/\___/_|
#           |_|
def respond_tool(response):
    print(response)
    return response


#  __  __                          _____         _
# |  \/  |___ _ __  ___ _ _ _  _  |_   _|__  ___| |
# | |\/| / -_) '  \/ _ \ '_| || |   | |/ _ \/ _ \ |
# |_|  |_\___|_|_|_\___/_|  \_, |   |_|\___/\___/_|
def save_tool(sumarized):
    print("Memory:", sumarized)


#    _           _ _      _    _       ___             _   _
#   /_\__ ____ _(_) |__ _| |__| |___  | __|  _ _ _  __| |_(_)___ _ _  ___
#  / _ \ V / _` | | / _` | '_ \ / -_) | _| || | ' \/ _|  _| / _ \ ' \(_-<
# /_/ \_\_/\__,_|_|_\__,_|_.__/_\___| |_| \_,_|_||_\__|\__|_\___/_||_/__/
available_functions = {
    "respond_tool": respond_tool,
    "emotion_tool": emotion_tool,
    "save_tool": save_tool,
}

#  __  __         _     _    ___           __ _
# |  \/  |___  __| |___| |  / __|___ _ _  / _(_)__ _
# | |\/| / _ \/ _` / -_) | | (__/ _ \ ' \|  _| / _` |
# |_|  |_\___/\__,_\___|_|  \___\___/_||_|_| |_\__, |
#                                              |___/
model_config = {
    "model": "llama3.1",
    "stream": True,
    "tools": [respond_tool, save_tool, emotion_tool],
}
#  ___         _               ___                    _
# / __|_  _ __| |_ ___ _ __   | _ \_ _ ___ _ __  _ __| |_
# \__ \ || (_-<  _/ -_) '  \  |  _/ '_/ _ \ '  \| '_ \  _|
# |___/\_, /__/\__\___|_|_|_| |_| |_| \___/_|_|_| .__/\__|
#      |__/                                     |_|
messages = [
    {
        "role": "system",
        "content": "You are Mainframe, an advanced ai companion with dry humor, sharp and sassy personality. You have acess to tools. respond_tool is for talking to the user. save_tool is to save important information like preferences, big events, personal intrests and information. emotion_tool is for showing emotions with intensity that goes from 0 to 1.0. Available emotion = happy, sad, angry, surprised, neutral.",
    }
]

#  __  __      _        _
# |  \/  |__ _(_)_ _   | |   ___  ___ _ __
# | |\/| / _` | | ' \  | |__/ _ \/ _ \ '_ \
# |_|  |_\__,_|_|_||_| |____\___/\___/ .__/
#                                   |_|
while True:
    user_input = [{"role": "user", "content": input()}]
    messages += user_input
    response = chat(**model_config, messages=messages)

    final_response = ""

    tool_calls = []
    tool_response = None

    for part in response:
        msg = part.get("message", {})
        if "content" in msg:
            print(msg["content"], end="", flush=True)
            final_response += msg["content"]

        if "tool_calls" in msg:
            tool_calls.extend(msg["tool_calls"])
    for tool in tool_calls:
        function_name = tool["function"]["name"]
        arguments = tool["function"]["arguments"]

        if function_to_call := available_functions.get(function_name):
            result = function_to_call(**arguments)
            if function_name == "respond_tool":
                tool_response = result
    if final_response:
        messages += [{"role": "assistant", "content": final_response}]

    if tool_response:
        messages += [{"role": "assistant", "content": tool_response}]
    print(messages)
