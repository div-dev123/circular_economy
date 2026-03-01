#!/usr/bin/env python3
"""
Script to change Neo4j password from default 'neo4j' to the one in .env
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def change_neo4j_password():
    # Get Neo4j connection details from environment
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'MyStr0ngPassw0rd!')
    
    print(f"Attempting to connect to Neo4j at {neo4j_uri}")
    print(f"Changing password for user: {neo4j_username}")
    
    try:
        # Connect with the default password 'neo4j'
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, "neo4j"))
        
        with driver.session() as session:
            # Change the password to the one in the .env file
            session.run("ALTER CURRENT USER SET PASSWORD FROM $current_password TO $new_password", 
                       current_password="neo4j", new_password=neo4j_password)
        
        driver.close()
        print(f"✅ Successfully updated Neo4j password to: {neo4j_password}")
        print("You can now connect to Neo4j with the configured password.")
        
    except Exception as e:
        print(f"❌ Error updating Neo4j password: {e}")
        print("This might mean:")
        print("1. Neo4j is not running - check with: docker ps")
        print("2. The default password might not be 'neo4j' anymore")
        print("3. Connection details in .env file might be incorrect")
        return False
    
    return True

if __name__ == "__main__":
    success = change_neo4j_password()
    if success:
        print("\n✅ Neo4j setup completed successfully!")
        print("You can now run the main application with: python app.py")
    else:
        print("\n❌ Neo4j setup failed! Please check the error messages above.")
        import sys
        sys.exit(1)