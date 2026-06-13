from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[2]


def load_env_file() -> None:
    """
    加载项目根目录下的 .env 文件。

    已存在的系统环境变量优先级更高，不会被 .env 覆盖。
    """
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#") or "=" not in clean_line:
            continue

        key, value = clean_line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()

APP_NAME = "IELTS Speaking Coach"
APP_VERSION = "0.5.0"

# 默认使用项目根目录下的 ielts.db，方便本地启动。
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "ielts.db"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# OpenAI-compatible LLM 配置。默认先走 DeepSeek，适合本项目低成本试跑。
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL", "")

if LLM_PROVIDER == "deepseek":
    LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY") or LLM_API_KEY
    LLM_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", LLM_BASE_URL or "https://api.deepseek.com")
    LLM_MODEL = os.getenv("DEEPSEEK_MODEL", LLM_MODEL or "deepseek-v4-flash")
else:
    LLM_BASE_URL = LLM_BASE_URL or "https://api.openai.com/v1"
    LLM_MODEL = LLM_MODEL or "gpt-4o-mini"
