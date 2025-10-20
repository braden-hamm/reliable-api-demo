# ============================================
#  Building Reliable APIs That Teach Themselves (v5)
#  © 2025 Braden Hamm — Educational License
# ============================================
FROM mcr.microsoft.com/devcontainers/python:3.11
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py /app/app.py
# Create non-root user for runtime
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
