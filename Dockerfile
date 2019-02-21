# The first instruction is what image we want to base our container on
# We Use an official Python runtime as a parent image
FROM python:2.7

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY . /usr/src/app

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r requirements-docker.txt

ENTRYPOINT ["/usr/src/app/waves/bin/entry.sh"]