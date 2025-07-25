# setup.py
from setuptools import setup, find_packages

setup(
    name="trading_bot",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'Flask-Login',
        'Flask-Migrate',
        'python-dotenv',
    ],
    python_requires='>=3.8',
)