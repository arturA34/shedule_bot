from bot.config import get_settings, setup_logging

setup_logging()

if __name__ == "__main__":
    settings = get_settings()
    print(f"Config loaded. DB_PATH={settings.DB_PATH}")
