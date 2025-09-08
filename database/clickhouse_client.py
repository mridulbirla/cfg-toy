import clickhouse_connect
from config import Config
import logging
import time

logger = logging.getLogger(__name__)

class ClickHouseClient:
    def __init__(self, auto_connect=True):
        self.client = None
        if auto_connect:
            self.connect()
    
    def connect(self):
        """Establish connection to ClickHouse"""
        try:
            # Validate configuration before attempting connection
            config_errors = Config.validate_config()
            if config_errors:
                error_msg = f"Configuration errors: {', '.join(config_errors)}"
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            logger.info(f"🔗 Attempting to connect to ClickHouse at {Config.CLICKHOUSE_HOST}:{Config.CLICKHOUSE_PORT}")
            
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
    
    def reconnect(self):
        """Reconnect with updated configuration"""
        try:
            # Close existing connection if any
            if self.client is not None:
                try:
                    self.client.close()
                except:
                    pass
            
            # Create new connection
            self.client = clickhouse_connect.get_client(
                host=Config.CLICKHOUSE_HOST,
                port=Config.CLICKHOUSE_PORT,
                username=Config.CLICKHOUSE_USERNAME,
                password=Config.CLICKHOUSE_PASSWORD,
                database=Config.CLICKHOUSE_DATABASE
            )
            logger.info("✅ Reconnected to ClickHouse with new configuration")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to reconnect to ClickHouse: {e}")
            return False
    
    def test_connection_with_config(self, config_dict):
        """Test connection with specific configuration"""
        try:
            # Validate the test configuration
            clickhouse_config = config_dict.get("clickhouse", {})
            host = clickhouse_config.get("host")
            port = clickhouse_config.get("port")
            username = clickhouse_config.get("username")
            password = clickhouse_config.get("password")
            database = clickhouse_config.get("database")
            
            # Check for None or empty values
            if not host or host.lower() in ['none', 'null', '']:
                return False, "Invalid host: host cannot be None, null, or empty"
            
            if not port:
                return False, "Invalid port: port cannot be None or empty"
            
            try:
                port_int = int(port)
                if port_int <= 0:
                    return False, f"Invalid port: {port_int} must be a positive integer"
            except (ValueError, TypeError):
                return False, f"Invalid port: '{port}' is not a valid integer"
            
            logger.info(f"🔗 Testing ClickHouse connection to {host}:{port}")
            
            test_client = clickhouse_connect.get_client(
                host=host,
                port=port_int,
                username=username,
                password=password,
                database=database
            )
            result = test_client.query("SELECT 1 as test")
            test_client.close()
            logger.info("✅ ClickHouse connection test successful")
            return True, None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ ClickHouse connection test failed: {error_msg}")
            return False, error_msg
    
    def execute_query(self, query: str):
        """Execute a ClickHouse query and return results"""
        try:
            # Connect if not already connected
            if self.client is None:
                self.connect()
            
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
            # Connect if not already connected
            if self.client is None:
                self.connect()
            
            result = self.client.query("SELECT 1 as test")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
