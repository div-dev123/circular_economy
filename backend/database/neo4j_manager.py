from neo4j import GraphDatabase
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Neo4jManager:
    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        
    def close(self):
        self.driver.close()
        
    def create_waste_node(self, waste_id: str, waste_type: str, quantity: float, 
                         location: str, producer_id: str) -> None:
        """Create a waste node in the graph"""
        query = """
        CREATE (w:Waste {
            id: $waste_id,
            type: $waste_type,
            quantity: $quantity,
            location: $location,
            producer_id: $producer_id,
            created_at: timestamp()
        })
        """
        with self.driver.session() as session:
            session.run(query, waste_id=waste_id, waste_type=waste_type,
                       quantity=quantity, location=location, producer_id=producer_id)
            logger.info(f"Created waste node: {waste_id}")
    
    def create_industry_node(self, industry_id: str, industry_type: str, 
                           location: str, capacity: float) -> None:
        """Create an industry node in the graph"""
        query = """
        CREATE (i:Industry {
            id: $industry_id,
            type: $industry_type,
            location: $location,
            capacity: $capacity,
            created_at: timestamp()
        })
        """
        with self.driver.session() as session:
            session.run(query, industry_id=industry_id, industry_type=industry_type,
                       location=location, capacity=capacity)
            logger.info(f"Created industry node: {industry_id}")
    
    def create_supply_chain_relationship(self, waste_id: str, industry_id: str,
                                       relationship_type: str, distance: float,
                                       cost: float) -> None:
        """Create relationship between waste and industry"""
        query = """
        MATCH (w:Waste {id: $waste_id})
        MATCH (i:Industry {id: $industry_id})
        CREATE (w)-[r:SUPPLIED_TO {
            type: $relationship_type,
            distance: $distance,
            cost: $cost,
            created_at: timestamp()
        }]->(i)
        """
        with self.driver.session() as session:
            session.run(query, waste_id=waste_id, industry_id=industry_id,
                       relationship_type=relationship_type, distance=distance, cost=cost)
    
    def find_industries_for_waste(self, waste_type: str, location: str = None, 
                                max_distance: float = 100) -> List[Dict]:
        """Find all industries that can use specific waste type"""
        query = """
        MATCH (w:Waste {type: $waste_type})
        MATCH (i:Industry)
        WHERE i.type IN $compatible_industries
        """
        
        if location:
            query += """
            AND distance(point({latitude: w.latitude, longitude: w.longitude}),
                       point({latitude: i.latitude, longitude: i.longitude})) < $max_distance
            """
        
        query += """
        RETURN i.id as industry_id, i.type as industry_type, i.location as location,
               w.quantity as available_quantity
        ORDER BY w.quantity DESC
        """
        
        compatible_industries = self._get_compatible_industries(waste_type)
        
        with self.driver.session() as session:
            result = session.run(query, waste_type=waste_type,
                               compatible_industries=compatible_industries,
                               max_distance=max_distance)
            return [record.data() for record in result]
    
    def find_shortest_supply_path(self, waste_id: str, target_industry_id: str) -> List[Dict]:
        """Find shortest path from waste producer to consumer"""
        query = """
        MATCH path = (w:Waste {id: $waste_id})-[:SUPPLIED_TO*1..5]->(i:Industry {id: $target_id})
        RETURN [n IN nodes(path) | {id: n.id, type: labels(n)[0]}] as path_nodes,
               reduce(s = 0, r IN relationships(path) | s + r.distance) as total_distance
        ORDER BY total_distance
        LIMIT 1
        """
        
        with self.driver.session() as session:
            result = session.run(query, waste_id=waste_id, target_id=target_industry_id)
            return [record.data() for record in result]
    
    def get_circular_economy_pathways(self, waste_type: str) -> List[Dict]:
        """Find circular economy pathways for waste type"""
        query = """
        MATCH (w:Waste {type: $waste_type})-[:SUPPLIED_TO]->(i1:Industry)
        MATCH (i1)-[:PRODUCES]->(p:Product)-[:GENERATES]->(w2:Waste)
        MATCH (w2)-[:SUPPLIED_TO]->(i2:Industry)
        RETURN w.type as input_waste, i1.type as first_industry,
               p.name as intermediate_product, w2.type as output_waste,
               i2.type as second_industry
        """
        
        with self.driver.session() as session:
            result = session.run(query, waste_type=waste_type)
            return [record.data() for record in result]
    
    def _get_compatible_industries(self, waste_type: str) -> List[str]:
        """Map waste types to compatible industries"""
        compatibility_map = {
            'PLASTIC': ['Recycling', 'Manufacturing', 'Construction'],
            'METAL': ['Steel', 'Manufacturing', 'Automotive'],
            'ORGANIC': ['Agriculture', 'Biogas', 'Composting'],
            'PAPER_CARDBOARD': ['Recycling', 'Packaging', 'Manufacturing'],
            'GLASS': ['Glass', 'Construction', 'Manufacturing'],
            'TEXTILE': ['Textile', 'Insulation', 'Manufacturing'],
            'CONSTRUCTION': ['Construction', 'Recycling', 'Manufacturing'],
            'ELECTRONIC': ['Electronics', 'Recycling', 'Manufacturing']
        }
        return compatibility_map.get(waste_type, [])