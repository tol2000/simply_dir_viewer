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

app_dir: Path = Path(__file__).resolve().absolute().parent
app_work_dir: Path = (app_dir / Path('public_files')).resolve().absolute()

app = Flask('photo_v')


def make_url_for_subdir(dir_url, path_for_url):
    return f'{dir_url}?{SUBDIR_PARAM_NAME}={urllib.parse.quote(str(path_for_url), safe="")}'


def make_picture_url_for_subdir(picture_url: str, picture_subdir: Path, picture_name: Path):
    picture_path = str(Path(picture_subdir) / Path(picture_name))
    url = f'{picture_url}?{PICTURE_PATH_PARAM_NAME}={urllib.parse.quote(picture_path, safe="")}'
    url += f'&{SUBDIR_PARAM_NAME}={urllib.parse.quote(str(picture_subdir), safe="")}'
    return url


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
@app.route(f'/{PICTURE_ENDPOINT}/<int:zoom>/')
def show_picture(zoom=4):
    picture_path = request.args.get(f'{PICTURE_PATH_PARAM_NAME}', '', str)
    picture_dir_path = request.args.get(f'{SUBDIR_PARAM_NAME}', '', str)
    image_name = Path(picture_path).name
    return render_template(
        'picture.html',
        img_data=get_image_data_for_html(app_work_dir / Path(picture_path)),
        img_subdir_link=make_url_for_subdir(request.url_root + f'{DIR_ENDPOINT}/{zoom}/', picture_dir_path),
        zoom=zoom,
        image_name=image_name,
    )


@app.route(f'/{DIR_ENDPOINT}/')
@app.route(f'/{DIR_ENDPOINT}/<int:zoom>/')
def show_dir(zoom=4):
    """
    :param zoom: 1, 2... - this number takes a part in <hn> tag, where n is zoom_h_num
                       for example, if you set 2 then all items will be displayed with <h2></h2> tags
    :return:
    """
    subdir = request.args.get(f'{SUBDIR_PARAM_NAME}', '', str)
    dir_name = (app_work_dir / subdir).resolve().absolute()
    dir_url = request.url_root + f'{DIR_ENDPOINT}/{zoom}/'
    picture_url = request.url_root + f'{PICTURE_ENDPOINT}/{zoom}/'

    # for security reasons :)
    if not str(dir_name).startswith(str(app_work_dir)):
        dir_name = app_work_dir
        subdir = ''

    # Parent dir (..)
    if app_work_dir in dir_name.parents:
        subdir_to_up = str(dir_name.parent)[len(str(app_work_dir))+1:]
    else:
        subdir_to_up = ''
    up_dir_link = make_url_for_subdir(dir_url, subdir_to_up)

    dir_list = sorted(list(dir_name.iterdir()), key=lambda x: (not x.is_dir(), str(x)))
    dir_items = []
    for path_obj in dir_list:
        path_for_url = path_obj.relative_to(app_work_dir)
        path_for_display = path_obj.relative_to(dir_name)
        preview_data = None
        if path_obj.is_dir():
            url = make_url_for_subdir(dir_url, path_for_url)
        elif path_obj.suffix.lower() in ['.jpg', '.jpeg']:
            url = make_picture_url_for_subdir(picture_url, Path(subdir), Path(path_for_display))
            preview_data = get_image_data_for_html(path_obj, (PREVIEW_WIDTH, PREVIEW_WIDTH))
        else:
            url = None
        if url:
            dir_items.append((path_for_display, url, not path_obj.is_dir(), preview_data))

    return render_template(
        'dir.html',
        dir_path=subdir if subdir else "root",
        root_dir_link=make_url_for_subdir(dir_url, ''),
        up_dir_link=up_dir_link,
        dir_items=dir_items,
        zoom=zoom,
    )
