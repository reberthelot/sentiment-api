# Sentiment API

A small FastAPI service that analyzes course-evaluation text using the LabMT word sentiment list. It returns a sentiment score between `-5` and `5`, together with a sentiment label.

## Run with Docker Compose

From the project directory, run:

```bash
docker compose up --build
```

The API is then available at:

- Swagger documentation: http://localhost:8000/docs
- UI interface: http://localhost:8000/ui
- Sentiment endpoint: `POST http://localhost:8000/v1/sentiment`

Stop the service with `Ctrl+C`.

## Run with Uvicorn

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the application:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The same documentation and API endpoint are available on port `8000`.

## Example request

```bash
curl -X POST http://localhost:8000/v1/sentiment \
  -H "Content-Type: application/json" \
  -d '{"text":"It was a great course."}'
```
