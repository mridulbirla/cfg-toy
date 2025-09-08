import os
import json
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = "app_config.json"

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # ClickHouse Configuration
    # Handle CLICKHOUSE_HOST with proper None/empty string handling
    _clickhouse_host_raw = os.getenv("CLICKHOUSE_HOST")
    CLICKHOUSE_HOST = _clickhouse_host_raw if _clickhouse_host_raw and _clickhouse_host_raw.lower() not in ['none', 'null', ''] else "localhost"
    CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    CLICKHOUSE_USERNAME = os.getenv("CLICKHOUSE_USERNAME", "default")
    CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
    CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "default")
    
    # Application Configuration
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("PORT", "8000"))
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration values are properly set"""
        errors = []
        
        # Check ClickHouse configuration
        if not cls.CLICKHOUSE_HOST or cls.CLICKHOUSE_HOST.lower() in ['none', 'null', '']:
            errors.append("CLICKHOUSE_HOST is not properly configured")
        
        if not cls.CLICKHOUSE_PORT or cls.CLICKHOUSE_PORT <= 0:
            errors.append("CLICKHOUSE_PORT is not properly configured")
        
        if not cls.CLICKHOUSE_USERNAME:
            errors.append("CLICKHOUSE_USERNAME is not properly configured")
        
        if not cls.CLICKHOUSE_DATABASE:
            errors.append("CLICKHOUSE_DATABASE is not properly configured")
        
        # Check OpenAI configuration
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not properly configured")
        
        return errors
    
    @classmethod
    def get_config_summary(cls):
        """Get a summary of the current configuration (without sensitive data)"""
        return {
            "clickhouse_host": cls.CLICKHOUSE_HOST,
            "clickhouse_port": cls.CLICKHOUSE_PORT,
            "clickhouse_username": cls.CLICKHOUSE_USERNAME,
            "clickhouse_database": cls.CLICKHOUSE_DATABASE,
            "clickhouse_password_set": bool(cls.CLICKHOUSE_PASSWORD),
            "openai_api_key_set": bool(cls.OPENAI_API_KEY),
            "debug": cls.DEBUG,
            "port": cls.PORT
        }
    
    @classmethod
    def load_config_from_file(cls):
        """Load configuration from file if it exists"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                    cls.update_config(config_data)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    @classmethod
    def save_config_to_file(cls, config_dict):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_dict, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    @classmethod
    def update_config(cls, config_dict):
        """Update configuration dynamically"""
        if "openai" in config_dict:
            openai_config = config_dict["openai"]
            if "api_key" in openai_config:
                cls.OPENAI_API_KEY = openai_config["api_key"]
        
        if "clickhouse" in config_dict:
            clickhouse_config = config_dict["clickhouse"]
            if "host" in clickhouse_config:
                host = clickhouse_config["host"]
                cls.CLICKHOUSE_HOST = host if host and host.lower() not in ['none', 'null', ''] else "localhost"
            if "port" in clickhouse_config:
                cls.CLICKHOUSE_PORT = int(clickhouse_config["port"])
            if "username" in clickhouse_config:
                cls.CLICKHOUSE_USERNAME = clickhouse_config["username"]
            if "password" in clickhouse_config:
                cls.CLICKHOUSE_PASSWORD = clickhouse_config["password"]
            if "database" in clickhouse_config:
                cls.CLICKHOUSE_DATABASE = clickhouse_config["database"]
        
        # Save to file
        cls.save_config_to_file(config_dict)
