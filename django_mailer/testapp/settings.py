
EMAIL_PORT = 1025
ROOT_URLCONF = 'django_mailer.apptest.urls'

SECRET_KEY = 'yo secret yo'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'django_mailer.sqlite',
    },
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django_mailer',
    'django_mailer.testapp'
)
