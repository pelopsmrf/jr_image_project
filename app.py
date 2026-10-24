from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pathlib import Path
import logging

from utils.file_utils import is_allowed_file, is_real_image, get_unique_name, MAX_UPLOAD_SIZE
from utils import db


IMAGES_DIR = Path("images")
LOGS_DIR = Path("logs")
IMAGES_URL = "http://localhost:8080/images/"
PER_PAGE = 10

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
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

db.init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Главная страница сервиса."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/images/")
def images():
    """Старый адрес каталога, перенаправляем на новый список."""
    return RedirectResponse("/images-list")


@app.get("/images-list", response_class=HTMLResponse)
def images_list(request: Request, page: int = 1):
    """Список изображений из БД, по 10 штук на странице."""
    page = max(page, 1)
    total = db.count_images()
    rows = db.get_images(PER_PAGE, (page - 1) * PER_PAGE)
    return templates.TemplateResponse(
        request=request,
        name="images_list.html",
        context={
            "images": rows,
            "images_url": IMAGES_URL,
            "page": page,
            "has_prev": page > 1,
            "has_next": page * PER_PAGE < total,
        },
    )


@app.post("/delete/{image_id}")
def delete(request: Request, image_id: int):
    """Удаляет запись из БД и файл с диска."""
    filename = db.delete_image(image_id)
    if filename is None:
        logging.info(f"Ошибка: изображение с id={image_id} не найдено.")
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"error": f"Изображение с id={image_id} не найдено"},
            status_code=404,
        )

    file_path = IMAGES_DIR / filename
    if file_path.exists():
        file_path.unlink()
        logging.info(f"Успех: изображение {filename} удалено.")
    else:
        logging.info(f"Ошибка: файл {filename} отсутствует на диске, удалена только запись в БД.")

    return RedirectResponse("/images-list", status_code=303)


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    """Страница с формой загрузки."""
    return templates.TemplateResponse(request=request, name="upload.html")


@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...)):
    """Загрузка изображения: проверяем, сохраняем файл и метаданные, возвращаем ссылку."""
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
    file_path = IMAGES_DIR / new_name
    file_path.write_bytes(contents)

    try:
        db.save_metadata(new_name, my_file.name, len(contents), my_file.suffix.lower().lstrip("."))
    except Exception as e:
        # Без записи в БД файл не нужен, удаляем его
        file_path.unlink()
        logging.info(f"Ошибка: не удалось сохранить метаданные {my_file.name} в БД ({e}).")
        return show_error(request, "Ошибка базы данных, файл не сохранён", status_code=500)

    logging.info(f"Успех: изображение {new_name} загружено.")
    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={"file_id": new_name, "url": IMAGES_URL + new_name},
    )


def show_error(request: Request, message: str, status_code: int = 400):
    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={"error": message},
        status_code=status_code,
    )


if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
