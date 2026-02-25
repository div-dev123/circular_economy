import redis
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self, host: str, port: int, db: int, password: str = None):
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                health_check_interval=30
            )
            self.client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    def close(self):
        self.client.close()
    
    # Session Management
    def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create user session"""
        session_key = f"session:{user_id}:{self._generate_session_id()}"
        session_data['created_at'] = datetime.utcnow().isoformat()
        session_data['user_id'] = user_id
        
        self.client.hset(session_key, mapping=session_data)
        self.client.expire(session_key, 3600)  # 1 hour expiry
        logger.info(f"Created session: {session_key}")
        return session_key
    
    def get_session(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if self.client.exists(session_key):
            return self.client.hgetall(session_key)
        return None
    
    def extend_session(self, session_key: str) -> bool:
        """Extend session expiry"""
        if self.client.exists(session_key):
            self.client.expire(session_key, 3600)
            return True
        return False
    
    def delete_session(self, session_key: str) -> bool:
        """Delete session"""
        return bool(self.client.delete(session_key))
    
    # Caching
    def cache_waste_classification(self, image_hash: str, result: Dict[str, Any], 
                                 ttl: int = 3600) -> None:
        """Cache AI classification results"""
        cache_key = f"classification:{image_hash}"
        self.client.setex(
            cache_key,
            ttl,
            json.dumps(result)
        )
        logger.info(f"Cached classification result for {image_hash}")
    
    def get_cached_classification(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached classification result"""
        cache_key = f"classification:{image_hash}"
        cached = self.client.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    
    def cache_waste_search(self, query: str, results: List[Dict], 
                          ttl: int = 1800) -> None:
        """Cache waste search results"""
        cache_key = f"search:{hash(query)}:{query}"
        self.client.setex(
            cache_key,
            ttl,
            json.dumps(results)
        )
    
    def get_cached_search(self, query: str) -> Optional[List[Dict]]:
        """Get cached search results"""
        cache_key = f"search:{hash(query)}:{query}"
        cached = self.client.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    
    # Real-time Data
    def increment_waste_views(self, waste_id: str) -> int:
        """Track waste listing views"""
        key = f"views:waste:{waste_id}"
        return self.client.incr(key)
    
    def get_waste_views(self, waste_id: str) -> int:
        """Get view count for waste listing"""
        key = f"views:waste:{waste_id}"
        count = self.client.get(key)
        return int(count) if count else 0
    
    def track_user_interaction(self, user_id: str, waste_id: str, 
                              interaction_type: str) -> None:
        """Track user interaction with waste listing"""
        timestamp = datetime.utcnow().isoformat()
        
        # Add to sorted set for recent interactions
        interaction_key = f"interactions:user:{user_id}"
        score = datetime.utcnow().timestamp()
        self.client.zadd(
            interaction_key,
            {f"{waste_id}:{interaction_type}:{timestamp}": score}
        )
        
        # Keep only last 1000 interactions
        self.client.zremrangebyrank(interaction_key, 0, -1001)
    
    def get_recent_interactions(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's recent interactions"""
        interaction_key = f"interactions:user:{user_id}"
        interactions = self.client.zrevrange(interaction_key, 0, limit-1)
        
        results = []
        for interaction in interactions:
            waste_id, interaction_type, timestamp = interaction.split(':', 2)
            results.append({
                'waste_id': waste_id,
                'type': interaction_type,
                'timestamp': timestamp
            })
        return results
    
    # Real-time Matching
    def add_waste_to_matching_pool(self, waste_id: str, waste_data: Dict[str, Any]) -> None:
        """Add waste to real-time matching pool"""
        matching_key = "matching_pool:waste"
        score = datetime.utcnow().timestamp()
        self.client.zadd(matching_key, {waste_id: score})
        
        # Store waste data
        data_key = f"waste_data:{waste_id}"
        self.client.hset(data_key, mapping=waste_data)
        self.client.expire(data_key, 3600)  # 1 hour expiry
    
    def get_matching_candidates(self, waste_type: str, location: str = None, 
                              limit: int = 10) -> List[Dict[str, Any]]:
        """Get potential matching candidates"""
        # This would be enhanced with geospatial and compatibility logic
        matching_key = "matching_pool:waste"
        waste_ids = self.client.zrange(matching_key, 0, limit-1)
        
        candidates = []
        for waste_id in waste_ids:
            data_key = f"waste_data:{waste_id}"
            data = self.client.hgetall(data_key)
            if data and data.get('waste_type') == waste_type:
                candidates.append({
                    'waste_id': waste_id,
                    'data': data
                })
        
        return candidates[:limit]
    
    # Notifications
    def publish_notification(self, channel: str, message: Dict[str, Any]) -> None:
        """Publish notification to channel"""
        self.client.publish(channel, json.dumps(message))
    
    def subscribe_to_notifications(self, channel: str) -> redis.client.PubSub:
        """Subscribe to notification channel"""
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)
        return pubsub
    
    # Rate Limiting
    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limit is exceeded"""
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, window)
        return current <= limit
    
    def get_rate_limit_info(self, key: str) -> Dict[str, Any]:
        """Get rate limit information"""
        current = self.client.get(key)
        ttl = self.client.ttl(key)
        return {
            'current': int(current) if current else 0,
            'ttl': ttl if ttl > 0 else 0
        }
    
    # Helper Methods
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid
        return str(uuid.uuid4())