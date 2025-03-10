#!/bin/bash
#!/bin/bash
# build.sh

# Install dependencies
echo "Installing dependencies..."
# pip install --upgrade pip
# pip install -r requirements.txt
python3.9 -m pip install --upgrade pip
python3.9 -m pip install -r requirements.txt
# Apply migrations
echo "Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear
