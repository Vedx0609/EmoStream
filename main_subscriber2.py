from kafka import KafkaConsumer
import json
import websockets
import asyncio
from websockets.exceptions import ConnectionClosed
import logging
from typing import Set
from datetime import datetime

logging.basicConfig(                   #set the logger
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_TOPIC = 'cluster1'

class WebSocketServer:
    def __init__(self):
        self.consumer = KafkaConsumer(
            INPUT_TOPIC,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),      #setup kafka consumer
            auto_offset_reset='latest',
            enable_auto_commit=True
        )
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.lock = asyncio.Lock()

    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        async with self.lock:                                               #this code basically creates a new client connection
            self.connected_clients.add(websocket)       
            logger.info(f"New client connected. Total clients: {len(self.connected_clients)}")   #keep track of number of clients joined

    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        async with self.lock:
            self.connected_clients.remove(websocket)                       #when client disconnected, the number of connected clients is reduced
            logger.info(f"Client disconnected. Total clients: {len(self.connected_clients)}")

    async def broadcast_messages(self):
        try:
            while True:
                messages = self.consumer.poll(timeout_ms=100)
                if messages:
                    for tp, msgs in messages.items():
                        for message in msgs:
                            data = message.value
                            logger.info(f"Broadcasting message to {len(self.connected_clients)} clients: {data}")
                            
                            # Create copy of set to avoid runtime modification issues
                            async with self.lock: 
                                current_clients = self.connected_clients.copy()
                            
                            for client in current_clients:
                                try:                                            # broadcast message to all the connected clients
                                    await client.send(json.dumps(data, ensure_ascii=False))
                                except Exception as e:
                                    logger.error(f"Error sending to client: {e}")
                                    # Will be removed in handle_client when connection closes

                #this is potentially where the latency is increasing, because the client sends emojis at a rate of 0.005
                await asyncio.sleep(0.01)                  

        except Exception as e:
            logger.error(f"Error in broadcast_messages: {e}")
        finally:
            self.consumer.close()

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        await self.register_client(websocket)
        try:
            # Keep the connection alive
            while True:
                try:
                    # Wait for any message from client (or disconnection)
                    await websocket.recv()
                except ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"Error in client connection: {e}")
                    break
        finally:
            await self.unregister_client(websocket)

async def main():
    server = WebSocketServer()
    
    broadcast_task = asyncio.create_task(server.broadcast_messages())    # Start the broadcasting
    
    async with websockets.serve(
        server.handle_client,
        'localhost',
        5960,                               #hardcoded port for each subscriber
        ping_interval=20,
        ping_timeout=30,
        close_timeout=10
    ) as websocket_server:
        logger.info("WebSocket server started on port 5960")
        try:
            await asyncio.Future()  # this code makes the server connection run forever
        finally:
            broadcast_task.cancel()
            server.consumer.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutting down")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
