import logging
import subprocess
from datetime import datetime
from pathlib import Path


BACKUPS_DIR = Path("backups")
LOGS_DIR = Path("logs")

BACKUPS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOGS_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


def make_backup():
    backup_file = BACKUPS_DIR / f"backup_{datetime.now():%Y-%m-%d_%H%M%S}.sql"
    command = ["docker", "exec", "image_server_db", "pg_dump", "-U", "postgres", "images_db"]

    with open(backup_file, "w", encoding="utf-8") as f:
        result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        logging.info(f"Успех: резервная копия {backup_file.name} создана.")
    else:
        backup_file.unlink()
        logging.info(f"Ошибка: резервная копия не создана ({result.stderr.strip()}).")


if __name__ == '__main__':
    make_backup()
