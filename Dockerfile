
FROM python:3.13-slim
WORKDIR /app
# Copy project
COPY . .

RUN apt-get update && apt-get install -y --no-install-recommends binutils build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir uv
RUN uv sync --group dist

CMD ["bash"]
