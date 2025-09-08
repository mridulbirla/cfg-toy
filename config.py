import os
import json
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = "app_config.json"

class Config:
    # Default configuration from environment variables
    _openai_api_key = os.getenv("OPENAI_API_KEY")
    _clickhouse_host = os.getenv("CLICKHOUSE_HOST", "localhost")
    _clickhouse_port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    _clickhouse_username = os.getenv("CLICKHOUSE_USERNAME", "default")
    _clickhouse_password = os.getenv("CLICKHOUSE_PASSWORD", "")
    _clickhouse_database = os.getenv("CLICKHOUSE_DATABASE", "default")
    
    # Application Configuration
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("PORT", "8000"))
    
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
                cls._openai_api_key = openai_config["api_key"]
        
        if "clickhouse" in config_dict:
            clickhouse_config = config_dict["clickhouse"]
            if "host" in clickhouse_config:
                cls._clickhouse_host = clickhouse_config["host"]
            if "port" in clickhouse_config:
                cls._clickhouse_port = int(clickhouse_config["port"])
            if "username" in clickhouse_config:
                cls._clickhouse_username = clickhouse_config["username"]
            if "password" in clickhouse_config:
                cls._clickhouse_password = clickhouse_config["password"]
            if "database" in clickhouse_config:
                cls._clickhouse_database = clickhouse_config["database"]
        
        # Save to file
        cls.save_config_to_file(config_dict)
    
    @classmethod
    def get_openai_api_key(cls):
        return cls._openai_api_key
    
    @classmethod
    def get_clickhouse_host(cls):
        return cls._clickhouse_host
    
    @classmethod
    def get_clickhouse_port(cls):
        return cls._clickhouse_port
    
    @classmethod
    def get_clickhouse_username(cls):
        return cls._clickhouse_username
    
    @classmethod
    def get_clickhouse_password(cls):
        return cls._clickhouse_password
    
    @classmethod
    def get_clickhouse_database(cls):
        return cls._clickhouse_database
    
    # Properties for backward compatibility
    @property
    def OPENAI_API_KEY(cls):
        return cls._openai_api_key
    
    @property
    def CLICKHOUSE_HOST(cls):
        return cls._clickhouse_host
    
    @property
    def CLICKHOUSE_PORT(cls):
        return cls._clickhouse_port
    
    @property
    def CLICKHOUSE_USERNAME(cls):
        return cls._clickhouse_username
    
    @property
    def CLICKHOUSE_PASSWORD(cls):
        return cls._clickhouse_password
    
    @property
    def CLICKHOUSE_DATABASE(cls):
        return cls._clickhouse_database
