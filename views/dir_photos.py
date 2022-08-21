import sys
from functools import lru_cache
from flask import request, render_template, Blueprint, url_for
from PIL import Image
from pillow_heif import register_heif_opener
register_heif_opener()
import base64
import io
import os
from pathlib import Path
from . import exif_util

app_dir_photos = Blueprint('dir_photos_app', __name__, url_prefix='/dirpic')

SUBDIR_PARAM_NAME = 'subdir'
PICTURE_PATH_PARAM_NAME = 'picture'
ZOOM_PARAM_NAME = 'zoom'
PICTURE_ENDPOINT = 'picture'
PREVIEW_WIDTH = 200
DEFAULT_COLUMNS = 6
IMAGES_LRU_CACHE_MAX_SIZE = 256

# Dir with photos to display
PATH_ENV = os.getenv('SIMPLY_DIR_VIEWER_PUBLIC_FILES')
PUBLIC_FILES = Path(PATH_ENV) if PATH_ENV \
    else (Path(sys.argv[0]).resolve().absolute().parent / Path('public_files')).resolve().absolute()

# suffixes to display
SUFFIXES_TO_DISPLAY = [
    x.strip().lower() for x in
    os.getenv(
        'SIMPLY_DIR_VIEWER_SUFFIXES_TO_DISPLAY',
        default='.jpg, .jpeg, .png, .heif, .heic'
    ).split(',')
]


def make_url_for_subdir(path_for_url):
    query_args = {
        SUBDIR_PARAM_NAME: str(path_for_url)
    }
    return url_for(app_dir_photos.name+".show_dir", **query_args)


def make_picture_url_for_subdir(picture_subdir: Path, picture_name: Path):
    picture_path = str(Path(picture_subdir) / Path(picture_name))
    query_args = {
        PICTURE_PATH_PARAM_NAME: picture_path,
        SUBDIR_PARAM_NAME: str(picture_subdir),
    }
    return url_for(app_dir_photos.name+".show_picture", **query_args)


@lru_cache(maxsize=IMAGES_LRU_CACHE_MAX_SIZE)
def get_image_data_for_html(image_path: Path, preview_width=None):
    exif = {}
    try:
        im: Image = Image.open(image_path)
        exif["Megapixels (size)"] = f"{(im.size[0]*im.size[1])/pow(10, 6):.1f} ({im.size[0]}x{im.size[1]})"
        exif_loc = exif_util.extract_exif_tags(im)
        exif.update(exif_loc)

        if preview_width:
            im.thumbnail(preview_width, Image.ANTIALIAS)

        data = io.BytesIO()
        im.save(data, "JPEG")
        encoded_img_data = base64.b64encode(data.getvalue()).decode('utf-8')
    except Exception:
        encoded_img_data = None
    return encoded_img_data, exif


@app_dir_photos.route(f'/picture/')
def show_picture():
    picture_path = request.args.get(f'{PICTURE_PATH_PARAM_NAME}', '', str)
    picture_dir_path = request.args.get(f'{SUBDIR_PARAM_NAME}', '', str)
    zoom = request.args.get(f'{ZOOM_PARAM_NAME}', '', str)
    image_name = Path(picture_path).name
    img_data, exif = get_image_data_for_html(PUBLIC_FILES / Path(picture_path))
    return render_template(
        app_dir_photos.url_prefix + '/picture.html',
        img_data=img_data,
        img_subdir_link=make_url_for_subdir(picture_dir_path),
        image_name=image_name,
        image_class='img_fullsize' if zoom == 'full' else 'img_fit2',
        exif=exif,
    )


@app_dir_photos.route('/')
def show_dir():
    subdir = request.args.get(f'{SUBDIR_PARAM_NAME}', '', str)
    dir_name = (PUBLIC_FILES / subdir).resolve().absolute()

    # for security reasons :)
    if not str(dir_name).startswith(str(PUBLIC_FILES)):
        dir_name = PUBLIC_FILES
        subdir = ''

    # Parent dir (..)
    if PUBLIC_FILES in dir_name.parents:
        subdir_to_up = str(dir_name.parent)[len(str(PUBLIC_FILES)) + 1:]
    else:
        subdir_to_up = ''
    up_dir_link = make_url_for_subdir(subdir_to_up)

    # resolve() - to resolve symlinks
    dir_list = sorted(list(dir_name.resolve().iterdir()), key=lambda x: (not x.is_dir(), str(x)))

    dirs_items = []
    files_items = []

    for path_obj in dir_list:
        path_for_url = path_obj.relative_to(PUBLIC_FILES)
        path_for_display = path_obj.relative_to(dir_name)

        if path_obj.is_dir():
            url = make_url_for_subdir(path_for_url)
            dirs_items.append((path_for_display, url))
        elif path_obj.suffix.lower() in SUFFIXES_TO_DISPLAY:
            url = make_picture_url_for_subdir(Path(subdir), Path(path_for_display))
            preview_data, exif = get_image_data_for_html(path_obj, (PREVIEW_WIDTH, PREVIEW_WIDTH))
            files_items.append((path_for_display, url, preview_data))

    return render_template(
        app_dir_photos.url_prefix + '/dir.html',
        dir_path=subdir if subdir else "root",
        root_dir_link=make_url_for_subdir(''),
        up_dir_link=up_dir_link,
        dirs_items=dirs_items,
        files_items=files_items,
    )
