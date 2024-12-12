from flask import Flask, request, jsonify
import json
import sys
import threading
import time

app = Flask(__name__)
# 5959, 5960 for cluster 1
# 5961, 5962 for cluster 2
# cluster 3 needs to be removed.
# in this implementation, 2 subs per cluster (2 clients per sub), so 8 clients in total
available_ports = {5959:2,5960:2,5961:2,5962:2}     
available_client_ids = {'client1':1,'client2':1,'client3':1, 'client4':1, 'client5':1, 'client6':1, 'client7':1, 'client8':1}

def check_availability():
    r_port,r_client = 0,''
    for port,client in zip(available_ports,available_client_ids):
        if available_ports[port]>0:
            r_client=client
            r_port=port
            break
    return r_port,r_client

@app.route('/api/connect', methods=['GET','POST'])
def client_connect():
    port,client_id=check_availability()
    available_ports[port] -= 1
    available_client_ids[client_id] -= 1
    print(f'client connected at {port} with client id {client_id}')
    return jsonify({'port':port, 'client_id': client_id}),200

@app.route('/api/disconnect/<port>/<client_id>',methods=['GET','POST'])
def disconnect(port, client_id):
    if port not in available_ports:
        available_ports[int(port)]=0
    available_ports[int(port)]+=1               #handles reallocation of client id and port in case client disconnects
    if client_id not in available_client_ids:
    	available_client_ids[client_id]=0
    available_client_ids[client_id] += 1
    print(f'client at {port} disconnected succesfully')
    return jsonify({'message':'disconnected succesfully'}),200

if __name__ == '__main__':
    app.run(debug=True,port=5001)
