FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app KERNELLAB_DB=/data/kernellab.db
WORKDIR /app
COPY requirements.txt pyproject.toml README.md ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 kernellab
COPY --chown=kernellab:kernellab . .
RUN pip install --no-cache-dir . && mkdir /data && chown -R kernellab:kernellab /app /data
USER kernellab
EXPOSE 8000
CMD ["uvicorn", "kernellab.api:app", "--host", "0.0.0.0", "--port", "8000"]
