from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI()

# Allow connections from any origin (so your Flet frontend can connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# List to keep track of connected clients
clients = []

# --------- WebSocket endpoint for chat ---------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()  # accept connection
    clients.append(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            # Broadcast message to all connected clients
            for client in clients:
                await client.send_text(data)
    except WebSocketDisconnect:
        # Remove client if disconnected
        clients.remove(websocket)

# --------- Optional HTTP route to confirm server is running ---------
@app.get("/")
async def root():
    return {"message": "FastAPI server is online!"}
