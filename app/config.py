# config.py
import os
from typing import Optional


class Config:
    """Configuration class for Warung AI application"""
    
    # Database Configuration
    DB_NAME: str = os.getenv("DB_NAME", "warung.db")
    
    # LLM Configuration
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "llama3-groq-tool-use:latest")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Directory Configuration
    APP_DIR: str = "app"
    SRC_DIR: str = "src"
    STATIC_DIR: str = os.path.join(APP_DIR, "static")
    QRIS_DIR: str = os.path.join(SRC_DIR, "qris_images")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # MCP Configuration
    MCP_SERVER_SCRIPT: str = os.getenv("MCP_SERVER_SCRIPT", "mcp_server.py")
    
    # CORS Configuration
    CORS_ORIGINS: list = ["*"]  # Untuk production, ganti dengan domain spesifik
    
    # Memory Configuration
    MEMORY_DB: str = "warung_ai_memory.sqlite"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        directories = [cls.STATIC_DIR, cls.QRIS_DIR]
        
        for directory in directories:
            full_path = os.path.join(os.getcwd(), directory)
            if not os.path.exists(full_path):
                os.makedirs(full_path)
                print(f"Directory '{directory}' created.")
        
        # Create dummy QRIS file if not exists
        default_qris_path = os.path.join(cls.QRIS_DIR, "default.png")
        if not os.path.exists(default_qris_path):
            with open(default_qris_path, "w") as f:
                f.write("Ini adalah QRIS dummy")
            print("Default QRIS dummy file created.")
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration"""
        required_files = [cls.DB_NAME]
        missing_files = []
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"Missing required files: {missing_files}")
            print("Please run database setup first.")
            return False
        
        return True


# Global config instance
config = Config()


def get_config() -> Config:
    """Get configuration instance"""
    return config