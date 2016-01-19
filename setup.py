from setuptools import setup, find_packages


setup(
    name='clubadm',
    version='4.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Django==1.9.1',
        'Celery==3.1.19',
        'djangorestframework==3.3.2',
        'django-pipeline==1.5.4',
        'django-debug-toolbar==1.4',
        'pylibmc',
        'psycopg2',
        'jinja2',
    ]
)
