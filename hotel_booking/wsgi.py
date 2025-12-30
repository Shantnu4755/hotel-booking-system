"""
WSGI config for hotel_booking project.
"""

import os
import sys

# ✅ Absolute path where manage.py exists
PROJECT_PATH = '/home/Shantnu4755/hotel_booking_system'

if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

# ✅ Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'hotel_booking.settings'

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
