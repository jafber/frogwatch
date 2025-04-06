# docker build -t jafber/frogwatch-back .
# docker run --rm -p 3000:3000 jafber/frogwatch-back

FROM python:3.9-slim
WORKDIR /back
COPY * .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 3000
CMD ["python", "__init__.py"]
