FROM --platform=linux/amd64 python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONPATH=/app

# Install curl
RUN apt-get update && apt-get install --no-install-recommends -y \
    # Needed for Poetry installation
    curl

# Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | POETRY_HOME=/opt/poetry python  \
    && cd /usr/local/bin  \
    && ln -s /opt/poetry/bin/poetry  \
    && poetry config virtualenvs.create false

# Set workdir
WORKDIR /app

# Install dependencies
COPY poetry.lock pyproject.toml ./
RUN pip install --upgrade pip --user
RUN poetry install --no-dev --no-root

# Copy files
COPY . ./
# Set workdir
WORKDIR /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]