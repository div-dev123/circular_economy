import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)

# Database configurations
DATABASE_CONFIG = {
    'neo4j': {
        'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        'username': os.getenv('NEO4J_USERNAME', 'neo4j'),
        'password': os.getenv('NEO4J_PASSWORD', 'password')
    },
    'mongodb': {
        'uri': os.getenv('MONGODB_URI', 'mongodb://localhost:27017'),
        'database': os.getenv('MONGODB_DATABASE', 'circular_economy')
    },
    'redis': {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'db': int(os.getenv('REDIS_DB', 0)),
        'password': os.getenv('REDIS_PASSWORD', None)
    },
    'cassandra': {
        'hosts': os.getenv('CASSANDRA_HOSTS', '127.0.0.1').split(','),
        'keyspace': os.getenv('CASSANDRA_KEYSPACE', 'circular_economy'),
        'port': int(os.getenv('CASSANDRA_PORT', 9042))
    },
    'postgresql': {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DATABASE', 'circular_economy'),
        'username': os.getenv('POSTGRES_USERNAME', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password')
    }
}