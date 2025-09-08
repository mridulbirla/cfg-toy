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
                host=Config.get_clickhouse_host(),
                port=Config.get_clickhouse_port(),
                username=Config.get_clickhouse_username(),
                password=Config.get_clickhouse_password(),
                database=Config.get_clickhouse_database()
            )
            logger.info("✅ Connected to ClickHouse")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ClickHouse: {e}")
            raise
    
    def reconnect(self):
        """Reconnect with updated configuration"""
        try:
            self.client = clickhouse_connect.get_client(
                host=Config.get_clickhouse_host(),
                port=Config.get_clickhouse_port(),
                username=Config.get_clickhouse_username(),
                password=Config.get_clickhouse_password(),
                database=Config.get_clickhouse_database()
            )
            logger.info("✅ Reconnected to ClickHouse with new configuration")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to reconnect to ClickHouse: {e}")
            return False
    
    def test_connection_with_config(self, config_dict):
        """Test connection with specific configuration"""
        try:
            test_client = clickhouse_connect.get_client(
                host=config_dict["clickhouse"]["host"],
                port=int(config_dict["clickhouse"]["port"]),
                username=config_dict["clickhouse"]["username"],
                password=config_dict["clickhouse"]["password"],
                database=config_dict["clickhouse"]["database"]
            )
            result = test_client.query("SELECT 1 as test")
            test_client.close()
            return True, None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, str(e)
    
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
