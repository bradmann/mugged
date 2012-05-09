import os

if __name__ == '__main__':
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mugged.settings")
	from muggedapp.api import mugapi
	mugapi.update_daily_mugshots()