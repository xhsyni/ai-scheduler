# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /backend

# # CA certs for TLS (MongoDB Atlas, HTTPS); certifi is used explicitly too
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends ca-certificates openssl \
#     && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates

# Copy the requirements file and install dependencies
COPY ./requirements.txt /backend/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /backend/requirements.txt

# Copy the application code
COPY ./ /backend

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
