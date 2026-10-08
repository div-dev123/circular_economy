import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)

from urllib.parse import urlparse, parse_qs

# Parse DATABASE_URL if provided (e.g. from Neon, Supabase, Render)
db_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
if db_url:
    parsed = urlparse(db_url)
    qs = parse_qs(parsed.query)
    default_ssl = 'require' if parsed.hostname not in ('localhost', '127.0.0.1') else 'prefer'
    sslmode_val = qs.get('sslmode', [os.getenv('POSTGRES_SSLMODE', default_ssl)])[0]
    pg_config = {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/') or 'circular_economy',
        'username': parsed.username or 'postgres',
        'password': parsed.password or 'password',
        'sslmode': sslmode_val
    }
else:
    pg_host = os.getenv('POSTGRES_HOST', 'localhost')
    default_ssl = 'require' if pg_host not in ('localhost', '127.0.0.1') else 'prefer'
    pg_config = {
        'host': pg_host,
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DATABASE', 'circular_economy'),
        'username': os.getenv('POSTGRES_USERNAME', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password'),
        'sslmode': os.getenv('POSTGRES_SSLMODE', default_ssl)
    }

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
        'url': os.getenv('REDIS_URL'),
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
    'postgresql': pg_config
}