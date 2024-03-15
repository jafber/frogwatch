FROM python:3.9-slim
WORKDIR /back
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY __init__.py .
CMD ["python", "__init__.py"]
