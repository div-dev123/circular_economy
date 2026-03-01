import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json
import hashlib
import secrets

logger = logging.getLogger(__name__)

class PostgreSQLManager:
    def __init__(self, host: str, port: int, database: str, username: str, password: str):
        try:
            # Try to connect with the provided credentials
            try:
                self.connection = psycopg2.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=username,
                    password=password,
                    cursor_factory=RealDictCursor
                )
            except psycopg2.OperationalError as e:
                if 'role' in str(e) and 'does not exist' in str(e):
                    logger.warning(f"Role '{username}' does not exist, trying with default 'postgres' role")
                    # Try to connect as default postgres user to create the needed role
                    try:
                        temp_conn = psycopg2.connect(
                            host=host,
                            port=port,
                            database='postgres',  # Connect to default database
                            user='postgres',
                            password='postgres',  # Default password
                            cursor_factory=RealDictCursor
                        )
                        temp_cursor = temp_conn.cursor()
                        # Create the user if it doesn't exist
                        temp_cursor.execute(f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '{username}') THEN CREATE USER {username} WITH PASSWORD '{password}'; END IF; END $$;")
                        temp_cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {database} TO {username};")
                        temp_conn.commit()
                        temp_conn.close()
                        
                        # Now try connecting with the created user
                        self.connection = psycopg2.connect(
                            host=host,
                            port=port,
                            database=database,
                            user=username,
                            password=password,
                            cursor_factory=RealDictCursor
                        )
                    except Exception as temp_e:
                        logger.error(f"Failed to create user or connect: {temp_e}")
                        raise
                else:
                    raise
            
            self.connection.autocommit = True
            self._create_tables()
            self._migrate_tables()
            logger.info("PostgreSQL connection successful")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    def close(self):
        if self.connection:
            self.connection.close()
    
    def _create_tables(self):
        """Create required tables"""
        cursor = self.connection.cursor()
        
        # Users table
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            salt VARCHAR(255) NOT NULL,
            company_name VARCHAR(255),
            industry_type VARCHAR(100),
            location VARCHAR(255),
            phone VARCHAR(20),
            is_active BOOLEAN DEFAULT TRUE,
            email_verified BOOLEAN DEFAULT FALSE,
            classifications_count INTEGER DEFAULT 0,
            listings_count INTEGER DEFAULT 0,
            waste_processed_tons DECIMAL(15,2) DEFAULT 0.00,
            co2_saved_tons DECIMAL(15,2) DEFAULT 0.00,
            cost_savings DECIMAL(15,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(users_table)
        
        # Companies table
        companies_table = """
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            industry_type VARCHAR(100) NOT NULL,
            location VARCHAR(255),
            capacity DECIMAL(10,2),
            certifications JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(companies_table)
        
        # Waste types table
        waste_types_table = """
        CREATE TABLE IF NOT EXISTS waste_types (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            category VARCHAR(50),
            processing_method VARCHAR(100),
            environmental_impact JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(waste_types_table)
        
        # Compliance standards table
        compliance_table = """
        CREATE TABLE IF NOT EXISTS compliance_standards (
            id SERIAL PRIMARY KEY,
            standard_name VARCHAR(100) NOT NULL,
            jurisdiction VARCHAR(100),
            requirements JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(compliance_table)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry_type)",
            "CREATE INDEX IF NOT EXISTS idx_companies_location ON companies(location)"
        ]
        
        for index_query in indexes:
            cursor.execute(index_query)
    
    # Approximate coordinates for Indian cities used in our seed data
    INDIAN_CITY_COORDS = {
        'mumbai': (19.0760, 72.8777),
        'jamnagar': (22.4707, 70.0577),
        'pune': (18.5204, 73.8567),
        'noida': (28.5355, 77.3910),
        'nashik': (19.9975, 73.7898),
        'jodhpur': (26.2389, 73.0243),
        'chennai': (13.0827, 80.2707),
        'thane': (19.2183, 72.9781),
        'ahmedabad': (23.0225, 72.5714),
        'hyderabad': (17.3850, 78.4867),
        'panaji': (15.4909, 73.8278),
        'renukoot': (24.2167, 83.0333),
        'anand': (22.5645, 72.9289),
        'bangalore': (12.9716, 77.5946),
        'vadodara': (22.3072, 73.1812),
        'gurugram': (28.4595, 77.0266),
        'kochi': (9.9312, 76.2673),
        'kolkata': (22.5726, 88.3639),
        'nagpur': (21.1458, 79.0882),
        'delhi': (28.6139, 77.2090),
        'new delhi': (28.6139, 77.2090),
        'lucknow': (26.8467, 80.9462),
        'jaipur': (26.9124, 75.7873),
        'bhopal': (23.2599, 77.4126),
        'indore': (22.7196, 75.8577),
        'chandigarh': (30.7333, 76.7794),
        'coimbatore': (11.0168, 76.9558),
        'visakhapatnam': (17.6868, 83.2185),
        'surat': (21.1702, 72.8311),
        'patna': (25.6093, 85.1376),
    }

    def _geocode_location(self, location: str):
        """Return (lat, lng) for a location string like 'Mumbai, Maharashtra'"""
        if not location:
            return None, None
        city = location.split(',')[0].strip().lower()
        coords = self.INDIAN_CITY_COORDS.get(city)
        if coords:
            return coords
        return None, None

    def _migrate_tables(self):
        """Run migrations to update table schemas"""
        cursor = self.connection.cursor()
        
        # Add stats columns to users table if they don't exist
        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS classifications_count INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS listings_count INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS waste_processed_tons DECIMAL(15,2) DEFAULT 0.00",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS co2_saved_tons DECIMAL(15,2) DEFAULT 0.00",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS cost_savings DECIMAL(15,2) DEFAULT 0.00",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION"
        ]
        
        for migration in migrations:
            try:
                cursor.execute(migration)
            except Exception as e:
                logger.warning(f"Migration skipped (column may already exist): {e}")

        # Backfill lat/lng for existing users who have a location but no coordinates
        try:
            cursor.execute("SELECT id, location FROM users WHERE location IS NOT NULL AND latitude IS NULL")
            rows = cursor.fetchall()
            for row in rows:
                lat, lng = self._geocode_location(row['location'])
                if lat and lng:
                    cursor.execute("UPDATE users SET latitude = %s, longitude = %s WHERE id = %s",
                                   (lat, lng, row['id']))
            if rows:
                logger.info(f"Backfilled coordinates for {len(rows)} users")
        except Exception as e:
            logger.warning(f"Coordinate backfill skipped: {e}")
    
    # User Management
    def create_user(self, user_data: Dict[str, Any]) -> int:
        """Create a new user"""
        cursor = self.connection.cursor()
        query = """
        INSERT INTO users (email, company_name, industry_type, location, phone)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        cursor.execute(query, (
            user_data['email'],
            user_data.get('company_name'),
            user_data.get('industry_type'),
            user_data.get('location'),
            user_data.get('phone')
        ))
        result = cursor.fetchone()
        logger.info(f"Created user with ID: {result['id']}")
        return result['id']
    
    def hash_password(self, password: str, salt: str = None) -> tuple:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_hash.hex(), salt
    
    def create_user_with_password(self, user_data: Dict[str, Any]) -> int:
        """Create a new user with password"""
        cursor = self.connection.cursor()
        
        # Hash the password
        password_hash, salt = self.hash_password(user_data['password'])
        
        query = """
        INSERT INTO users (email, password_hash, salt, company_name, industry_type, location, phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        cursor.execute(query, (
            user_data['email'],
            password_hash,
            salt,
            user_data.get('company_name'),
            user_data.get('industry_type'),
            user_data.get('location'),
            user_data.get('phone')
        ))
        result = cursor.fetchone()
        logger.info(f"Created user with ID: {result['id']}")
        return result['id']
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password"""
        cursor = self.connection.cursor()
        query = "SELECT * FROM users WHERE email = %s AND is_active = TRUE"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        
        if user:
            # Verify password
            stored_hash = user['password_hash']
            salt = user['salt']
            password_hash, _ = self.hash_password(password, salt)
            
            if password_hash == stored_hash:
                # Return user data without password fields
                user_data = dict(user)
                del user_data['password_hash']
                del user_data['salt']
                return user_data
        
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        cursor = self.connection.cursor()
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        
        if result:
            # Return user data without password fields
            user_data = dict(result)
            del user_data['password_hash']
            del user_data['salt']
            return user_data
        
        return None
    
    def get_user_companies(self, user_id: int) -> List[Dict]:
        """Get companies associated with user"""
        cursor = self.connection.cursor()
        query = """
        SELECT c.* FROM companies c
        JOIN user_companies uc ON c.id = uc.company_id
        WHERE uc.user_id = %s
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    
    # Company Management
    def create_company(self, company_data: Dict[str, Any]) -> int:
        """Create a new company"""
        cursor = self.connection.cursor()
        query = """
        INSERT INTO companies (name, industry_type, location, capacity, certifications)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        cursor.execute(query, (
            company_data['name'],
            company_data['industry_type'],
            company_data.get('location'),
            company_data.get('capacity'),
            json.dumps(company_data.get('certifications', {}))
        ))
        result = cursor.fetchone()
        logger.info(f"Created company with ID: {result['id']}")
        return result['id']
    
    def get_companies_by_industry(self, industry_type: str) -> List[Dict]:
        """Get companies by industry type"""
        cursor = self.connection.cursor()
        query = "SELECT * FROM companies WHERE industry_type = %s"
        cursor.execute(query, (industry_type,))
        return cursor.fetchall()
    
    def get_companies_by_location(self, location: str) -> List[Dict]:
        """Get companies by location"""
        cursor = self.connection.cursor()
        query = "SELECT * FROM companies WHERE location ILIKE %s"
        cursor.execute(query, (f"%{location}%",))
        return cursor.fetchall()
    
    # Waste Type Management
    def create_waste_type(self, waste_data: Dict[str, Any]) -> int:
        """Create a new waste type"""
        cursor = self.connection.cursor()
        query = """
        INSERT INTO waste_types (name, category, processing_method, environmental_impact)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """
        cursor.execute(query, (
            waste_data['name'],
            waste_data.get('category'),
            waste_data.get('processing_method'),
            json.dumps(waste_data.get('environmental_impact', {}))
        ))
        result = cursor.fetchone()
        logger.info(f"Created waste type with ID: {result['id']}")
        return result['id']
    
    def get_waste_type_by_name(self, name: str) -> Optional[Dict]:
        """Get waste type by name"""
        cursor = self.connection.cursor()
        query = "SELECT * FROM waste_types WHERE name = %s"
        cursor.execute(query, (name,))
        return cursor.fetchone()
    
    def get_all_waste_types(self) -> List[Dict]:
        """Get all waste types"""
        cursor = self.connection.cursor()
        query = "SELECT * FROM waste_types ORDER BY name"
        cursor.execute(query)
        return cursor.fetchall()
    
    # Compliance Management
    def create_compliance_standard(self, compliance_data: Dict[str, Any]) -> int:
        """Create a new compliance standard"""
        cursor = self.connection.cursor()
        query = """
        INSERT INTO compliance_standards (standard_name, jurisdiction, requirements)
        VALUES (%s, %s, %s)
        RETURNING id
        """
        cursor.execute(query, (
            compliance_data['standard_name'],
            compliance_data.get('jurisdiction'),
            json.dumps(compliance_data.get('requirements', {}))
        ))
        result = cursor.fetchone()
        logger.info(f"Created compliance standard with ID: {result['id']}")
        return result['id']
    
    def get_compliance_standards(self, jurisdiction: str = None) -> List[Dict]:
        """Get compliance standards"""
        cursor = self.connection.cursor()
        if jurisdiction:
            query = "SELECT * FROM compliance_standards WHERE jurisdiction = %s"
            cursor.execute(query, (jurisdiction,))
        else:
            query = "SELECT * FROM compliance_standards"
            cursor.execute(query)
        return cursor.fetchall()
    
    # Reporting and Analytics
    def get_industry_statistics(self) -> List[Dict]:
        """Get industry statistics"""
        cursor = self.connection.cursor()
        query = """
        SELECT 
            industry_type,
            COUNT(*) as company_count,
            AVG(capacity) as avg_capacity
        FROM companies
        GROUP BY industry_type
        ORDER BY company_count DESC
        """
        cursor.execute(query)
        return cursor.fetchall()
    
    def get_location_statistics(self) -> List[Dict]:
        """Get location-based statistics"""
        cursor = self.connection.cursor()
        query = """
        SELECT 
            location,
            COUNT(*) as company_count
        FROM companies
        WHERE location IS NOT NULL
        GROUP BY location
        ORDER BY company_count DESC
        LIMIT 20
        """
        cursor.execute(query)
        return cursor.fetchall()
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report"""
        cursor = self.connection.cursor()
        
        # Get total companies
        cursor.execute("SELECT COUNT(*) as total_companies FROM companies")
        total_companies = cursor.fetchone()['total_companies']
        
        # Get companies by compliance status (simplified)
        cursor.execute("""
            SELECT 
                COUNT(*) as compliant_companies
            FROM companies 
            WHERE certifications IS NOT NULL 
            AND certifications != '{}'
        """)
        compliant_companies = cursor.fetchone()['compliant_companies']
        
        return {
            'total_companies': total_companies,
            'compliant_companies': compliant_companies,
            'compliance_rate': round((compliant_companies / total_companies * 100), 2) if total_companies > 0 else 0
        }
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        cursor = self.connection.cursor()
        query = "SELECT * FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        if result:
            # Return user data without password fields
            user_data = dict(result)
            if 'password_hash' in user_data:
                del user_data['password_hash']
            if 'salt' in user_data:
                del user_data['salt']
            return user_data
        
        return None
    
    # Waste-to-Industry Matching
    WASTE_INDUSTRY_MAP = {
        'metal': ['Steel', 'Aluminum', 'Metals & Mining', 'Automobile', 'Manufacturing', 'Construction'],
        'plastic': ['Plastics', 'Manufacturing', 'Rubber', 'Chemicals', 'Automobile'],
        'paper/cardboard': ['Paper & Pulp', 'Manufacturing', 'Food Processing'],
        'glass': ['Glass', 'Ceramics', 'Construction', 'Manufacturing'],
        'organic': ['Agriculture', 'Food Processing', 'Renewable Energy'],
        'textile': ['Textiles', 'Leather', 'Manufacturing'],
        'construction': ['Construction', 'Cement', 'Manufacturing', 'Steel'],
        'hazardous': ['Chemicals', 'Pharmaceuticals', 'Refinery'],
        'industrial ash': ['Cement', 'Construction', 'Renewable Energy'],
        'electronic': ['Electronics', 'IT Hardware', 'Metals & Mining', 'Manufacturing'],
        'mixed': ['Manufacturing', 'Renewable Energy', 'Chemicals', 'Construction'],
    }

    def get_matching_companies(self, waste_type: str, exclude_user_id: int = None) -> List[Dict]:
        """Find registered companies whose industry matches a waste classification type"""
        cursor = self.connection.cursor()
        industries = self.WASTE_INDUSTRY_MAP.get(waste_type.lower(), [])
        if not industries:
            return []

        placeholders = ','.join(['%s'] * len(industries))
        query = f"""
            SELECT id, email, company_name, industry_type, location
            FROM users
            WHERE industry_type IN ({placeholders})
              AND is_active = TRUE
        """
        params = list(industries)

        if exclude_user_id:
            query += " AND id != %s"
            params.append(exclude_user_id)

        query += " ORDER BY company_name"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Update user profile"""
        cursor = self.connection.cursor()
        
        # Build dynamic UPDATE query
        update_fields = []
        values = []
        
        allowed_fields = ['company_name', 'industry_type', 'location', 'phone']
        
        for field in allowed_fields:
            if field in user_data:
                update_fields.append(f"{field} = %s")
                values.append(user_data[field])
        
        # Auto-geocode if location changed
        if 'location' in user_data:
            lat, lng = self._geocode_location(user_data['location'])
            if lat and lng:
                update_fields.extend(['latitude = %s', 'longitude = %s'])
                values.extend([lat, lng])
        
        if not update_fields:
            return False
        
        # Add updated_at timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        
        try:
            cursor.execute(query, values)
            logger.info(f"Updated user with ID: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False

    def get_all_users_for_map(self, industry_filter: str = None) -> List[Dict]:
        """Get all users with coordinates for the map view"""
        cursor = self.connection.cursor()
        query = """
            SELECT id, company_name, industry_type, location, latitude, longitude,
                   classifications_count, listings_count, email
            FROM users
            WHERE is_active = TRUE AND latitude IS NOT NULL AND longitude IS NOT NULL
        """
        params = []
        if industry_filter and industry_filter != 'all':
            query += " AND industry_type = %s"
            params.append(industry_filter)
        query += " ORDER BY company_name"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_distinct_industry_types(self) -> List[str]:
        """Get all distinct industry types from users table"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT DISTINCT industry_type FROM users
            WHERE industry_type IS NOT NULL AND is_active = TRUE
            ORDER BY industry_type
        """)
        return [row['industry_type'] for row in cursor.fetchall()]