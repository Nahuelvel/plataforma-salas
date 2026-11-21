"""Configuración por variables de entorno (ver .env.example)."""
import os


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./local.db")
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")  # el QR apunta a BASE_URL/r/{sala}
    admin_user: str = os.getenv("ADMIN_USER", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "cambiar-esto")
    soporte_user: str = os.getenv("SOPORTE_USER", "soporte")
    soporte_password: str = os.getenv("SOPORTE_PASSWORD", "cambiar-esto-tambien")
    solver_max_segundos: float = float(os.getenv("SOLVER_MAX_SEGUNDOS", "60"))
    solver_hilos: int = int(os.getenv("SOLVER_HILOS", "8"))
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    correo_soporte: str = os.getenv("CORREO_SOPORTE", "soporte@example.com")
    zona_horaria: str = os.getenv("ZONA_HORARIA", "America/Santiago")


settings = Settings()
