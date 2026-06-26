FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 用法: docker compose run --rm crawler -- -c 122 -m "同步说明"
ENTRYPOINT ["python3", "-u", "fetchCourseList.py"]
CMD []
