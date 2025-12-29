import pika
import json
import config

def publish_task(image_url: str):
    credentials = pika.PlainCredentials(config.RABBIT_USER, config.RABBIT_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config.RABBIT_HOST, port=config.RABBIT_PORT, credentials=credentials)
    )
    channel = connection.channel()

    channel.queue_declare(queue='vision_tasks', durable=True)

    message = {"url": image_url}
    
    channel.basic_publish(
        exchange='',
        routing_key='vision_tasks',
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)  
    )
    
    connection.close()
