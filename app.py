from functools import lru_cache
import urllib.parse
from flask import Flask, request, render_template
from PIL import Image
import base64
import io
from pathlib import Path

SUBDIR_PARAM_NAME = 'subdir'
PICTURE_PATH_PARAM_NAME = 'picture'
DIR_ENDPOINT = 'dir'
PICTURE_ENDPOINT = 'picture'
PREVIEW_WIDTH = 200
DEFAULT_COLUMNS = 6
DIRECTORY_LIST_ONE_COLUMN = False

app_dir: Path = Path(__file__).resolve().absolute().parent

# This constant must to point to dir with your photos to display
PUBLIC_FILES: Path = (app_dir / Path('public_files')).resolve().absolute()

app = Flask('photo_v')


def make_url_for_subdir(dir_url, path_for_url):
    return f'{dir_url}?{SUBDIR_PARAM_NAME}={urllib.parse.quote(str(path_for_url), safe="")}'


def make_picture_url_for_subdir(picture_url: str, picture_subdir: Path, picture_name: Path):
    picture_path = str(Path(picture_subdir) / Path(picture_name))
    url = f'{picture_url}?{PICTURE_PATH_PARAM_NAME}={urllib.parse.quote(picture_path, safe="")}'
    url += f'&{SUBDIR_PARAM_NAME}={urllib.parse.quote(str(picture_subdir), safe="")}'
    return url


def where_append_by_cols(list_items: list, added_cols: int, max_cols: int):
    """

    :param list_items:
    :param added_cols:
    :param max_cols:
    :return: (
                 new added or last element of list_items counted by added_cols,
                 new calculated added_cols
             )
    """
    if added_cols == 0:
        loc_list2append = []
        list_items.append(loc_list2append)
    else:
        loc_list2append = list_items[-1]
    added_cols = added_cols + 1 if added_cols < max_cols - 1 else 0
    return loc_list2append, added_cols


@lru_cache(maxsize=256)
def get_image_data_for_html(image_path: Path, preview_width=None):
    im: Image = Image.open(image_path)
    if preview_width:
        im.thumbnail(preview_width, Image.ANTIALIAS)
    data = io.BytesIO()
    im.save(data, "JPEG")
    encoded_img_data = base64.b64encode(data.getvalue())
    return encoded_img_data.decode('utf-8')


@app.route(f'/{PICTURE_ENDPOINT}/')
@app.route(f'/{PICTURE_ENDPOINT}/<int:cols>/')
def show_picture(cols=DEFAULT_COLUMNS):
    picture_path = request.args.get(f'{PICTURE_PATH_PARAM_NAME}', '', str)
    picture_dir_path = request.args.get(f'{SUBDIR_PARAM_NAME}', '', str)
    image_name = Path(picture_path).name
    return render_template(
        'picture.html',
        img_data=get_image_data_for_html(PUBLIC_FILES / Path(picture_path)),
        img_subdir_link=make_url_for_subdir(request.url_root + f'{DIR_ENDPOINT}/{cols}/', picture_dir_path),
        image_name=image_name,
    )


@app.route(f'/{DIR_ENDPOINT}/')
@app.route(f'/{DIR_ENDPOINT}/<int:cols>/')
def show_dir(cols=DEFAULT_COLUMNS):
    """
    :param cols: 1, 2... - number of columns in images grid (default: DEFAULT_COLUMNS)
    :return:
    """
    subdir = request.args.get(f'{SUBDIR_PARAM_NAME}', '', str)
    dir_name = (PUBLIC_FILES / subdir).resolve().absolute()
    dir_url = request.url_root + f'{DIR_ENDPOINT}/{cols}/'
    picture_url = request.url_root + f'{PICTURE_ENDPOINT}/'

    # for security reasons :)
    if not str(dir_name).startswith(str(PUBLIC_FILES)):
        dir_name = PUBLIC_FILES
        subdir = ''

    # Parent dir (..)
    if PUBLIC_FILES in dir_name.parents:
        subdir_to_up = str(dir_name.parent)[len(str(PUBLIC_FILES)) + 1:]
    else:
        subdir_to_up = ''
    up_dir_link = make_url_for_subdir(dir_url, subdir_to_up)

    # resolve() - to resolve symlinks
    dir_list = sorted(list(dir_name.resolve().iterdir()), key=lambda x: (not x.is_dir(), str(x)))

    dirs_items = []
    files_items = []
    added_dirs_cols = 0
    added_files_cols = 0
    for path_obj in dir_list:
        path_for_url = path_obj.relative_to(PUBLIC_FILES)
        path_for_display = path_obj.relative_to(dir_name)

        if path_obj.is_dir():
            url = make_url_for_subdir(dir_url, path_for_url)
            list2append, added_dirs_cols = where_append_by_cols(dirs_items, added_dirs_cols, 1 if DIRECTORY_LIST_ONE_COLUMN else cols)
            list2append.append((path_for_display, url))
        elif path_obj.suffix.lower() in ['.jpg', '.jpeg']:
            url = make_picture_url_for_subdir(picture_url, Path(subdir), Path(path_for_display))
            preview_data = get_image_data_for_html(path_obj, (PREVIEW_WIDTH, PREVIEW_WIDTH))
            list2append, added_files_cols = where_append_by_cols(files_items, added_files_cols, cols)
            list2append.append((path_for_display, url, preview_data))

    return render_template(
        'dir.html',
        dir_path=subdir if subdir else "root",
        root_dir_link=make_url_for_subdir(dir_url, ''),
        up_dir_link=up_dir_link,
        dirs_items=dirs_items,
        files_items=files_items,
    )
