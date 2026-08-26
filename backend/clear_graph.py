from neo4j import GraphDatabase
import os

# Connection details - Using Defaults from docker-compose
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')

def clear_graph():
    print(f"Connecting to Neo4j at {NEO4J_URI}...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            # DETACH DELETE removes both nodes and their relationships
            print("Deleting all nodes and relationships...")
            result = session.run("MATCH (n) DETACH DELETE n")
            summary = result.consume()
            print(f"✅ Successfully deleted {summary.counters.nodes_deleted} nodes and {summary.counters.relationships_deleted} relationships.")
        driver.close()
    except Exception as e:
        print(f"❌ Error clearing graph: {e}")

if __name__ == "__main__":
    clear_graph()
