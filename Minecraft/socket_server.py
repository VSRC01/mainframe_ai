# ---------------- socket server --------------

def start_mainframe_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 65432))
    server.listen()

    def handle_client(conn):
        with conn:
            buffer = ""
            while True:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    handle_minecraft_input(line.strip())

    def accept_clients():
        while True:
            conn, _ = server.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

    print("[Mainframe] Listening for Minecraft events on port 65432...")
    threading.Thread(target=accept_clients, daemon=True).start()

