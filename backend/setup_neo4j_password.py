#!/usr/bin/env python3
"""
Script to initialize Neo4j password for the first time.
This script should be run when starting with a fresh Neo4j installation.
"""

import sys
from neo4j import GraphDatabase

def change_neo4j_password(uri, current_password, new_password):
    """
    Change the Neo4j password from current to new password.
    This is needed because Neo4j requires password change on first login with default credentials.
    """
    try:
        # Connect with the current password
        driver = GraphDatabase.driver(uri, auth=("neo4j", current_password))
        
        # Change the password
        with driver.session() as session:
            # Execute the ALTER USER statement to change the password
            session.run("ALTER CURRENT USER SET PASSWORD FROM $current_password TO $new_password",
                       current_password=current_password, new_password=new_password)
        
        driver.close()
        print(f"✅ Successfully changed Neo4j password!")
        print(f"URI: {uri}")
        print(f"Username: neo4j")
        print(f"New Password: {new_password}")
        return True
        
    except Exception as e:
        print(f"❌ Error changing Neo4j password: {e}")
        return False

def test_connection(uri, username, password):
    """Test if the new credentials work."""
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful!' AS message")
            record = result.single()
            print(f"✅ Connection test successful: {record['message']}")
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Default values - these should match your .env file
    uri = "bolt://localhost:7687"
    current_password = "neo4j"  # Default Neo4j password
    new_password = "MyStr0ngPassw0rd!"  # New password
    
    if len(sys.argv) > 1:
        current_password = sys.argv[1]
    if len(sys.argv) > 2:
        new_password = sys.argv[2]
    
    print("🔄 Setting up Neo4j password...")
    print(f"URI: {uri}")
    print(f"Current password: {current_password}")
    print(f"New password: {new_password}")
    
    # Change the password
    if change_neo4j_password(uri, current_password, new_password):
        print("\n✅ Password change completed successfully!")
        print("\n📝 To use the new password:")
        print(f"   Update your .env file with NEO4J_PASSWORD={new_password}")
        print("   Restart your application to use the new credentials")
        
        # Test the new connection
        print("\n🔍 Testing new connection...")
        if test_connection(uri, "neo4j", new_password):
            print("\n🎉 Neo4j setup completed successfully!")
        else:
            print("\n⚠️  Connection test failed. Please check your Neo4j service.")
    else:
        print("\n❌ Failed to change Neo4j password. Please check your Neo4j service.")
        print("💡 Make sure Neo4j is running on your system.")
        print("   You can start it with Docker: docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/neo4j neo4j")