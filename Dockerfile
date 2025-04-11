# Use official lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential

# Install Python dependencies
COPY requirements.txt ./
EXPOSE 8080
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .

# Run the bot
CMD ["python", "optbot.py"]
