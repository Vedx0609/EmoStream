# this is the code for the publisher in the 1st cluster.
# The publisher receives data via a kafka-consumer which subscribes to the same topic as the one published to by the main producer
# Main producer being the one in the pyspark processing program
# This code publishes to a topic which 3 subscribers subscribe to

from kafka import KafkaConsumer, KafkaProducer
import json

INPUT_TOPIC = 'scaled_emojis' #Topic for getting the scaled emojis
SUBSCRIBER_TOPIC = 'cluster2'

consumer = KafkaConsumer(INPUT_TOPIC, value_deserializer = lambda m:json.loads(m.decode('utf-8')))
cluster_publisher = KafkaProducer(value_serializer = lambda m: json.dumps(m).encode('utf-8'))

for message in consumer:
    if 'end' in message.value:                  #replace 'end' with end message
       break

    # print(message.value)
    data_to_be_forwarded = message.value
    print("Received from spark engine: ", data_to_be_forwarded)
    
    try:
        cluster_publisher.send(SUBSCRIBER_TOPIC,data_to_be_forwarded)
        print('message successfully sent')
    except:
        print('there was an error')


consumer.close()
# cluster_publisher.flush()
# cluster_publisher.close()
