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
            "service_name": "ingestor",
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

def publish_message(channel, queue_name, message):
    """Publish a message to the specified queue"""
    logger = logging.getLogger()
    
    try:
        # Declare queue (idempotent operation)
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
        )
        
        logger.info(f"Message published to queue '{queue_name}': {json.dumps(message)}")
        
    except Exception as e:
        logger.error(f"Failed to publish message: {str(e)}")
        raise

def main():
    """Main service loop"""
    logger = setup_logging()
    logger.info("NFL Ingestor service starting up")
    
    # Get configuration
    queue_name = os.getenv('RABBITMQ_QUEUE', 'game_events')
    interval = int(os.getenv('INGESTOR_INTERVAL', 10))
    
    # Create RabbitMQ connection
    connection = create_rabbitmq_connection()
    channel = connection.channel()
    
    message_counter = 1
    
    try:
        logger.info(f"Starting message publishing loop (every {interval} seconds)")
        
        while True:
            # Create placeholder test message
            test_message = {
                "game_id": f"test_{message_counter:03d}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "home_team": "Test Home Team",
                "away_team": "Test Away Team",
                "status": "placeholder_data",
                "message_number": message_counter
            }
            
            # Publish message
            publish_message(channel, queue_name, test_message)
            
            message_counter += 1
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping service")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {str(e)}")
    finally:
        try:
            connection.close()
            logger.info("RabbitMQ connection closed")
        except:
            pass
        logger.info("NFL Ingestor service shutdown complete")

if __name__ == "__main__":
    main()