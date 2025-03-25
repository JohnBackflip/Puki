from setuptools import setup, find_packages

setup(
    name="security_service",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.68.1",
        "uvicorn==0.15.0",
        "mysql-connector-python==8.0.33",
        "python-jose==3.3.0",
        "passlib==1.7.4",
        "python-multipart==0.0.5",
        "aio-pika==8.0.3",
        "httpx==0.24.1",
        "pytest==6.2.5",
        "pytest-asyncio==0.16.0",
        "pytest-cov==2.12.1",
        "python-dotenv==0.19.0",
        "alembic==1.7.1"
    ],
) 