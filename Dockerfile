# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-alpine

EXPOSE 8000

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 