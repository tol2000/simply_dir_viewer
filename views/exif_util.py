from PIL import Image
from PIL.ExifTags import TAGS

EXIF_VALUE_MAX_LENGTH = 150
# key - parameter, value - optional description
EXIF_ADD_IFD_PARAMETERS = {
    # Exif
    0x8769: '',
    0x8825: 'GPS info',
}
EXIF_TAG_IDS_TO_IGNORE = (
    39594,
)
EXIF_TAG_NAMES_TO_IGNORE = (
    'GPSInfo',
    'ResolutionUnit',
    'ExifOffset',
)


def add_exif_tag_to_dict(dict_obj, exif_obj, description_prefix=''):
    for tag_id in exif_obj:
        if tag_id not in EXIF_TAG_IDS_TO_IGNORE:
            key = str(TAGS.get(tag_id, tag_id))
            if key not in EXIF_TAG_NAMES_TO_IGNORE:
                key = description_prefix + key
                value = exif_obj.get(tag_id)
                val_type = type(value)
                # str(value) is not so optimal, i know :)
                if len(str(value)) > EXIF_VALUE_MAX_LENGTH:
                    value = str(value)[:EXIF_VALUE_MAX_LENGTH] + '...'
                if val_type not in (bytes,):
                    dict_obj[key] = value


def extract_exif_tags(im: Image):
    exif = {}
    add_exif_tag_to_dict(exif, im.getexif())
    for param, desc in EXIF_ADD_IFD_PARAMETERS.items():
        try:
            add_exif_tag_to_dict(exif, im.getexif().get_ifd(param), f'{desc}: ' if desc else '')
        except Exception:
            pass
    return exif
