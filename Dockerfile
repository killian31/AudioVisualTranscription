# Use a base Python image
FROM python:3.11

# Install system-level dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    export PATH="$HOME/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy all project files into the container
COPY . /app

# Install Python dependencies using Poetry
RUN poetry config virtualenvs.create false && poetry install --no-root

# Command to run the Gradio app
CMD ["python", "app.py"]

