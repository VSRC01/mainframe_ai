#---------------- minecraft input -------------

def handle_minecraft_input(message):
    try:
        data = json.loads(message)
        event_type = data.get("event", "unknown")

        # Simple example: convert to text question
        if event_type == "chat":
            username = data.get("username", "Unknown")
            msg = data.get("message", "")
            input_text = f"Player {username} said: {msg}"
        else:
            input_text = f"Minecraft event: {event_type} - {data}"

        print(f"[MC-EVENT] {input_text}")
        chat_history.append((input_text, ""))  # Temporary history update

        # Run it through the Mainframe
        response = qa_chain.run({"question": input_text, "chat_history": chat_history})
        chat_history[-1] = (input_text, response)  # Replace with real response

        print(f"Mainframe: {response}")
        if synthesize_speech(response):
            play_audio()
        else:
            print("Failed to generate voice.")
    except Exception as e:
        print(f"[Mainframe][MC Error] {e}")
