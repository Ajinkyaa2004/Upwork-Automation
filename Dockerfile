FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

# Same uid as the "ubuntu" user on the VPS, so ./data stays writable.
RUN useradd --uid 1000 --create-home agent && mkdir -p /app/data && chown -R agent /app
USER agent

CMD ["python", "-m", "src.main"]
