#!/bin/bash

# Production Setup Script for TaskManager AI
# This script helps set up the application for production deployment

set -e

echo "=== TaskManager AI Production Setup ==="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "[1/6] Creating .env file from template..."
    cp .env.example .env
    echo "Created .env file. Please edit it with your production values."
else
    echo "[1/6] .env file already exists."
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[2/6] Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "[2/6] Virtual environment already exists."
fi

# Activate virtual environment
echo "[3/6] Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "[4/6] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Apply migrations
echo "[5/6] Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "[6/6] Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file and set DJANGO_DEBUG=False"
echo "2. Generate a strong DJANGO_SECRET_KEY"
echo "3. Set DJANGO_ALLOWED_HOSTS to your domain"
echo "4. Configure email settings if needed"
echo "5. Run: python manage.py check --deploy"
echo "6. Start with: gunicorn taskmanager.wsgi:application --bind 0.0.0.0:8000"
echo ""
echo "For systemd service setup, see README.md"
