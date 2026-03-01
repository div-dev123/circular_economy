from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import gridfs

logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self, uri: str, database: str):
        try:
            self.client = MongoClient(uri)
            self.client.admin.command('ping')  # Test connection
            self.db = self.client[database]
            self.fs = gridfs.GridFS(self.db)
            logger.info("MongoDB connection successful")
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    def close(self):
        self.client.close()
    
    # User Management
    def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user profile"""
        user_data['created_at'] = datetime.utcnow()
        user_data['updated_at'] = datetime.utcnow()
        result = self.db.users.insert_one(user_data)
        logger.info(f"Created user: {result.inserted_id}")
        return str(result.inserted_id)
    
    def create_user_profile(self, user_data: Dict[str, Any]) -> str:
        """Create a new user profile in MongoDB"""
        user_data['created_at'] = datetime.utcnow()
        user_data['updated_at'] = datetime.utcnow()
        result = self.db.users.insert_one(user_data)
        logger.info(f"Created user profile: {result.inserted_id}")
        return str(result.inserted_id)
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        return self.db.users.find_one({'_id': user_id})
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user profile"""
        update_data['updated_at'] = datetime.utcnow()
        result = self.db.users.update_one(
            {'_id': user_id},
            {'$set': update_data}
        )
        return result.modified_count > 0
    
    def get_user_transactions(self, user_id: str) -> List[Dict]:
        """Get user's transaction history"""
        pipeline = [
            {'$match': {'user_id': user_id}},
            {'$sort': {'created_at': -1}},
            {'$limit': 50}
        ]
        return list(self.db.transactions.aggregate(pipeline))
    
    # Waste Listings
    def create_waste_listing(self, listing_data: Dict[str, Any]) -> str:
        """Create a new waste listing"""
        listing_data['created_at'] = datetime.utcnow()
        listing_data['updated_at'] = datetime.utcnow()
        listing_data['status'] = 'active'
        
        result = self.db.waste_listings.insert_one(listing_data)
        logger.info(f"Created waste listing: {result.inserted_id}")
        return str(result.inserted_id)
    
    def get_waste_listings(self, filters: Dict[str, Any] = None, 
                          limit: int = 20, offset: int = 0) -> List[Dict]:
        """Get waste listings with filtering"""
        if filters is None:
            filters = {}
        
        # Add status filter
        filters['status'] = 'active'
        
        cursor = self.db.waste_listings.find(filters)
        cursor = cursor.sort('created_at', -1)
        cursor = cursor.skip(offset).limit(limit)
        
        return list(cursor)
    
    def search_waste_listings(self, query: str, location: str = None) -> List[Dict]:
        """Search waste listings by text and location"""
        text_search = {
            '$text': {'$search': query}
        }
        
        if location:
            text_search['location'] = {
                '$regex': location, '$options': 'i'
            }
        
        cursor = self.db.waste_listings.find(text_search)
        cursor = cursor.sort('created_at', -1).limit(20)
        
        return list(cursor)
    
    def get_waste_by_location(self, location: str, radius_km: float = 50) -> List[Dict]:
        """Get waste listings near specific location"""
        # Assuming geospatial indexing is set up
        pipeline = [
            {
                '$geoNear': {
                    'near': {
                        'type': 'Point',
                        'coordinates': [0, 0]  # Replace with actual coordinates
                    },
                    'distanceField': 'distance',
                    'maxDistance': radius_km * 1000,
                    'spherical': True
                }
            },
            {'$match': {'status': 'active'}},
            {'$sort': {'distance': 1}},
            {'$limit': 50}
        ]
        
        return list(self.db.waste_listings.aggregate(pipeline))
    
    # Image Management
    def store_waste_image(self, image_bytes: bytes, filename: str, 
                         metadata: Dict[str, Any]) -> str:
        """Store waste image with metadata"""
        metadata['uploaded_at'] = datetime.utcnow()
        file_id = self.fs.put(
            image_bytes,
            filename=filename,
            metadata=metadata
        )
        return str(file_id)
    
    def get_waste_image(self, file_id: str) -> Optional[bytes]:
        """Retrieve waste image"""
        try:
            return self.fs.get(file_id).read()
        except Exception as e:
            logger.error(f"Error retrieving image {file_id}: {e}")
            return None
    
    # Analytics
    def get_waste_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """Get waste listing statistics"""
        pipeline = [
            {'$group': {
                '_id': '$waste_type',
                'count': {'$sum': 1},
                'total_quantity': {'$sum': '$quantity'},
                'avg_price': {'$avg': '$price_per_ton'}
            }},
            {'$sort': {'count': -1}}
        ]
        
        if user_id:
            pipeline.insert(0, {'$match': {'user_id': user_id}})
        
        results = list(self.db.waste_listings.aggregate(pipeline))
        
        return {
            'by_type': results,
            'total_listings': sum(r['count'] for r in results),
            'total_quantity': sum(r['total_quantity'] for r in results)
        }
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's waste type preferences"""
        pipeline = [
            {'$match': {'user_id': user_id}},
            {'$group': {
                '_id': '$waste_type',
                'interaction_count': {'$sum': 1},
                'last_interaction': {'$max': '$created_at'}
            }},
            {'$sort': {'interaction_count': -1}},
            {'$limit': 10}
        ]
        
        results = list(self.db.user_interactions.aggregate(pipeline))
        return {'preferences': results}