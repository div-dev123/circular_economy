from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
import logging
from datetime import datetime
from .config import DATABASE_CONFIG

logger = logging.getLogger(__name__)

# Safely import managers so a missing optional driver doesn't crash the entire platform
try:
    from .postgresql_manager import PostgreSQLManager
except Exception as e:
    PostgreSQLManager = None
    logger.warning(f"PostgreSQLManager not available: {e}")

try:
    from .redis_manager import RedisManager
except Exception as e:
    RedisManager = None
    logger.warning(f"RedisManager not available: {e}")

try:
    from .mongodb_manager import MongoDBManager
except Exception as e:
    MongoDBManager = None
    logger.warning(f"MongoDBManager not available: {e}")

try:
    from .neo4j_manager import Neo4jManager
except Exception as e:
    Neo4jManager = None
    logger.warning(f"Neo4jManager not available: {e}")

try:
    from .cassandra_manager import CassandraManager
except Exception as e:
    CassandraManager = None
    logger.warning(f"CassandraManager not available: {e}")

class DatabaseManager:
    def __init__(self):
        self.managers: Dict[str, Any] = {}
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize all available database connections"""
        # PostgreSQL (Relational Core)
        if PostgreSQLManager:
            try:
                postgres_config = DATABASE_CONFIG.get('postgresql', {})
                self.managers['postgresql'] = PostgreSQLManager(
                    host=postgres_config['host'],
                    port=postgres_config['port'],
                    database=postgres_config['database'],
                    username=postgres_config['username'],
                    password=postgres_config['password'],
                    sslmode=postgres_config.get('sslmode')
                )
                logger.info("PostgreSQL connection initialized")
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed: {e}")

        # Redis (Key-Value / Cache)
        if RedisManager:
            try:
                redis_config = DATABASE_CONFIG.get('redis', {})
                # Only attempt connection if URL or host is configured and not default unconfigured localhost on remote
                if redis_config.get('url') or (redis_config.get('host') and redis_config.get('password')):
                    self.managers['redis'] = RedisManager(
                        host=redis_config.get('host', 'localhost'),
                        port=redis_config.get('port', 6379),
                        db=redis_config.get('db', 0),
                        password=redis_config.get('password'),
                        url=redis_config.get('url')
                    )
                    logger.info("Redis connection initialized")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")

        # MongoDB (Document DB)
        if MongoDBManager:
            try:
                mongo_config = DATABASE_CONFIG.get('mongodb', {})
                # Only attempt if non-localhost URI is configured
                mongo_uri = mongo_config.get('uri', '')
                if mongo_uri and 'localhost' not in mongo_uri and '127.0.0.1' not in mongo_uri:
                    self.managers['mongodb'] = MongoDBManager(
                        uri=mongo_uri,
                        database=mongo_config.get('database', 'circular_economy')
                    )
                    logger.info("MongoDB connection initialized")
            except Exception as e:
                logger.warning(f"MongoDB connection failed: {e}")

        # Neo4j (Graph DB)
        if Neo4jManager:
            try:
                neo4j_config = DATABASE_CONFIG.get('neo4j', {})
                neo_uri = neo4j_config.get('uri', '')
                if neo_uri and 'localhost' not in neo_uri and '127.0.0.1' not in neo_uri:
                    self.managers['neo4j'] = Neo4jManager(
                        uri=neo_uri,
                        username=neo4j_config.get('username', 'neo4j'),
                        password=neo4j_config.get('password', '')
                    )
                    logger.info("Neo4j connection initialized")
            except Exception as e:
                logger.warning(f"Neo4j connection failed: {e}")

        # Cassandra (Column-Family)
        if CassandraManager:
            try:
                cassandra_config = DATABASE_CONFIG.get('cassandra', {})
                cass_hosts = cassandra_config.get('hosts', [])
                if cass_hosts and cass_hosts != ['127.0.0.1'] and cass_hosts != ['localhost']:
                    self.managers['cassandra'] = CassandraManager(
                        hosts=cass_hosts,
                        keyspace=cassandra_config.get('keyspace', 'circular_economy'),
                        port=cassandra_config.get('port', 9042)
                    )
                    logger.info("Cassandra connection initialized")
            except Exception as e:
                logger.warning(f"Cassandra connection failed: {e}")
    
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
            postgres_manager = self.managers.get('postgresql')
            if postgres_manager:
                transaction_id = postgres_manager.record_transaction(transaction_data)
            else:
                # Generate a transaction ID if PostgreSQL is not available
                from uuid import uuid4
                transaction_id = str(uuid4())
                logger.warning("PostgreSQL not available, using generated transaction ID")
            
            # MongoDB: Store user profile update
            if 'user_id' in transaction_data:
                mongo_manager = self.managers.get('mongodb')
                if mongo_manager:
                    mongo_manager.update_user(str(transaction_data['user_id']), {
                        'last_transaction_at': datetime.utcnow()
                    })
            
            # Cassandra: Store analytics and audit logs
            cassandra_manager = self.managers.get('cassandra')
            if cassandra_manager:
                cassandra_manager.record_transaction(transaction_data)
                cassandra_manager.log_audit_event(
                    user_id=str(transaction_data.get('user_id', '')),
                    action='CREATE_TRANSACTION',
                    resource_type='transaction',
                    resource_id=transaction_id,
                    details=f"Created transaction for {transaction_data.get('waste_type')}"
                )
            
            # Redis: Update real-time metrics
            redis_manager: Optional[RedisManager] = self.managers.get('redis')
            if redis_manager:
                redis_manager.increment_waste_views(str(transaction_data.get('waste_id', '')))
            
            # Neo4j: Update supply chain relationships
            neo4j_manager: Optional[Neo4jManager] = self.managers.get('neo4j')
            if neo4j_manager and 'waste_id' in transaction_data and 'industry_id' in transaction_data:
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
            redis_manager = self.managers.get('redis')
            if redis_manager:
                cache_key = f"search:{hash(query)}:{query}"
                cached_results = redis_manager.get_cached_search(query)
                
                if cached_results:
                    logger.info("Returning cached search results")
                    return cached_results
            
            # MongoDB: Perform actual search
            mongo_manager: Optional[MongoDBManager] = self.managers.get('mongodb')
            if mongo_manager:
                results = mongo_manager.search_waste_listings(query, location)
            else:
                results = []
                logger.warning("MongoDB not available, returning empty results")
            
            # PostgreSQL: Get user preferences for personalized results
            if user_id:
                postgres_manager: Optional[PostgreSQLManager] = self.managers.get('postgresql')
                if postgres_manager:
                    user_companies = postgres_manager.get_user_companies(int(user_id))
                    # Apply personalization logic here
                    
            # Cassandra: Record search analytics
            cassandra_manager = self.managers.get('cassandra')
            if cassandra_manager:
                cassandra_manager.record_analytics_metric(
                    metric_name='search_queries',
                    timestamp=datetime.utcnow(),
                    dimension1=query,
                    dimension2=location or 'global',
                    value=1.0
                )
            
            # Cache results in Redis
            if redis_manager:
                redis_manager.cache_waste_search(query, results, ttl=1800)
            
            # Track user interaction in Redis
            if user_id and redis_manager:
                redis_manager.track_user_interaction(user_id, 'search', 'query')
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching waste listings: {e}")
            return []
    
    def get_supply_chain_insights(self, waste_type: str) -> Dict[str, Any]:
        """Get comprehensive supply chain insights using graph database"""
        try:
            # Initialize default values
            industries = []
            pathways = []
            industry_stats = {}
            trends = []
            
            # Neo4j: Get industry connections and pathways
            neo4j_manager: Optional[Neo4jManager] = self.managers.get('neo4j')
            if neo4j_manager:
                industries = neo4j_manager.find_industries_for_waste(waste_type)
                pathways = neo4j_manager.get_circular_economy_pathways(waste_type)
            
            # PostgreSQL: Get industry statistics
            postgres_manager: Optional[PostgreSQLManager] = self.managers.get('postgresql')
            if postgres_manager:
                industry_stats = postgres_manager.get_industry_statistics()
            
            # Cassandra: Get historical trends
            cassandra_manager: Optional[CassandraManager] = self.managers.get('cassandra')
            if cassandra_manager:
                trends = cassandra_manager.get_waste_diversion_trends(days=90)
            
            # Redis: Get real-time metrics
            redis_manager: Optional[RedisManager] = self.managers.get('redis')
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
            # Initialize default values
            co2_savings = 0.0
            trends = []
            compliance_report = {}
            user_stats = {}
            
            # Cassandra: Get environmental metrics
            cassandra_manager: Optional[CassandraManager] = self.managers.get('cassandra')
            if cassandra_manager:
                co2_savings = cassandra_manager.get_co2_savings_by_month(2026, 2)
                trends = cassandra_manager.get_waste_diversion_trends(days=365)
            
            # PostgreSQL: Get compliance data
            postgres_manager: Optional[PostgreSQLManager] = self.managers.get('postgresql')
            if postgres_manager:
                compliance_report = postgres_manager.get_compliance_report()
            
            # MongoDB: Get user-specific statistics
            if user_id:
                mongo_manager: Optional[MongoDBManager] = self.managers.get('mongodb')
                if mongo_manager:
                    user_stats = mongo_manager.get_waste_statistics(user_id)
            
            # Redis: Get real-time engagement metrics
            redis_manager: Optional[RedisManager] = self.managers.get('redis')
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
            redis_manager: Optional[RedisManager] = self.managers.get('redis')
            if redis_manager:
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
                'estimated_value': '₹10,000-15,000 per tonne',
                'processing_time': '2.3s'
            }
            
            # Cache the result
            if redis_manager:
                redis_manager.cache_waste_classification(image_hash, classification_result)
            
            # Store in MongoDB for user history
            if user_id:
                mongo_manager: Optional[MongoDBManager] = self.managers.get('mongodb')
                if mongo_manager:
                    mongo_manager.store_waste_image(
                        image_bytes, 
                        f"waste_{image_hash}.jpg",
                        {'classification_result': classification_result, 'user_id': user_id}
                    )
            
            # Record analytics in Cassandra
            cassandra_manager: Optional[CassandraManager] = self.managers.get('cassandra')
            if cassandra_manager:
                cassandra_manager.record_analytics_metric(
                    metric_name='ai_classifications',
                    timestamp=datetime.utcnow(),
                    dimension1='success',
                    dimension2='plastic_metal',
                    value=1.0
                )
            
            return classification_result
            
        except Exception as e:
            logger.error(f"Error in waste classification: {e}")
            return {}
    
    def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user with password"""
        try:
            postgres_manager: Optional[PostgreSQLManager] = self.managers.get('postgresql')
            if not postgres_manager:
                return {'error': 'Database not available'}
            
            # Check if user already exists
            existing_user = postgres_manager.get_user_by_email(user_data['email'])
            if existing_user:
                return {'error': 'Email already registered'}
            
            # Create user with password
            user_id = postgres_manager.create_user_with_password(user_data)
            
            # Get the full user object
            user = postgres_manager.get_user_by_id(user_id)
            
            # Optionally create corresponding entries in other databases
            # Create user profile in MongoDB
            mongo_manager: Optional[MongoDBManager] = self.managers.get('mongodb')
            if mongo_manager:
                mongo_manager.create_user_profile({
                    'user_id': user_id,
                    'email': user_data['email'],
                    'company_name': user_data.get('company_name', ''),
                    'industry_type': user_data.get('industry_type', ''),
                    'location': user_data.get('location', ''),
                    'created_at': datetime.utcnow()
                })
            
            # Create company node in Neo4j
            neo4j_manager: Optional[Neo4jManager] = self.managers.get('neo4j')
            if neo4j_manager:
                try:
                    neo4j_manager.create_industry_node(
                        industry_id=str(user_id),
                        industry_type=user_data.get('industry_type', 'Manufacturing'),
                        location=user_data.get('location', 'India'),
                        capacity=100.0 # Default starting capacity
                    )
                except Exception as ne:
                    logger.warning(f"Failed to create Neo4j node for user {user_id}: {ne}")
            
            # Log the registration in Cassandra
            cassandra_manager: Optional[CassandraManager] = self.managers.get('cassandra')
            if cassandra_manager:
                cassandra_manager.record_analytics_metric(
                    metric_name='user_registrations',
                    timestamp=datetime.utcnow(),
                    dimension1=user_data.get('industry_type', 'unknown'),
                    dimension2='success',
                    value=1.0
                )
            
            return {'success': True, 'user_id': user_id, 'user': user}
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return {'error': str(e)}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        try:
            postgres_manager: Optional[PostgreSQLManager] = self.managers.get('postgresql')
            if not postgres_manager:
                return {'error': 'Database not available'}
            
            user = postgres_manager.authenticate_user(email, password)
            
            if user:
                # Update last login in MongoDB if available
                mongo_manager: Optional[MongoDBManager] = self.managers.get('mongodb')
                if mongo_manager:
                    try:
                        mongo_manager.update_user(str(user['id']), {
                            'last_login_at': datetime.utcnow()
                        })
                    except Exception:
                        pass  # Continue even if MongoDB update fails
                
                # Log the login in Cassandra
                cassandra_manager: Optional[CassandraManager] = self.managers.get('cassandra')
                if cassandra_manager:
                    cassandra_manager.record_analytics_metric(
                        metric_name='user_logins',
                        timestamp=datetime.utcnow(),
                        dimension1=user.get('industry_type', 'unknown'),
                        dimension2='success',
                        value=1.0
                    )
                
                return {'success': True, 'user': user}
            else:
                # Log failed login attempt
                cassandra_manager = self.managers.get('cassandra')
                if cassandra_manager:
                    cassandra_manager.record_analytics_metric(
                        metric_name='failed_logins',
                        timestamp=datetime.utcnow(),
                        dimension1=email.split('@')[1] if '@' in email else 'unknown',
                        dimension2='authentication_failed',
                        value=1.0
                    )
                
                return {'success': False, 'error': 'Invalid credentials'}
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return {'error': str(e)}

# Global database manager instance
db_manager = DatabaseManager()