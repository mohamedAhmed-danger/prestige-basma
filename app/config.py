import os
from dotenv import load_dotenv
load_dotenv()


BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'geoattend.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Batch 12 — WebAuthn (Relying Party) config. Defaults match local dev
    # (localhost, plain http). Override via env vars for staging/prod — RP_ID
    # must be the bare domain (no scheme/port), ORIGIN must be the exact
    # scheme+host+port the browser sees, or every ceremony will fail.
    WEBAUTHN_RP_ID = os.getenv("WEBAUTHN_RP_ID", "localhost")
    WEBAUTHN_RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "برستيج بصمة")
    WEBAUTHN_ORIGIN = os.getenv("WEBAUTHN_ORIGIN", "http://localhost:5000")