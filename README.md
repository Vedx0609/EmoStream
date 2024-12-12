# EMOStream: Concurrent Emoji Broadcast over Event-Driven Architecture

## Project Overview
EMOStream is a distributed, event-driven architecture for real-time emoji broadcasting using Kafka, Spark, and Python.

## Prerequisites
- Python 3.8+
- Apache Kafka
- Apache Spark
- Apache Zookeeper

## System Setup and Deployment

### 1. Clone the Repository
```bash
git clone https://github.com/Cloud-Computing-Big-Data/RR-Team-23-emostream-concurrent-emoji-broadcast-over-event-driven-architecture
cd RR-Team-23-emostream-concurrent-emoji-broadcast-over-event-driven-architecture
```

### 2. Environment Preparation
```bash
# Create Python Virtual Environment
python3 -m venv EmoStream
source EmoStream/bin/activate

# Install Dependencies
pip install -r requirements.txt
```

### 3. Service Initialization
```bash
# Start Zookeeper
sudo systemctl start zookeeper

# Start Kafka
sudo systemctl start kafka

# Create Kafka Topic
/usr/local/kafka/bin/kafka-topics.sh --create --topic cluster1 --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```
similarly for the topic cluster2
```bash
# Start Spark Services
/opt/spark/sbin/start-all.sh

# Verify Services (Optional)
jps  # Check running Java processes
```

### 4. Application Execution

#### Option 1: Manual Execution
```bash
# 2 Split Terminals: Main Servers
python3 main_server.py
python3 main_port_server.py

# 3 New Split Terminals: Publishers and Spark Engine
python3 main_pub_cluster1.py
python3 main_pub_cluster2.py
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3 main_spark_engine.py

# 4 New Split Terminals: Subscribers
python3 main_subscriber1.py
python3 main_subscriber2.py
python3 main_subscriber3.py
python3 main_subscriber4.py

# Terminal 4: Client
python3 main_client.py
```
Each client should be created on a new terminal.
Note that you can create upto 8 clients which connect to the subscribers successfully (architecture limit). Any more clients created from here will not be able to connect to any subscribers successfully, as the subs can only serve 2 clients.
#### Option 2: Bash Script
```bash
# Single command execution
./architecture.sh
```
Here, you may not be able to view all the logs and outputs properly. To view all of them, use Option 1.
## Architecture Components
- **Servers**: Handle core server logic
- **Publishers**: Generate and broadcast emoji events
- **Subscribers**: Consume and process emoji streams
- **Spark Engine**: Perform real-time data processing
- **Client**: Interact with the emoji broadcasting system

## Technology Stack
- Python
- Apache Kafka
- Apache Spark
- Event-Driven Architecture
