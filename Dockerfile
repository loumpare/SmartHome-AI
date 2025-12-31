# Use a lightweight Python image
FROM python:3.11-slim

# Install system dependencies for Bleak (Bluetooth) and other tools
RUN apt-get update && apt-get install -y \
    bluez \
    libbluetooth-dev \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port used by FastAPI
EXPOSE 8000

# Start the application
CMD ["uvicorn", "Src.Main:app", "--host", "0.0.0.0", "--port", "8000"]