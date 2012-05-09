import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mugged.settings")
from muggedapp.api import mugapi

if __name__ == '__main__':
	mugapi.update_daily_mugshots()
