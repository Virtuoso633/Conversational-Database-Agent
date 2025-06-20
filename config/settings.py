import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MongoDB Setting
    MONGODB_URI = os.getenv('MONGODB_URI')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'sample_analytics')
    ANALYTICS_DB = os.getenv('ANALYTICS_DB', DATABASE_NAME)
    # Groq Settings
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    MODEL_NAME = "llama-3.1-8b-instant"  # Fast and efficient for development
    FALLBACK_MODEL = "llama-3.3-70b-versatile"  # More capable for complex queries

    # Application Settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Collections to work with
    COLLECTIONS = ['customers', 'events', 'transactions', 'dashboard_metrics']

    # Groq-specific settings
    GROQ_TEMPERATURE = 0.1  # Low temperature for consistent responses
    GROQ_MAX_TOKENS = 1000  # Reasonable limit for responses
    GROQ_BASE_URL = "https://api.groq.com/openai/v1"  # OpenAI compatibility

    # Database Manager Settings
    DB_CONNECTION_TIMEOUT = 10000  # 10 seconds
    DB_QUERY_LIMIT = 100  # Default query limit
    SCHEMA_SAMPLE_SIZE = 100  # Documents to sample for schema extraction

config = Config()