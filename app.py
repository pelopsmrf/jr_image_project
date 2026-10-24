from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from pathlib import Path
import logging

from utils.file_utils import is_allowed_file, is_real_image, get_unique_name, MAX_UPLOAD_SIZE


IMAGES_DIR = Path("images")
LOGS_DIR = Path("logs")
IMAGES_URL = "http://localhost:8080/images/"

IMAGES_DIR.mkdir(exist_ok=True)
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

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Главная страница сервиса."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/images/", response_class=HTMLResponse)
def images(request: Request):
    """Список загруженных изображений."""
    files = sorted(f.name for f in IMAGES_DIR.iterdir() if is_allowed_file(f))
    return templates.TemplateResponse(
        request=request,
        name="images.html",
        context={"files": files, "images_url": IMAGES_URL},
    )


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    """Страница с формой загрузки."""
    return templates.TemplateResponse(request=request, name="upload.html")


@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...)):
    """Загрузка изображения: проверяем, сохраняем и возвращаем ссылку."""
    my_file = Path(file.filename)

    if not is_allowed_file(my_file):
        logging.info(f"Ошибка: неподдерживаемый формат файла ({my_file.name}).")
        return show_error(request, "Неподдерживаемый формат файла. Разрешены: .jpg, .png, .gif")

    contents = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(contents) > MAX_UPLOAD_SIZE:
        logging.info(f"Ошибка: файл слишком большой ({my_file.name}).")
        return show_error(request, "Файл слишком большой. Максимум 5 МБ")

    if not is_real_image(contents):
        logging.info(f"Ошибка: файл не является изображением ({my_file.name}).")
        return show_error(request, "Файл не является изображением")

    new_name = get_unique_name(my_file)
    (IMAGES_DIR / new_name).write_bytes(contents)
    logging.info(f"Успех: изображение {new_name} загружено.")

    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={"file_id": new_name, "url": IMAGES_URL + new_name},
    )


def show_error(request: Request, message: str):
    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={"error": message},
        status_code=400,
    )


if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
