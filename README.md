# Project Prestige - Phase 2 NFL Validation Engine

## Milestone 1: Production-Ready Service Skeletons

This milestone establishes the foundational infrastructure for the NFL Validation Engine with production-ready microservices architecture.

## Architecture Overview

The system consists of two core microservices:

- **nfl_ingestor**: Publishes test messages to the message queue every 10 seconds
- **nfl_processor**: Consumes messages from the queue and processes them
- **RabbitMQ**: Message queue for asynchronous communication between services

## Prerequisites

- Docker and Docker Compose installed
- Git for version control

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd project_prestige
   ```

2. **Start the entire system**
   ```bash
   docker-compose up --build
   ```

3. **View logs**
   ```bash
   # View all service logs
   docker-compose logs -f
   
   # View specific service logs
   docker-compose logs -f nfl_ingestor
   docker-compose logs -f nfl_processor
   ```

4. **Stop the system**
   ```bash
   docker-compose down
   ```

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options.

### Key Configuration Options

- `RABBITMQ_HOST`: RabbitMQ server hostname
- `RABBITMQ_QUEUE`: Queue name for message passing
- `INGESTOR_INTERVAL`: Message publishing interval in seconds
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Features

### Production-Ready Infrastructure
- ✅ Containerized microservices with Docker
- ✅ Environment-based configuration
- ✅ Structured JSON logging
- ✅ Exponential backoff retry logic
- ✅ Health checks and graceful shutdown

### Resilience & Observability
- **Retry Logic**: Automatic reconnection with exponential backoff (1s → 2s → 4s → 8s → 60s max)
- **Structured Logging**: JSON-formatted logs with timestamp, level, service name, and message
- **Health Monitoring**: Built-in health checks for all services

### Message Flow
1. `nfl_ingestor` publishes test messages every 10 seconds to `game_events` queue
2. `nfl_processor` consumes messages and logs their content
3. All operations are logged with structured JSON format

## Accessing RabbitMQ Management

The RabbitMQ management interface is available at: http://localhost:15672
- Username: `guest`
- Password: `guest`

## Development

### Running Individual Services

```bash
# Run ingestor locally
cd nfl_ingestor
pip install -r requirements.txt
python main.py

# Run processor locally
cd nfl_processor
pip install -r requirements.txt
python main.py
```

### Viewing Real-time Logs

```bash
# Follow logs for all services
docker-compose logs -f

# Follow logs for specific service
docker-compose logs -f nfl_processor
```

### Stopping Services

```bash
# Stop and remove containers
docker-compose down

# Stop, remove containers, and clean up volumes
docker-compose down -v
```

## Expected Output

When running successfully, you should see:

**nfl_ingestor logs:**
```json
{"timestamp": "2025-07-28T10:00:00Z", "level": "INFO", "service_name": "ingestor", "message": "NFL Ingestor service starting up"}
{"timestamp": "2025-07-28T10:00:01Z", "level": "INFO", "service_name": "ingestor", "message": "Successfully connected to RabbitMQ"}
{"timestamp": "2025-07-28T10:00:11Z", "level": "INFO", "service_name": "ingestor", "message": "Message published to queue 'game_events': {...}"}
```

**nfl_processor logs:**
```json
{"timestamp": "2025-07-28T10:00:00Z", "level": "INFO", "service_name": "processor", "message": "NFL Processor service starting up"}
{"timestamp": "2025-07-28T10:00:01Z", "level": "INFO", "service_name": "processor", "message": "Successfully connected to RabbitMQ"}
{"timestamp": "2025-07-28T10:00:11Z", "level": "INFO", "service_name": "processor", "message": "Message received: {...}"}
```

## Next Milestones

- **Milestone 2**: Data Integration & Persistence (PostgreSQL, real NFL data processing)
- **Milestone 3**: Backtesting Logic & Walk-Forward Optimization
- **Milestone 4**: API & User Interface

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 5672 and 15672 are not in use
2. **Docker issues**: Try `docker-compose down -v` and rebuild
3. **Connection failures**: Check Docker network connectivity

### Debugging

View detailed logs:
```bash
docker-compose logs -f --tail=100
```

Check service health:
```bash
docker-compose ps
```

## Contact

For technical questions or issues, contact the development team.