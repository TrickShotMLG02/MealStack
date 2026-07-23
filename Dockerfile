FROM python:3.12.4-slim
LABEL authors="TrickShotMLG02"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libsqlite3-dev \
    pkg-config \
    default-libmysqlclient-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install Pillow dependencies
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libwebp-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin/:$PATH"

# Copy project
COPY . .

# Install Python dependencies via uv
RUN /root/.local/bin/uv python install
RUN /root/.local/bin/uv sync

# Compile localization files
# This will generate .po files if not present and compile .mo files
RUN uv run python manage.py makemessages -a || true  # -a: all languages, ignore if no changes
RUN uv run python manage.py compilemessages --ignore "*/site-packages/*"

EXPOSE 8000

# Default command is to run Django, but can override
ENTRYPOINT ["uv", "run", "python", "manage.py"]
CMD ["runserver", "0.0.0.0:8000"]