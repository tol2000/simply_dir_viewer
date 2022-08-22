# pull official base image
FROM python:3.10.4-alpine

# set work directory
WORKDIR /simply_dir_viewer

# set build-time environment variables
ENV SIMPLY_DIR_VIEWER_PUBLIC_FILES /public_files

# install dependencies
RUN pip install --upgrade pip
RUN pip install pipenv
COPY Pipfile ./
COPY Pipfile.lock ./
RUN pipenv install

COPY . ./
