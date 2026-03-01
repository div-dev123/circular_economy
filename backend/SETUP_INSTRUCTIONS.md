# Database Setup Instructions

## Prerequisites

Make sure you have Docker installed on your system. You can download it from [Docker's official website](https://www.docker.com/products/docker-desktop).

## Quick Setup with Docker Compose

1. **Start all required services:**
   ```bash
   cd backend
   docker-compose up -d
   ```

2. **Wait for all services to start:**
   ```bash
   # Wait about 30 seconds for all services to be ready
   docker-compose ps
   ```

3. **Configure Neo4j password (first time only):**
   ```bash
   python setup_neo4j_password.py
   ```

4. **Start the Flask application:**
   ```bash
   python app.py
   ```

## Individual Service Setup

If you prefer to run services individually:

### PostgreSQL
```bash
docker run -d \
  --name ce_postgresql \
  -e POSTGRES_DB=circular_economy \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:13
```

### Neo4j
```bash
docker run -d \
  --name ce_neo4j \
  -e NEO4J_AUTH=neo4j/password \
  -p 7474:7474 -p 7687:7687 \
  -v neo4j_data:/data \
  neo4j:latest
```

Then run:
```bash
python setup_neo4j_password.py
```

### MongoDB
```bash
docker run -d \
  --name ce_mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:5
```

### Redis
```bash
docker run -d \
  --name ce_redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:alpine
```

### Cassandra
```bash
docker run -d \
  --name ce_cassandra \
  -e MAX_HEAP_SIZE=512M \
  -e HEAP_NEWSIZE=128M \
  -p 9042:9042 \
  -v cassandra_data:/var/lib/cassandra \
  cassandra:4
```

## Environment Configuration

Make sure your `.env` file in the backend directory has the correct settings:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=circular_economy
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=postgres

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password  # This will be changed after setup

MONGODB_URI=mongodb://admin:password@localhost:27017/
MONGODB_DATABASE=circular_economy

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

CASSANDRA_HOST=localhost
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=circular_economy
```

## Troubleshooting

### If PostgreSQL gives "role does not exist" error:
The application will try to create the user automatically. If it fails:
1. Connect to PostgreSQL directly: `psql -h localhost -U postgres`
2. Create the user manually: `CREATE USER postgres WITH PASSWORD 'postgres';`
3. Grant privileges: `GRANT ALL PRIVILEGES ON DATABASE circular_economy TO postgres;`

### If Neo4j authentication fails:
1. Make sure you've run `python setup_neo4j_password.py` after starting Neo4j
2. Or change the password in `.env` to match what you set during setup

### Checking Service Status
```bash
docker-compose ps
```

### Stopping Services
```bash
docker-compose down
```

## Verifying Setup

Once all services are running and configured, start your Flask application:

```bash
python app.py
```

Check the health endpoint to verify all databases are connected:
```
GET http://localhost:5001/api/health
```

You should see something like:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "database_status": {
    "neo4j": true,
    "mongodb": true,
    "redis": true,
    "cassandra": true,
    "postgresql": true
  },
  "database_integration": true
}
```