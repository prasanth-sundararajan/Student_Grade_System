FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the frontend application code
COPY . .

EXPOSE 8501

# Run Streamlit in headless mode so it binds correctly inside the container network
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]