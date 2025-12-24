from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.websocket_manager import manager
from app.restaurant_service import get_restaurant_recommendations
import json

app = FastAPI()

@app.websocket("/ws/location")
async def location_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    await manager.send(websocket, {"status": "connected"})

    try:
        while True:
            message = await websocket.receive()

            text = message.get("text")
            if text is None:
                continue

            text = text.strip()
            if not text:
                continue

            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                await manager.send(websocket, {
                    "error": "Invalid JSON",
                    "received": text
                })
                continue

            lat = data.get("latitude")
            lng = data.get("longitude")

            if lat is None or lng is None:
                await manager.send(websocket, {
                    "error": "latitude and longitude required"
                })
                continue

            restaurants = await get_restaurant_recommendations(lat, lng)

            await manager.send(websocket, {
                "latitude": lat,
                "longitude": lng,
                "count": len(restaurants),
                "recommendations": restaurants
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
