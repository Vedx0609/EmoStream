# To run this, first run main_server.py and use this command:
# spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3 main_spark_engine.py (You can change 3.5.3 to whatever spark version you have)

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType
from kafka import KafkaProducer
import json
import time

PRODUCER_TOPIC = "scaled_emojis"
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda m: json.dumps(m).encode('utf-8')
)

spark = SparkSession.builder \
    .appName("KafkaConsumerWithSparkEngine") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

#Define the schema of streaming data
emoji_schema = StructType([
    StructField("emoji_type", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("user_id", IntegerType(), True)
])

#Define the array in which the topic sends emoji data
batch_schema = ArrayType(emoji_schema)

topic = 'spark_consumer'

#Created a micro batching instance of streaming inputs
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", topic) \
    .option("startingOffsets", "latest") \
    .load() \
    .select(F.from_json(F.col("value").cast("string"), batch_schema).alias("data"))

#Break the array data into individual json/dictionary objects
exploded_df = df.select(F.explode("data").alias("emoji")) \
    .select("emoji.*")

#Function to process each batch
def process_batch(batch_df, batch_id):
    aggregated_df = batch_df.groupBy("emoji_type").count()
    
    #Scale it down (for every 1000 emojis = emoji count will be 1)
    #So divided by 1000 and applied a ceil function to it
    #Set it to 100 now just to see if it works. Can be changed to 1000 later
    scaled_df = aggregated_df.withColumn("scaled_count", F.ceil(aggregated_df["count"] / 100))
    final_df = scaled_df.select("emoji_type", "scaled_count")
    #Output the aggregation result
    final_df.show(truncate=False)

    emoji_dict = {row["emoji_type"]: row["scaled_count"] for row in final_df.collect()}

    if emoji_dict:
        producer.send(PRODUCER_TOPIC, emoji_dict)
        print(f"Sent scaled emojis to Pub Sub : {emoji_dict}")   
        producer.flush()

    #Printing aggregated as well to cross reference with the scaled down output (Can be removed)
    aggregated_df.show(truncate=False)
    #Send output after 2 seconds of processing
    time.sleep(2)

#Send the output to console (terminal) - using foreachBatch to process one batch at a time and not aggregate all the batches together
query = exploded_df.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("append") \
    .start()

query.awaitTermination()

# Key inferences
# Observed that we can also do .trigger(processingTime="2 seconds") for writeStream
# But it seemed as though sleep was working faster
