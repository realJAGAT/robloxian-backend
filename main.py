from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = {}          # websocket -> username
message_history = []  # (timestamp, message)

HISTORY_DAYS = 15
AFK_SECONDS = 20 * 60


def cleanup_history():
    cutoff = time.time() - HISTORY_DAYS * 86400
    message_history[:] = [m for m in message_history if m[0] >= cutoff]


async def broadcast(message: str):
    message_history.append((time.time(), message))
    cleanup_history()
    for ws in list(clients.keys()):
        await ws.send_text(message)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    username = "Unknown"
    last_active = time.time()

    try:
        # ---- FIRST MESSAGE MUST BE JOIN ----
        join_msg = await websocket.receive_text()
        if join_msg.startswith("__join__:"):
            username = join_msg.split(":", 1)[1]

        clients[websocket] = username

        # send history
        for _, msg in message_history:
            await websocket.send_text(msg)

        await broadcast(f"🟢 {username} joined the chat")

        while True:
            data = await websocket.receive_text()
            last_active = time.time()
            await broadcast(f"{username}: {data}")

    except WebSocketDisconnect:
        clients.pop(websocket, None)
        await broadcast(f"🔴 {username} left the chat")
