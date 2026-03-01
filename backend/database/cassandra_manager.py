from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class CassandraManager:
    def __init__(self, hosts: List[str], keyspace: str, port: int = 9042):
        try:
            self.cluster = Cluster(hosts, port=port)
            self.session = self.cluster.connect()
            self.keyspace = keyspace
            
            # Create keyspace if it doesn't exist
            self._create_keyspace()
            self.session.set_keyspace(keyspace)
            
            # Create tables
            self._create_tables()
            logger.info("Cassandra connection successful")
        except Exception as e:
            logger.error(f"Cassandra connection failed: {e}")
            raise
    
    def close(self):
        self.cluster.shutdown()
    
    def _create_keyspace(self):
        """Create keyspace if it doesn't exist"""
        query = f"""
        CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
        """
        self.session.execute(query)
    
    def _create_tables(self):
        """Create required tables"""
        # Transaction history table
        transaction_table = """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id uuid PRIMARY KEY,
            user_id uuid,
            waste_id uuid,
            waste_type text,
            quantity double,
            price double,
            status text,
            created_at timestamp,
            updated_at timestamp
        )
        """
        self.session.execute(transaction_table)
        
        # Environmental impact metrics table
        impact_table = """
        CREATE TABLE IF NOT EXISTS environmental_impact (
            date date,
            metric_type text,
            waste_type text,
            value double,
            unit text,
            PRIMARY KEY ((date, metric_type), waste_type)
        )
        """
        self.session.execute(impact_table)
        
        # Audit logs table
        audit_table = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            timestamp timestamp,
            user_id uuid,
            action text,
            resource_type text,
            resource_id uuid,
            details text,
            PRIMARY KEY ((user_id, action), timestamp)
        ) WITH CLUSTERING ORDER BY (timestamp DESC)
        """
        self.session.execute(audit_table)
        
        # Time-series data table for analytics
        timeseries_table = """
        CREATE TABLE IF NOT EXISTS analytics_timeseries (
            metric_name text,
            timestamp timestamp,
            dimension1 text,
            dimension2 text,
            value double,
            PRIMARY KEY ((metric_name, dimension1), timestamp, dimension2)
        ) WITH CLUSTERING ORDER BY (timestamp DESC)
        """
        self.session.execute(timeseries_table)
    
    # Transaction Management
    def record_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Record a new transaction"""
        transaction_id = str(uuid.uuid4())
        transaction_data['transaction_id'] = transaction_id
        transaction_data['created_at'] = datetime.utcnow()
        transaction_data['updated_at'] = datetime.utcnow()
        
        query = """
        INSERT INTO transactions (
            transaction_id, user_id, waste_id, waste_type, 
            quantity, price, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        statement = self.session.prepare(query)
        self.session.execute(statement, [
            uuid.UUID(transaction_data['transaction_id']),
            uuid.UUID(transaction_data['user_id']),
            uuid.UUID(transaction_data['waste_id']),
            transaction_data['waste_type'],
            transaction_data['quantity'],
            transaction_data['price'],
            transaction_data['status'],
            transaction_data['created_at'],
            transaction_data['updated_at']
        ])
        
        logger.info(f"Recorded transaction: {transaction_id}")
        return transaction_id
    
    def get_transaction_history(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get transaction history for user"""
        query = """
        SELECT * FROM transactions 
        WHERE user_id = ? 
        LIMIT ? ALLOW FILTERING
        """
        try:
            statement = self.session.prepare(query)
            rows = self.session.execute(statement, [uuid.UUID(user_id), limit])
            return [dict(row) for row in rows]
        except Exception as e:
            logger.warning(f"Error getting transaction history: {e}")
            return []
    
    def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict]:
        """Get specific transaction"""
        query = "SELECT * FROM transactions WHERE transaction_id = ?"
        statement = self.session.prepare(query)
        row = self.session.execute(statement, [uuid.UUID(transaction_id)]).one()
        return dict(row) if row else None
    
    # Environmental Impact Tracking
    def record_environmental_impact(self, date: datetime, metric_type: str, 
                                  waste_type: str, value: float, unit: str) -> None:
        """Record environmental impact metric"""
        query = """
        INSERT INTO environmental_impact (date, metric_type, waste_type, value, unit)
        VALUES (?, ?, ?, ?, ?)
        """
        
        statement = self.session.prepare(query)
        self.session.execute(statement, [
            date.date(), metric_type, waste_type, value, unit
        ])
        logger.info(f"Recorded environmental impact: {metric_type} - {value} {unit}")
    
    def get_co2_savings_by_month(self, year: int, month: int) -> float:
        """Get CO2 savings for specific month"""
        try:
            query = """
            SELECT SUM(value) as total_co2_saved
            FROM environmental_impact
            WHERE metric_type = 'co2_savings'
              AND date >= ? AND date < ?
            ALLOW FILTERING
            """

            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            statement = self.session.prepare(query)
            result = self.session.execute(statement, [start_date.date(), end_date.date()]).one()
            return result.total_co2_saved if result and result.total_co2_saved else 0.0
        except Exception as e:
            logger.warning(f"Error getting CO2 savings: {e}")
            return 0.0
    
    def get_waste_diversion_trends(self, days: int = 30) -> List[Dict]:
        """Get waste diversion trends over time"""
        try:
            end_date = datetime.utcnow().date()
            start_date = datetime.utcnow().date() - timedelta(days=days)

            query = """
            SELECT date, waste_type, value
            FROM environmental_impact
            WHERE metric_type = 'waste_diverted'
              AND date >= ? AND date <= ?
            ALLOW FILTERING
            """

            statement = self.session.prepare(query)
            rows = self.session.execute(statement, [start_date, end_date])
            return [dict(row) for row in rows]
        except Exception as e:
            logger.warning(f"Error getting waste diversion trends: {e}")
            return []
    
    # Audit Logging
    def log_audit_event(self, user_id: str, action: str, resource_type: str, 
                       resource_id: str, details: str) -> None:
        """Log audit event"""
        query = """
        INSERT INTO audit_logs (timestamp, user_id, action, resource_type, resource_id, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        statement = self.session.prepare(query)
        self.session.execute(statement, [
            datetime.utcnow(),
            uuid.UUID(user_id),
            action,
            resource_type,
            uuid.UUID(resource_id),
            details
        ])
    
    def get_audit_logs(self, user_id: str = None, action: str = None, 
                      limit: int = 100) -> List[Dict]:
        """Get audit logs with optional filtering"""
        if user_id and action:
            query = """
            SELECT * FROM audit_logs 
            WHERE user_id = ? AND action = ? 
            LIMIT ?
            """
            statement = self.session.prepare(query)
            rows = self.session.execute(statement, [uuid.UUID(user_id), action, limit])
        elif user_id:
            query = "SELECT * FROM audit_logs WHERE user_id = ? LIMIT ?"
            statement = self.session.prepare(query)
            rows = self.session.execute(statement, [uuid.UUID(user_id), limit])
        else:
            query = "SELECT * FROM audit_logs LIMIT ?"
            statement = self.session.prepare(query)
            rows = self.session.execute(statement, [limit])
        
        return [dict(row) for row in rows]
    
    # Analytics Time Series
    def record_analytics_metric(self, metric_name: str, timestamp: datetime,
                               dimension1: str, dimension2: str, value: float) -> None:
        """Record analytics time-series data"""
        query = """
        INSERT INTO analytics_timeseries (metric_name, timestamp, dimension1, dimension2, value)
        VALUES (?, ?, ?, ?, ?)
        """
        
        statement = self.session.prepare(query)
        self.session.execute(statement, [metric_name, timestamp, dimension1, dimension2, value])
    
    def get_analytics_metrics(self, metric_name: str, dimension1: str = None,
                            start_time: datetime = None, end_time: datetime = None,
                            limit: int = 1000) -> List[Dict]:
        """Get analytics time-series data"""
        if dimension1 and start_time and end_time:
            query = """
            SELECT * FROM analytics_timeseries 
            WHERE metric_name = ? AND dimension1 = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT ?
            """
            statement = self.session.prepare(query)
            rows = self.session.execute(statement, [
                metric_name, dimension1, start_time, end_time, limit
            ])
        elif dimension1:
            query = """
            SELECT * FROM analytics_timeseries 
            WHERE metric_name = ? AND dimension1 = ? 
            ORDER BY timestamp DESC
            LIMIT ?
            """
            statement = self.session.prepare(query)
            rows = self.session.execute(statement, [metric_name, dimension1, limit])
        else:
            query = """
            SELECT * FROM analytics_timeseries 
            WHERE metric_name = ? 
            ORDER BY timestamp DESC
            LIMIT ?
            """
            statement = self.session.prepare(query)
            rows = self.session.execute(statement, [metric_name, limit])
        
        return [dict(row) for row in rows]