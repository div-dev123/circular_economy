from typing import Dict, Any, List, Optional
import logging
from .config import DATABASE_CONFIG
from .neo4j_manager import Neo4jManager
from .mongodb_manager import MongoDBManager
from .redis_manager import RedisManager
from .cassandra_manager import CassandraManager
from .postgresql_manager import PostgreSQLManager

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.managers = {}
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize all database connections"""
        try:
            # Neo4j (Graph DB)
            neo4j_config = DATABASE_CONFIG['neo4j']
            self.managers['neo4j'] = Neo4jManager(
                uri=neo4j_config['uri'],
                username=neo4j_config['username'],
                password=neo4j_config['password']
            )
            logger.info("Neo4j connection initialized")
            
            # MongoDB (Document DB)
            mongo_config = DATABASE_CONFIG['mongodb']
            self.managers['mongodb'] = MongoDBManager(
                uri=mongo_config['uri'],
                database=mongo_config['database']
            )
            logger.info("MongoDB connection initialized")
            
            # Redis (Key-Value)
            redis_config = DATABASE_CONFIG['redis']
            self.managers['redis'] = RedisManager(
                host=redis_config['host'],
                port=redis_config['port'],
                db=redis_config['db'],
                password=redis_config['password']
            )
            logger.info("Redis connection initialized")
            
            # Cassandra (Column-Family)
            cassandra_config = DATABASE_CONFIG['cassandra']
            self.managers['cassandra'] = CassandraManager(
                hosts=cassandra_config['hosts'],
                keyspace=cassandra_config['keyspace'],
                port=cassandra_config['port']
            )
            logger.info("Cassandra connection initialized")
            
            # PostgreSQL (Relational)
            postgres_config = DATABASE_CONFIG['postgresql']
            self.managers['postgresql'] = PostgreSQLManager(
                host=postgres_config['host'],
                port=postgres_config['port'],
                database=postgres_config['database'],
                username=postgres_config['username'],
                password=postgres_config['password']
            )
            logger.info("PostgreSQL connection initialized")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def get_manager(self, db_type: str):
        """Get specific database manager"""
        return self.managers.get(db_type)
    
    def close_all_connections(self):
        """Close all database connections"""
        for db_type, manager in self.managers.items():
            try:
                if hasattr(manager, 'close'):
                    manager.close()
                    logger.info(f"Closed {db_type} connection")
            except Exception as e:
                logger.error(f"Error closing {db_type} connection: {e}")
    
    # Unified Interface Methods
    def record_waste_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Record complete waste transaction across all databases"""
        try:
            transaction_id = None
            
            # PostgreSQL: Store transaction details
            postgres_manager = self.managers['postgresql']
            transaction_id = postgres_manager.record_transaction(transaction_data)
            
            # MongoDB: Store user profile update
            if 'user_id' in transaction_data:
                mongo_manager = self.managers['mongodb']
                mongo_manager.update_user(str(transaction_data['user_id']), {
                    'last_transaction_at': 'current_timestamp()' # Simplified
                })
            
            # Cassandra: Store analytics and audit logs
            cassandra_manager = self.managers['cassandra']
            cassandra_manager.record_transaction(transaction_data)
            cassandra_manager.log_audit_event(
                user_id=str(transaction_data.get('user_id', '')),
                action='CREATE_TRANSACTION',
                resource_type='transaction',
                resource_id=transaction_id,
                details=f"Created transaction for {transaction_data.get('waste_type')}"
            )
            
            # Redis: Update real-time metrics
            redis_manager = self.managers['redis']
            redis_manager.increment_waste_views(str(transaction_data.get('waste_id', '')))
            
            # Neo4j: Update supply chain relationships
            neo4j_manager = self.managers['neo4j']
            if 'waste_id' in transaction_data and 'industry_id' in transaction_data:
                neo4j_manager.create_supply_chain_relationship(
                    waste_id=str(transaction_data['waste_id']),
                    industry_id=str(transaction_data['industry_id']),
                    relationship_type='TRANSACTION',
                    distance=0.0,  # Would be calculated
                    cost=transaction_data.get('price', 0.0)
                )
            
            logger.info(f"Transaction recorded successfully: {transaction_id}")
            return transaction_id
            
        except Exception as e:
            logger.error(f"Error recording transaction: {e}")
            raise
    
    def search_waste_listings(self, query: str, location: str = None, 
                            user_id: str = None) -> List[Dict[str, Any]]:
        """Search waste listings with caching and analytics"""
        try:
            # Check Redis cache first
            redis_manager = self.managers['redis']
            cache_key = f"search:{hash(query)}:{query}"
            cached_results = redis_manager.get_cached_search(query)
            
            if cached_results:
                logger.info("Returning cached search results")
                return cached_results
            
            # MongoDB: Perform actual search
            mongo_manager = self.managers['mongodb']
            results = mongo_manager.search_waste_listings(query, location)
            
            # PostgreSQL: Get user preferences for personalized results
            if user_id:
                postgres_manager = self.managers['postgresql']
                user_companies = postgres_manager.get_user_companies(int(user_id))
                # Apply personalization logic here
                
            # Cassandra: Record search analytics
            cassandra_manager = self.managers['cassandra']
            cassandra_manager.record_analytics_metric(
                metric_name='search_queries',
                timestamp='current_timestamp()',
                dimension1=query,
                dimension2=location or 'global',
                value=1.0
            )
            
            # Cache results in Redis
            redis_manager.cache_waste_search(query, results, ttl=1800)
            
            # Track user interaction in Redis
            if user_id:
                redis_manager.track_user_interaction(user_id, 'search', 'query')
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching waste listings: {e}")
            return []
    
    def get_supply_chain_insights(self, waste_type: str) -> Dict[str, Any]:
        """Get comprehensive supply chain insights using graph database"""
        try:
            # Neo4j: Get industry connections and pathways
            neo4j_manager = self.managers['neo4j']
            industries = neo4j_manager.find_industries_for_waste(waste_type)
            pathways = neo4j_manager.get_circular_economy_pathways(waste_type)
            
            # PostgreSQL: Get industry statistics
            postgres_manager = self.managers['postgresql']
            industry_stats = postgres_manager.get_industry_statistics()
            
            # Cassandra: Get historical trends
            cassandra_manager = self.managers['cassandra']
            trends = cassandra_manager.get_waste_diversion_trends(days=90)
            
            # Redis: Get real-time metrics
            redis_manager = self.managers['redis']
            # Get recent interactions, views, etc.
            
            insights = {
                'waste_type': waste_type,
                'compatible_industries': industries,
                'circular_pathways': pathways,
                'industry_statistics': industry_stats,
                'historical_trends': trends,
                'real_time_metrics': {
                    'active_listings': len(industries),
                    'recent_interactions': 0  # Would be populated
                }
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting supply chain insights: {e}")
            return {}
    
    def get_environmental_impact_report(self, user_id: str = None) -> Dict[str, Any]:
        """Generate comprehensive environmental impact report"""
        try:
            # Cassandra: Get environmental metrics
            cassandra_manager = self.managers['cassandra']
            co2_savings = cassandra_manager.get_co2_savings_by_month(2026, 2)
            trends = cassandra_manager.get_waste_diversion_trends(days=365)
            
            # PostgreSQL: Get compliance data
            postgres_manager = self.managers['postgresql']
            compliance_report = postgres_manager.get_compliance_report()
            
            # MongoDB: Get user-specific statistics
            user_stats = {}
            if user_id:
                mongo_manager = self.managers['mongodb']
                user_stats = mongo_manager.get_waste_statistics(user_id)
            
            # Redis: Get real-time engagement metrics
            redis_manager = self.managers['redis']
            # Get views, interactions, etc.
            
            report = {
                'period': 'Last 12 months',
                'total_co2_saved': co2_savings,
                'waste_diversion_trends': trends,
                'compliance_metrics': compliance_report,
                'user_statistics': user_stats,
                'real_time_engagement': {
                    'total_views': 0,  # Would be populated
                    'active_users': 0
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating environmental impact report: {e}")
            return {}
    
    def classify_waste_with_caching(self, image_hash: str, image_bytes: bytes, 
                                   user_id: str = None) -> Dict[str, Any]:
        """AI waste classification with caching"""
        try:
            # Check Redis cache first
            redis_manager = self.managers['redis']
            cached_result = redis_manager.get_cached_classification(image_hash)
            
            if cached_result:
                logger.info("Returning cached classification result")
                return cached_result
            
            # Perform actual classification (would call your AI model)
            # This is where you'd integrate with your PyTorch model
            classification_result = {
                'waste_types': [
                    {'name': 'PLASTIC', 'confidence': 0.95, 'icon': '🥤'},
                    {'name': 'METAL', 'confidence': 0.78, 'icon': '🔧'}
                ],
                'estimated_value': '$120-180 per ton',
                'processing_time': '2.3s'
            }
            
            # Cache the result
            redis_manager.cache_waste_classification(image_hash, classification_result)
            
            # Store in MongoDB for user history
            if user_id:
                mongo_manager = self.managers['mongodb']
                mongo_manager.store_waste_image(
                    image_bytes, 
                    f"waste_{image_hash}.jpg",
                    {'classification_result': classification_result, 'user_id': user_id}
                )
            
            # Record analytics in Cassandra
            cassandra_manager = self.managers['cassandra']
            cassandra_manager.record_analytics_metric(
                metric_name='ai_classifications',
                timestamp='current_timestamp()',
                dimension1='success',
                dimension2='plastic_metal',
                value=1.0
            )
            
            return classification_result
            
        except Exception as e:
            logger.error(f"Error in waste classification: {e}")
            return {}

# Global database manager instance
db_manager = DatabaseManager()