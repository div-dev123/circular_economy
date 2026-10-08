#!/usr/bin/env python3
"""
Setup script for Neo4j initial password configuration.
Run this script to set the initial password for Neo4j.
"""

import sys
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def setup_neo4j_password():
    # Get Neo4j connection details from environment
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
    
    print(f"Attempting to connect to Neo4j at {neo4j_uri}")
    print(f"Using username: {neo4j_username}")
    
    try:
        # First try to connect with default password
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, "neo4j"))
        
        with driver.session() as session:
            # Change the default password
            session.run("ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO $password", 
                       password=neo4j_password)
        
        driver.close()
        print(f"Successfully updated Neo4j password to: {neo4j_password}")
        print("You can now connect to Neo4j with the configured password.")
        
    except Exception as e:
        print(f"Error setting Neo4j password: {e}")
        print("This might mean:")
        print("1. Neo4j is not running - start it with: docker-compose up neo4j")
        print("2. The password might already be set - try running the app directly")
        print("3. Connection details in .env file might be incorrect")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_neo4j_password()
    if success:
        print("\nSetup completed successfully!")
        print("You can now run the main application with: python app.py")
    else:
        print("\nSetup failed! Please check the error messages above.")
        sys.exit(1)