import requests 
import random
import time
import threading
from datetime import datetime
import websockets
import asyncio
import json
from websockets.exceptions import ConnectionClosed
from websockets.client import WebSocketClientProtocol

# API endpoints remain the same
API_ENDPOINT = "http://127.0.0.1:5000/api/emoji"
PORT_CONNECTION_ENDPOINT = "http://127.0.0.1:5001/api/connect"        #url when client tries to connect
PORT_DISCONNECT_ENDPOINT = "http://127.0.0.1:5001/api/disconnect"     #url when client disconnects (send back port and id to be repurposed)

# Emojis list and counter setup
emojis = ["😂", "😭", "😎", "🥳", "👍", "🔥"]
total_emojis_sent = 0
counter_lock = threading.Lock()
should_reconnect = True   #this is in case of errors, the client tries to reconnect to the websocket
websocket_connected = threading.Event()  # To track websocket connection status

#this function is to query the dhcp to get a new port and client id
def connect():
    try:
        response = requests.get(PORT_CONNECTION_ENDPOINT)
        if response.status_code == 200:
            print("Response received successfully:")
            print(response.json())
            port = response.json()['port']
            client_id = response.json()['client_id']
            return port, client_id 
        else:
            print(f"Request failed with status code: {response.status_code}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None, None

async def keep_alive(websocket: WebSocketClientProtocol):     
    while True:
        try:
            await websocket.ping()      #this function sends periodic heartbeats, so that it doesnt terminate connection
            await asyncio.sleep(20)     #due to inactivity
        except Exception as e:
            print(f"Keep-alive error: {e}")
            break

async def websocket_listener(port):
    global should_reconnect
    websocket_url = f"ws://127.0.0.1:{port}"
    
    while should_reconnect:
        try:
            async with websockets.connect(
                websocket_url,
                ping_interval=None,    # We'll handle pings manually
                ping_timeout=None,     # Disable ping timeout
                close_timeout=10,      # 10 seconds for graceful shutdown
                max_size=None         # No message size limit
            ) as websocket:
                print(f"Connected to WebSocket server at {websocket_url}")
                websocket_connected.set()  # Signal that connection is established
                
                keep_alive_task = asyncio.create_task(keep_alive(websocket)) # start the keep alive heartbeat function
                
                try:
                    while True:
                        try:
                            message = await websocket.recv()
                            message = json.loads(message)
                            # Actual output received
                            # print(f"Message received: {message}")
                            final_output = ''.join(emoji1 * count1 for emoji1,count1 in message.items())
                            print(f"Received message: {final_output}")
                        except ConnectionClosed:
                            print("Connection closed by server")
                            break
                        except Exception as e:
                            print(f"Error receiving message: {e}")
                            break
                finally:
                    keep_alive_task.cancel()
                    websocket_connected.clear()
                    
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            websocket_connected.clear()
        
        if should_reconnect:
            print("Attempting to reconnect in 5 seconds...")
            await asyncio.sleep(5)

def start_websocket_listener(port):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(websocket_listener(port))        #no changes to the websocker listener here
    finally:                                                     #asyncio.Future in the sub, and the keep-alive keep the connection forever
        loop.close()

def send_emoji(user_id):
    global total_emojis_sent
    
    # Wait for WebSocket connection before sending emojis
    if not websocket_connected.wait(timeout=10):
        print("Warning: WebSocket not connected, but continuing to send emojis")
    
    current_time = datetime.now()
    formatted_time = current_time.strftime("%H:%M:%S.%f %d-%m-%Y")
    emoji_data = {
        "user_id": user_id,
        "emoji_type": random.choice(emojis),          #emoji message format
        "timestamp": formatted_time
    }
    
    try:
        response = requests.post(API_ENDPOINT, json=emoji_data)
        if response.status_code == 200:
            with counter_lock:
                total_emojis_sent += 1
        else:
            print(f"[User {user_id}] Failed to send emoji. Status Code: {response.status_code}")
    except Exception as e:
        print(f"[User {user_id}] Error sending emoji: {e}")

def client_emojis(user_id, rate_per_sec=200, duration_sec=5):
    end_time = time.time() + duration_sec
    while time.time() < end_time:
        send_emoji(user_id)                     #new logic to send emojis, same rate of sending
        time.sleep(1 / rate_per_sec)

def spawn_threads(user_id, num_threads, rate_per_sec, duration_sec):
    threads = []

    websocket_thread = threading.Thread(
        target=start_websocket_listener,
        args=(port,),
        daemon=True
    )
    websocket_thread.start()
    threads.append(websocket_thread)

    for i in range(num_threads):
        thread = threading.Thread(
            target=client_emojis,
            args=(user_id, rate_per_sec, duration_sec)
        )
        thread.start()
        threads.append(thread)

    # Wait for emoji sender threads to finish
    for thread in threads[1:]:  #[1:] because the first thread is the websocket thread, so it keeps the connection alive 
        thread.join()           #even after the sending threads are complete, in case other clients havent finished sending

def close_connection(port, client_id):
    global should_reconnect
    should_reconnect = False
    try:
        response = requests.post(f'{PORT_DISCONNECT_ENDPOINT}/{port}/{client_id}')
        if response.status_code == 200:
            print("Successfully disconnected from server")                  #all error handling done by claude
        else:
            print(f"Error disconnecting: Status code {response.status_code}")
    except Exception as e:
        print(f"Error during disconnection: {e}")
    time.sleep(2)  #this is for gracefull disconnection

if __name__ == "__main__":
    start_time = time.time()
    x = input("Do you want to connect to the server? y/n: ")
    
    if x == "y":
        port, client_id = connect()
        if port and client_id:
            print("port returned: ", port)
            try:
                spawn_threads(user_id=client_id, num_threads=1, rate_per_sec=400, duration_sec=600)
            except KeyboardInterrupt:
                print("\nShutting down gracefully...")   #ctrl+C only to exit, but it handles the disconnection gracefully at least
            finally:
                end_time = time.time()
                print(f"\nTotal emojis sent: {total_emojis_sent}")
                print(f"Time taken: {end_time - start_time} seconds")
                close_connection(port, client_id)
        else:
            print("Failed to connect to server")
    else:
        print("You have chosen not to participate in the emoji stream!")