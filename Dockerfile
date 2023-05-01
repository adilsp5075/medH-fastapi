# Use the official Python image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . /app

# Expose port for the service
ARG PORT=8080
EXPOSE $PORT

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
