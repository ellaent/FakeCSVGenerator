from decouple import config

SECRET_KEY_PROD = config("SECRET_KEY_PROD")

DB_NAME = config("DB_NAME")
DB_HOST = config("DB_HOST")
DB_USERNAME = config("DB_USERNAME")
DB_PASSWORD = config("DB_PASSWORD")
