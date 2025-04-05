# docker build -t jafber/frogwatch-simpleserver .
# docker run -p 8765:8765 jafber/frogwatch-simpleserver

FROM python:3.9-slim
WORKDIR /simpleserver
COPY server.py requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8765
CMD ["python", "server.py"]
