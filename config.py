import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env (si présent)
load_dotenv()


def _db_uri(host):
    """Construit l'URI PostgreSQL à partir des variables d'environnement."""
    if os.environ.get('DATABASE_URL'):
        return os.environ['DATABASE_URL']
    return (
        f"postgresql://{os.environ.get('DB_USER', 'postgres')}:"
        f"{os.environ.get('DB_PASSWORD', 'admin')}@"
        f"{host}:"
        f"{os.environ.get('DB_PORT', '5432')}/"
        f"{os.environ.get('DB_NAME', 'devops_db')}"
    )


class Config:
    """Configuration locale (Windows / Linux sans Docker)."""
    SQLALCHEMY_DATABASE_URI = _db_uri(os.environ.get('DB_HOST', 'localhost'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')


class DockerConfig(Config):
    """Configuration Docker Compose — host = 'db' (nom du service)."""
    SQLALCHEMY_DATABASE_URI = _db_uri(os.environ.get('DB_HOST', 'db'))
