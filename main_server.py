from flask import Flask, request, jsonify
import json
import sys
from kafka import KafkaProducer
import threading
import time
#import requests

producer = KafkaProducer(
	key_serializer=lambda v: json.dumps(v).encode('utf-8'),
	value_serializer = lambda m: json.dumps(m).encode('utf-8')   #passes the data as a dictionary
	)

available_ports = [5959, 5960, 5961, 5962]

topic = 'spark_consumer'   # same topic in the consumer

app = Flask(__name__)

# In-memory storage for the data (use a database for production)
emoji_data = []
emoji_count = {}

@app.route('/api/emoji', methods=['POST'])
def receive_emoji():
    data = request.get_json()

    if not all(key in data for key in ("user_id", "emoji_type", "timestamp")):
        return jsonify({"error": "Missing required fields"}), 400

    user_id = data["user_id"]
    emoji_type = data["emoji_type"]
    timestamp = data["timestamp"]

    emoji_data.append({
        "user_id": user_id,
        "emoji_type": emoji_type,
        "timestamp": timestamp
    })
    
    if user_id in emoji_count:
        emoji_count[user_id] += 1
    else:
        emoji_count[user_id] = 1

    # add time code here, every 500ms, flush all inputs and reset the emoji data variable 
    
    #producer.send(topic,emoji_data)        #passes the data as a list of dicts, can be easily parsed as a spark dataframe 
    #emoji_data = []                         in the consumer					
    #producer.flush()
    
    
    
    #print(emoji_data)      #this is not required...

    return jsonify({"message": "Emoji data received"}), 200

# Function to flush emoji data every 500 milliseconds
def flush_emoji_data():
    while True:
        time.sleep(0.5)  # Wait for 500 milliseconds
        if emoji_data:
            producer.send(topic, emoji_data)
            producer.flush()
            emoji_data.clear()  # Clear the list after sending
    
@app.route('/api/close', methods=['POST'])
def close_connection():
	data = request.get_json() 		#route can be used later to handle graceful closing of user connection
	return 

# @app.route('/api/connect', methods=['GET','POST'])
# def client_connect():
#     port = available_ports[0]
#     available_ports.remove(port)                 # This is in case the /api/emoji route doesnt work for port selection
#     print('client connected at port',port)
#     return 1
    
if __name__ == '__main__':
    # Start the background thread
    flush_thread = threading.Thread(target=flush_emoji_data, daemon=True)
    flush_thread.start()
    app.run(debug=True)
