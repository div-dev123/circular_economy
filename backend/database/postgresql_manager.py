import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class PostgreSQLManager:
    def __init__(self, host: str, port: int, database: str, username: str, password: str):
        try:
            self.connection = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password,
                cursor_factory=RealDictCursor
            )
            self.connection.autocommit = True
            self._create_tables()
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
            company_name VARCHAR(255),
            industry_type VARCHAR(100),
            location VARCHAR(255),
            phone VARCHAR(20),
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
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        cursor = self.connection.cursor()
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        return cursor.fetchone()
    
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