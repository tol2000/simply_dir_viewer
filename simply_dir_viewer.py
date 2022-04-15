from app import app
from loguru import logger


def main():
    logger.info(f'Starting app "{app.import_name}"...')
    app.run(host='0.0.0.0', port=8080, debug=True)
    logger.info(f'Exiting')


if __name__ == '__main__':
    main()
