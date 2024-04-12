FROM python:3.11-slim

# Set the working directory
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

COPY wwwroot /app/wwwroot
RUN mkdir -p /app/wwwroot/assets/data

EXPOSE 80
ENV OPENAPI_URL=
ENV CORS_ORIGIN=https://aievolution.azurewebsites.net

CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "3", "--log-level", "info"]