#!/usr/bin/env python3
"""
Alias wrapper script for Neo4j password configuration.
Delegates directly to setup_neo4j_password.py.
"""
import sys
from setup_neo4j_password import setup_neo4j_password

if __name__ == "__main__":
    success = setup_neo4j_password()
    sys.exit(0 if success else 1)