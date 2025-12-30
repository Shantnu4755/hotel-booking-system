"""
Script to create a demo user for testing the booking system.
Run this with: python manage.py shell < create_demo_user.py
Or use: python manage.py createsuperuser
"""

from django.contrib.auth import get_user_model

User = get_user_model()

# Create demo user if it doesn't exist
username = 'demo'
email = 'demo@example.com'
password = 'demo123'

if not User.objects.filter(username=username).exists():
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    print(f"Demo user created successfully!")
    print(f"Username: {username}")
    print(f"Password: {password}")
else:
    print(f"User '{username}' already exists.")


