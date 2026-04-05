import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "dados" / "tradescan.db"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Garantir que o diretório de dados existe
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
