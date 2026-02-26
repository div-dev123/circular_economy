
## 🛠️ Database Setup Instructions

### Initial Database Setup

1. **Start Required Services** (using Docker):
```bash
# Neo4j
docker run -p 7474:7474 -p 7687:7687 --name neo4j-container -e NEO4J_AUTH=neo4j/neo4j neo4j

# MongoDB
docker run -p 27017:27017 --name mongodb-container mongo

# Redis
docker run -p 6379:6379 --name redis-container redis

# Cassandra
docker run -p 9042:9042 --name cassandra-container cassandra:latest

# PostgreSQL
docker run -p 5432:5432 --name postgresql-container -e POSTGRES_PASSWORD=password -e POSTGRES_DB=circular_economy postgres
```

2. **Change Neo4j Default Password** (Required for first-time setup):
```bash
cd backend
python setup_neo4j_password.py
```

3. **Update Environment Variables**:
Edit the `.env` file with your database credentials.
