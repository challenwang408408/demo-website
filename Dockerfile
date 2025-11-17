FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port (PORT will be set at runtime by Koyeb)
EXPOSE 8000

# Start application using PORT environment variable
# Use shell form (sh -c) to ensure environment variable expansion works correctly
CMD sh -c "python app.py"

