import os
import json
import time
import logging
import pika
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class JSONFormatter(logging.Formatter):
    """Custom formatter to output logs in JSON format"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service_name": "processor",
            "message": record.getMessage()
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

def setup_logging():
    """Configure structured JSON logging"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
    
    # Remove default handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    return logger

def create_rabbitmq_connection():
    """Create RabbitMQ connection with exponential backoff retry"""
    logger = logging.getLogger()
    
    host = os.getenv('RABBITMQ_HOST', 'localhost')
    port = int(os.getenv('RABBITMQ_PORT', 5672))
    user = os.getenv('RABBITMQ_USER', 'guest')
    password = os.getenv('RABBITMQ_PASS', 'guest')
    
    retry_delay = 1
    max_delay = 60
    
    while True:
        try:
            logger.info(f"Attempting to connect to RabbitMQ at {host}:{port}")
            
            credentials = pika.PlainCredentials(user, password)
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            connection = pika.BlockingConnection(parameters)
            logger.info("Successfully connected to RabbitMQ")
            return connection
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            logger.info(f"Retrying in {retry_delay} seconds...")
            
            time.sleep(retry_delay)
            
            # Exponential backoff with max cap
            retry_delay = min(retry_delay * 2, max_delay)

def process_message(ch, method, properties, body):
    """Process received message from queue"""
    logger = logging.getLogger()
    
    try:
        # Parse JSON message
        message = json.loads(body.decode('utf-8'))
        
        # Log the received message
        logger.info(f"Message received: {json.dumps(message)}")
        
        # Placeholder processing logic
        # In future milestones, this will contain complex backtesting logic
        if message.get('status') == 'placeholder_data':
            processed_result = {
                "processed_at": datetime.utcnow().isoformat() + "Z",
                "original_game_id": message.get('game_id'),
                "processing_status": "success",
                "notes": "Placeholder processing completed"
            }
            logger.info(f"Processing completed: {json.dumps(processed_result)}")
        
        # Acknowledge message processing
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON message: {str(e)}")
        # Reject message and don't requeue
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # Reject message and don't requeue for now
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    """Main service loop"""
    logger = setup_logging()
    logger.info("NFL Processor service starting up")
    
    # Get configuration
    queue_name = os.getenv('RABBITMQ_QUEUE', 'game_events')
    
    # Create RabbitMQ connection
    connection = create_rabbitmq_connection()
    channel = connection.channel()
    
    try:
        # Declare queue (idempotent operation)
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Set up consumer
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=process_message
        )
        
        # Set QoS to process one message at a time
        channel.basic_qos(prefetch_count=1)
        
        logger.info(f"Waiting for messages from queue '{queue_name}'. To exit press CTRL+C")
        
        # Start consuming messages
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping service")
        channel.stop_consuming()
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {str(e)}")
    finally:
        try:
            connection.close()
            logger.info("RabbitMQ connection closed")
        except:
            pass
        logger.info("NFL Processor service shutdown complete")

if __name__ == "__main__":
    main()