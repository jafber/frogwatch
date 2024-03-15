FROM python:3.9-slim
WORKDIR /back
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py .
# set pythonpath for camera python package
ENV PYTHONPATH=/usr/lib/python3/dist-packages
CMD ["python", "__init__.py"]
