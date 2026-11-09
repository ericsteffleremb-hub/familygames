"""
import socket
import json

HOST = "0.0.0.0"      # Listen on all interfaces
PORT = 5000

game_state = {"board": [[".",".","."],
                        [".",".","."],
                        [".",".","."]]}

def handle_message(msg):
    data = json.loads(msg)
    # Example: update board position
    x, y = data["x"], data["y"]
    game_state["board"][y][x] = data["piece"]
    return json.dumps(game_state)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("Server waiting for connection...")
    conn, addr = s.accept()
    print("Connected:", addr)

    with conn:
        while True:
            msg = conn.recv(1024).decode()
            if not msg:
                break
            print("Received:", msg)
            updated = handle_message(msg)
            conn.sendall(updated.encode())
"""

import ngrok
 
def start_ngrok():
    listener = ngrok.forward(5000, "tcp", authtoken_from_env=True)
    print("Public TCP address:", listener.url())
    return listener
 

import time
import socket
import threading
import json

from FamilyGame import generate_hex_rings
clients = []
tiles = generate_hex_rings()   # your tile list (HexTile objects)
RobberIndex = 0

def broadcast(message):
    data = json.dumps(message).encode()
    for c in clients:
        print(c, data)
        try:
            c.sendall(data + b"\n")
        except:
            pass

def handle_client(conn, addr):
    print("Client connected:", addr)
    clients.append(conn)

    try:
        while True:
            raw = conn.recv(4096)
            if not raw:
                break

            for line in raw.split(b"\n"):
                if not line.strip():
                    continue

                msg = json.loads(line.decode())

                if msg["type"] == "request_full_state":
                    print("recieved request_full_state")
                    broadcast({
                        "type": "full_state",
                        "tiles": [t.to_dict() for t in tiles]
                    })

                elif msg["type"] == "update_tile":
                    # update server tile
                    for t in tiles:
                        if t.q == msg["tile"]["q"] and t.r == msg["tile"]["r"]:
                            t.color_index = msg["tile"]["color_index"]
                            t.number = msg["tile"]["number"]
                            t.edge_pieces = msg["tile"]["edge_pieces"]
                            t.vertex_pieces = msg["tile"]["vertex_pieces"]

                    # broadcast update to all clients
                    broadcast(msg)
                elif msg["type"] == "RI":
                    global RobberIndex
                    RobberIndex = msg["I"]
                    broadcast(msg)
                elif msg["type"] == "SN":
                    tiles[msg["I"]].SetNumber(msg["N"])
                    broadcast(msg)
                elif msg["type"] == 1: 
                    print("recieved alive ", addr)

    finally:
        print("Client disconnected:", addr)
        clients.remove(conn)
        conn.close()
def KeepAlive():
    """Thread B: produces items and puts them in the queue."""
    print("Start keep alive thread")
    global clients
    while True:
        if 0 != len(clients):
            broadcast({
                "type": 1,
            })
            print("Keep alive...")
        time.sleep(15)         # simulate data arriving over time
def main():
    #start_ngrok()
    t1 = threading.Thread(target=KeepAlive, daemon=True)
    t1.start()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5000))
    server.listen()

    print("Server running on port 5000")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
