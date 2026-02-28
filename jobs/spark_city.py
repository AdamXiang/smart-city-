from pyspark.pandas import DataFrame
from pyspark.sql import SparkSession
from pyspark import SparkConf, SparkContext
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType, IntegerType

from config import configuration



def main():
    # spark.hadoop.....: tells hadoop and Spark how to connect to S3
    spark = SparkSession.builder.appName('SmartCityStreaming') \
                .config("spark.jars.packages",
                        "org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.0,"
                        "org.apache.hadoop:hadoop-aws:3.3.1,"
                        "com.amazonaws:aws-java-sdk:1.11.469") \
                .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                .config("spark.hadoop.fs.s3a.access.key", configuration.get('AWS_ACCESS_KEY')) \
                .config("spark.hadoop.fs.s3a.secret.key", configuration.get('AWS_SECRET_KEY')) \
                .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
                .getOrCreate()

    # Adjust the log level to minimize the console output on executors
    spark.sparkContext.setLogLevel('WARN')

    # Vehicle Schema
    vehicle_schema = StructType([
        StructField('id', StringType(), True),
        StructField('device_id', StringType(), True),
        StructField('timestamp', TimestampType(), True),
        StructField('location', StringType(), True),
        StructField('speed', DoubleType(), True),
        StructField('direction', StringType(), True),
        StructField('make', StringType(), True),
        StructField('model', StringType(), True),
        StructField('year', IntegerType(), True),
        StructField('fuel_type', StringType(), True),
    ])

    # GPS Schema
    gps_schema = StructType([
        StructField('id', StringType(), True),
        StructField('device_id', StringType(), True),
        StructField('timestamp', TimestampType(), True),
        StructField('speed', DoubleType(), True),
        StructField('direction', StringType(), True),
        StructField('vehicle_type', StringType(), True),
    ])

    # Traffic Schema
    traffic_schema = StructType([
        StructField('id', StringType(), True),
        StructField('device_id', StringType(), True),
        StructField('camera_id', StringType(), True),
        StructField('location', StringType(), True),
        StructField('timestamp', TimestampType(), True),
        StructField('snapshot', StringType(), True),
    ])

    # Weather Schema
    weather_schema = StructType([
        StructField('id', StringType(), True),
        StructField('device_id', StringType(), True),
        StructField('location', StringType(), True),
        StructField('timestamp', TimestampType(), True),
        StructField('temperature', DoubleType(), True),
        StructField('weather_condition', StringType(), True),
        StructField('precipitation', DoubleType(), True),
        StructField('wind_speed', DoubleType(), True),
        StructField('humidity', IntegerType(), True),
        StructField('airQualityIndex', DoubleType(), True),
    ])

    # Emergency Schema
    emergency_schema = StructType([
        StructField('id', StringType(), True),
        StructField('device_id', StringType(), True),
        StructField('incident_id', StringType(), True),
        StructField('type', StringType(), True),
        StructField('timestamp', TimestampType(), True),
        StructField('location', StringType(), True),
        StructField('status', StringType(), True),
        StructField('description', StringType(), True),
    ])

    def read_kafka_topic(topic, schema):
        return (spark.readStream
                .format("kafka")
                .option("kafka.bootstrap.servers", "kafka:29092")
                .option("subscribe", topic)
                .option("startingOffsets", "earliest")
                .load()
                .selectExpr('CAST(value AS STRING)')
                .select(from_json(col('value'), schema).alias('data'))
                .select('data.*')
                .withWatermark('timestamp', '2 minutes')
                )

    def streamWriter(input: DataFrame, checkpoint_folder: str, output):
        return (input.writeStream
                .format('parquet')
                .option("checkpointLocation", checkpoint_folder)
                .option('path', output)
                .outputMode('append')
                .start()
                )

    vehicle_df = read_kafka_topic('vehicle_data', vehicle_schema).alias('vehicle')
    gps_df = read_kafka_topic('gps_data', gps_schema).alias('gps')
    traffic_df = read_kafka_topic('traffic_data', traffic_schema).alias('traffic')
    weather_df = read_kafka_topic('weather_data', weather_schema).alias('weather')
    emergency_df = read_kafka_topic('emergency_data', emergency_schema).alias('emergency')

    # Join all the dataframes with id and timestamp



    qurey1 = streamWriter(vehicle_df,
                 's3a://spark-streaming-ching/checkpoints/vehicle_data',
                 's3a://spark-streaming-ching/data/vehicle_data')
    qurey2 = streamWriter(gps_df,
                 's3a://spark-streaming-ching/checkpoints/gps_data',
                 's3a://spark-streaming-ching/data/gps_data')
    qurey3 = streamWriter(traffic_df,
                 's3a://spark-streaming-ching/checkpoints/traffic_data',
                 's3a://spark-streaming-ching/data/traffic_data')
    qurey4 = streamWriter(weather_df,
                 's3a://spark-streaming-ching/checkpoints/weather_data',
                 's3a://spark-streaming-ching/data/weather_data')
    qurey5 = streamWriter(emergency_df,
                 's3a://spark-streaming-ching/checkpoints/emergency_data',
                 's3a://spark-streaming-ching/data/emergency_data')

    qurey5.awaitTermination()


if __name__ == '__main__':
    main()