#!/usr/bin/env python3
"""
Setup script for CFG + Eval Toy
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("🚀 Setting up CFG + Eval Toy...")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        env_content = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# ClickHouse Configuration
CLICKHOUSE_HOST=your_clickhouse_host_here
CLICKHOUSE_PORT=8123
CLICKHOUSE_USERNAME=default
CLICKHOUSE_PASSWORD=your_clickhouse_password_here
CLICKHOUSE_DATABASE=default

# Application Configuration
DEBUG=False
PORT=8000
"""
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ Created .env file - please configure your API keys and database credentials")
    else:
        print("✅ .env file already exists")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your OpenAI API key and ClickHouse credentials")
    print("2. Run: python -m database.setup_database")
    print("3. Run: python main.py")
    print("4. Run: python gradio_app.py")
    print("\nThe application will be available at:")
    print("- FastAPI: http://localhost:8000")
    print("- Gradio UI: http://localhost:7860")

if __name__ == "__main__":
    main()
