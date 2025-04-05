FROM python:3.9-slim
WORKDIR /back
COPY * .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 3000
CMD ["python", "__init__.py"]
