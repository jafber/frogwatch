# docker build -t jafber/frogwatch-back .
# docker run --env-file=../secret.env --rm -p 3000:3000 jafber/frogwatch-back

FROM python:3.9-slim
WORKDIR /back
# for health check
RUN apt-get update && apt-get install -y curl
COPY * .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 3000
CMD ["python", "__init__.py"]
