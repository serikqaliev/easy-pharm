# Use the official Python image as the base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    libssl-dev \
    gcc  \
    libglib2.0-0  \
    libsm6 libxrender1 \
    libgl1-mesa-glx \
    libxext6

# Copy the dependencies file to the working directory
COPY requirements.txt .
COPY entrypoint.sh .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install daphne
RUN pip install daphne
RUN pip install opencv-python-headless

# Create the django user
RUN adduser --disabled-password --no-create-home --gecos "" django

# Create the media directory in the /app directory
RUN mkdir -p media

# Give ownership of the media directory to the django user
RUN chown -R django:django media
RUN chmod +x entrypoint.sh

# Change to the django user
USER django
