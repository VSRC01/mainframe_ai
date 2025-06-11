from websocket_server import WebsocketServer

clients = []


# Called for every client connecting
def new_client(client, server):
    clients.append(client)
    print(f"Client {client['id']} connected.")


# Called when a client disconnects
def client_left(client, server):
    clients.remove(client)
    print(f"Client {client['id']} disconnected.")


# Called when a client sends a message
def message_received(client, server, message):
    print(f"Received from {client['id']}: {message}")

    # Broadcast to all clients except sender
    for other_client in clients:
        if other_client != client:
            server.send_message(other_client, message)


def start_emotion_server():
    server = WebsocketServer(host="localhost", port=6543, loglevel=1)
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)

    print("Emotion server running on ws://localhost:6543")
    server.run_forever()


if __name__ == "__main__":
    try:
        start_emotion_server()
    except KeyboardInterrupt:
        print("Server stopped.")
