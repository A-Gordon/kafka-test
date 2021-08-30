import backoff
import logging
import os
import pymongo
import sys
import time
import traceback

from json import dumps, loads
from kafka import KafkaProducer, KafkaConsumer, BrokerConnection
from pymongo import MongoClient


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def initializeEnv():
  """Initializes environment variables"""
  try:  
    function = os.getenv('FUNCTION')
  except KeyError: 
    logger.error('Please set the environment variable FUNCTION')
    sys.exit(1)
  try:  
    kafkaBootstrapServers = os.getenv('KAFKA_BOOTSTRAP_BROKER')
  except KeyError: 
    logger.error('Please set the environment variable KAFKA_BOOTSTRAP_BROKER')
    sys.exit(1)
  try:  
    kafkaGroup = os.getenv('KAFKA_GROUP')
  except KeyError: 
    logger.error('Please set the environment variable KAFKA_GROUP')
    sys.exit(1)
  try:  
    kafkaTopic = os.getenv('KAFKA_TOPIC')
  except KeyError: 
    logger.error('Please set the environment variable KAFKA_TOPIC')
    sys.exit(1)
  try:  
    timeInterval = os.getenv('TIME_INTERVAL')
  except KeyError: 
    logger.error('Please set the environment variable TIME_INTERVAL')
    sys.exit(1)
  try:  
    mongodbURI = os.getenv('MONGODB_URI')
  except KeyError: 
    logger.error('Please set the environment variable MONGODB_URI')
    sys.exit(1)
  logger.info('All environment variables present')
  return function, kafkaBootstrapServers, kafkaGroup, kafkaTopic, timeInterval, mongodbURI

def createProducer(kafkaBootstrapServers):
  """Tries to establish a Kafka producer connection"""
  try:
    logger.debug('Creating new kafka producer using brokers: ' +
                        str(['kafkaBootstrapServers']))

    return KafkaProducer(bootstrap_servers=[kafkaBootstrapServers],
                          value_serializer=lambda x: dumps(x).encode('utf-8'),
                          client_id='test-client',
                          acks='all')
  except KeyError as e:
    logger.error('Missing setting named ' + str(e),
                        {'ex': traceback.format_exc()})
  except:
    logger.error("Couldnt initialize kafka producer.",
                        {'ex': traceback.format_exc()})
    raise

def createConsumer(kafkaBootstrapServers, kafkaGroup, kafkaTopic):
  """Tries to establish a Kafka consumer connection"""
  try:
    logger.debug('Creating new kafka consumer using brokers: ' +
                        str(['kafkaBootstrapServers']))

    return KafkaConsumer(kafkaTopic,
                        bootstrap_servers=[kafkaBootstrapServers],
                        auto_offset_reset='earliest',
                        enable_auto_commit=True,
                        group_id=kafkaGroup,
                        value_deserializer=lambda x: loads(x.decode('utf-8')))
  except KeyError as e:
    logger.error('Missing setting named ' + str(e),
                        {'ex': traceback.format_exc()})
  except:
    logger.error('Couldnt initialize kafka producer.',
                        {'ex': traceback.format_exc()})
    raise

def createMongoConnection(mongodbURI):
  """Tries to establish a mongoDB client connection"""
  try: 
    logger.debug('Creating new mongodb client consumer using URI: ' +
                        str(['mongodbURI']))
    return MongoClient(mongodbURI)
  except KeyError as e:
    logger.error('Missing setting named ' + str(e),
                        {'ex': traceback.format_exc()})
  except:
    logger.error('Couldnt initialize mongodb client.',
                        {'ex': traceback.format_exc()})
    raise

def generateData(timestamp):
  """Generates dummy data"""
  datapoint = ('datapoint_' + timestamp)
  logger.info('Datapoint generated: {}'.format(datapoint))
  data = '{"success": "true", "status": 200, "message": "' + datapoint + '"}'
  return data

def kafkaPublish(producer, topic, datapoint):
  """Tries to publish data to a kafka topic"""
  connection = producer.bootstrap_connected()
  logger.info('Producer connection result: {}'.format(connection))

  try:
    logger.info('Attempting to publish datapoint {} to kafka'.format(datapoint))
    future = producer.send(topic, value=datapoint)
    result = future.get(timeout=60)
    logger.info('Published datapoint {} Result: {}'.format(datapoint, result))
  except:
    logger.error('Failed to publish {} Result: {}'.format(datapoint, result))
    raise 

def kafkaProducer(kafkaBootstrapServers, kafkaTopic, timeInterval):
  """Establishes a kafka producer and publishes data to a topic"""
  producer = createProducer(kafkaBootstrapServers)
  connection = producer.bootstrap_connected()
  data = generateData(str(int(time.time())))
  # if connection == True:
  kafkaPublish(producer, kafkaTopic, data)
  time.sleep(int(timeInterval))

@backoff.on_exception(backoff.expo,
                      pymongo.errors.AutoReconnect,
                      max_tries=8)
# Future advancement would be to manage the offset in a more ordered fashion. 
# Currently auto commit offset is enabled but in the future I would disable this and handle the offset 
# after the confirmation of the insert into the DB. 
def kafkaConsumer (kafkaBootstrapServers, kafkaGroup, kafkaTopic, mongodbURI):
  """Establishes a kafka consumer and consumes data from a topic then pushes to mongo"""
  consumer = createConsumer(kafkaBootstrapServers, kafkaGroup, kafkaTopic)
  client = createMongoConnection(mongodbURI)
  collection = client.streamdata.streamdata
  for message in consumer:
    logger.debug('Retrieving data from kafka server {} topic {}'.format(kafkaBootstrapServers, kafkaTopic))
    message = message.value
    logger.debug('Retrieved data from kafka server {} topic {} Message value: {}'.format(kafkaBootstrapServers, kafkaTopic, message))
    collection.insert_one(loads(message))
    logger.info('Datapoint "{}" added to {}'.format(message, collection))
  

def main():
  if __name__ == '__main__':
    function, kafkaBootstrapServers, kafkaGroup, kafkaTopic, timeInterval, mongodbURI = initializeEnv()
    if function == 'producer':
      logger.info('Function: Producer enabled')
      while True:
        kafkaProducer(kafkaBootstrapServers, kafkaTopic, timeInterval)
    elif function == 'consumer':
      logger.info('Function: Consumer enabled')
      kafkaConsumer(kafkaBootstrapServers, kafkaGroup, kafkaTopic, mongodbURI)
    else:
      logger.error('No function defined, please define one')

main()
