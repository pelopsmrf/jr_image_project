from io import BytesIO
from pathlib import Path
import uuid

from PIL import Image


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024


def is_allowed_file(filename: Path) -> bool:
    """Проверяем, есть ли расширение в разрешенной коллекции."""
    return filename.suffix.lower() in ALLOWED_EXTENSIONS


def is_real_image(contents: bytes) -> bool:
    """Проверяем через Pillow, что внутри файла действительно картинка."""
    try:
        Image.open(BytesIO(contents)).verify()
        return True
    except Exception:
        return False


def get_unique_name(filename: Path) -> str:
    return f"{uuid.uuid4().hex}{filename.suffix.lower()}"
