import clickhouse_connect
from config import Config
import logging
import time

logger = logging.getLogger(__name__)

class ClickHouseClient:
    def __init__(self):
        self.client = None
        self.connect()
    
    def connect(self):
        """Establish connection to ClickHouse"""
        try:
            self.client = clickhouse_connect.get_client(
                host=Config.CLICKHOUSE_HOST,
                port=Config.CLICKHOUSE_PORT,
                username=Config.CLICKHOUSE_USERNAME,
                password=Config.CLICKHOUSE_PASSWORD,
                database=Config.CLICKHOUSE_DATABASE
            )
            logger.info("✅ Connected to ClickHouse")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ClickHouse: {e}")
            raise
    
    def execute_query(self, query: str):
        """Execute a ClickHouse query and return results"""
        try:
            start_time = time.time()
            result = self.client.query(query)
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return {
                "rows": result.result_rows,
                "columns": result.column_names,
                "execution_time": execution_time
            }
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def test_connection(self):
        """Test the database connection"""
        try:
            result = self.client.query("SELECT 1 as test")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
