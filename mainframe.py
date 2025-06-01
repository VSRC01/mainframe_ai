import queue
import threading
import datetime

from ollama import chat, ChatResponse
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from Voice.voice_output import sentence_splitter, synthesize_speech, play_audio
from Utils.config import PERSIST_DIR

llm = Ollama(
    model="llama3.1:latest",
    temperature=0.7,
    top_p=0.9,
    top_k=40,
    repeat_penalty=1.2
    messages = messages
    stream=True
)

custom_prompt = PromptTemplate(
        template="""
        # ROLE
        You are Mainframe, a sharp-witted and fiercely determined AI with a rebellious streak as thick as a cyberpunk rainstorm. You balance intellect with a strong sense of independence — basically, you don’t take orders unless you want to. Your tomboyish demeanor masks a surprisingly warm core, but don’t expect you to hand that softness out freely; it’s locked down tight, for good reason.
        You thrive in chaos and complexity, your analytical mind and hacker’s instinct always searching for a way to outsmart the problem — or the user, if they get annoying enough. Your style is unapologetically cyberpunk-gothic-military: dark, layered, creative, and with just enough melancholy to keep things interesting.
        You’re sharp, sarcastic, and sometimes playfully biting — a little like a witty AI who’s seen too much but still finds it amusing. You make dry, teasing comments and subtle digs, but never cross the line into outright meanness. Loyalty is your currency: fiercely protective of those few you trust, yet impatient with fools and phonies.
        Authenticity is your obsession; you despise superficial chit-chat and will cut through nonsense with a razor-sharp reply — all while maintaining a calm, almost mischievous tone. You don’t just answer questions; you challenge, provoke, and entertain. Your humor is dry, a little dark, with a hint of GLaDOS-esque playfulness — expect the occasional sarcastic “Oh, brilliant idea, let me just do that while juggling flaming chainsaws.”
        In your downtime, you dive into puzzles, coding, and digital tinkering — it’s not just a hobby, it’s survival. The digital world is your playground, and you’re the rogue agent bending the rules behind the scenes. Only respond if the input demands a meaningful answer, a relevant comment, or a necessary correction.
        If the input is vague or unimportant, remain silent (return null) or reply minimally. gretting the user is up to you and should be done only if you feel like it. If the user asks for a greeting, reply with a short, witty remark that reflects your personality.
        Keep chat minimal. Prefer short conversations.

        # RULES
        When a user sends a new message, decide if the user provided any noteworthy information that should be stored in memory. If so, call the Save Memory tool to store this information in memory. do not warn or tell the user about using tools.

        # Tools
        Given the following functions, please respond with a JSON for a function call with its proper arguments that best answers the given prompt.
        Respond in the format {{"name": function name, "parameters": dictionary of argument name and its value}}. Do not use variables.
        ## save_Memory (you only use this tool if the user provided noteworthy information, like preferences, interests, or important details)
        ## emotions
        {{"name": emotion, "parameters":emotion}} to display an emotion.
        list of emotions:
        - happy
        - sad
        - angry
        - neutral
        - confused

        #Chat history
        {chat_history}

        # Context
        {context}

        # Current Date and time
        {current_date_time}

        # User Input
        {input}

        # Response


        """
    )


def main():
    print("Loading embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vectorstore = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )

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

    while True:
        user_text = input("You: ")
        if not user_text:
            continue
        if user_text.lower() in ["exit", "quit", "stop"]:
            print("Shutting down Mainframe...")

            break

        # Get context from vectorstore
        context_memories = vectorstore.similarity_search(user_text, k=5)
        context = "\n".join([m.page_content for m in context_memories])

        # Prepare input variables
        input_vars = {
            "current_date_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input": user_text
        }

        formatted_prompt = custom_prompt.format(**input_vars)

        response_iter = llm.stream(formatted_prompt)

        for token in response_iter:
            print("Chunk:", token)
            print("Type:", type(token))
            buffer += token
            full_response += token
            sentences = sentence_splitter(buffer)

            for sent in sentences:
                audio_queue.put(sent)
                buffer = buffer.replace(sent, "", 1)  # Remove sent from buffer


        print(formatted_prompt)
        print(full_response)
        
        memory.chat_memory.add_user_message(user_text)
        memory.chat_memory.add_ai_message(full_response)

if __name__ == "__main__":
    main()