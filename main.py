from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = {}
messages = []

AFK_LIMIT = 20 * 60          # 20 minutes
HISTORY_DAYS = 15

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    user = ws.query_params.get("user", "Unknown")

    clients[ws] = {
        "user": user,
        "last_active": datetime.datetime.utcnow()
    }

    join_msg = f"🟢 {user} joined the chat"
    await broadcast(join_msg)

    # Send message history
    now = datetime.datetime.utcnow()
    for msg, ts in messages:
        if (now - ts).days <= HISTORY_DAYS:
            await ws.send_text(msg)

    try:
        while True:
            data = await ws.receive_text()
            clients[ws]["last_active"] = datetime.datetime.utcnow()

            msg = f"{user}: {data}"
            messages.append((msg, datetime.datetime.utcnow()))
            await broadcast(msg)

    except WebSocketDisconnect:
        pass
    finally:
        clients.pop(ws, None)
        leave_msg = f"🔴 {user} left the chat"
        await broadcast(leave_msg)

async def broadcast(message: str):
    for ws in list(clients.keys()):
        try:
            await ws.send_text(message)
        except:
            clients.pop(ws, None)

async def afk_checker():
    while True:
        now = datetime.datetime.utcnow()
        for ws, info in list(clients.items()):
            if (now - info["last_active"]).seconds > AFK_LIMIT:
                try:
                    await ws.send_text("⏰ Disconnected due to inactivity")
                    await ws.close()
                except:
                    pass
                clients.pop(ws, None)
        await asyncio.sleep(30)

@app.on_event("startup")
async def startup():
    asyncio.create_task(afk_checker())

@app.get("/")
def root():
    return {"status": "ROBLOXIAN MSG backend running"}
