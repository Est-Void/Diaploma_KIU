"""
Server configuration for Genius Loci dispatch system.
"""
import os

SERVER_CONFIG = {
    "database_url": os.getenv("DATABASE_URL", "sqlite:///./genius_loci.db"),
    "host": os.getenv("SERVER_HOST", "0.0.0.0"),
    "port": int(os.getenv("SERVER_PORT", "8000")),
    "jwt_secret": os.getenv("JWT_SECRET", "change-this-secret-in-production"),
    "jwt_algorithm": "HS256",
    "jwt_expire_hours": 24,
    "cors_origins": ["http://localhost:5173"],
}
