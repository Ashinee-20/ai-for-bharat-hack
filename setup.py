from setuptools import setup, find_packages

setup(
    name="agribridge-ai",
    version="1.0.0",
    description="AgriBridge AI - Offline-first agricultural intelligence platform",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "boto3>=1.34.34",
        "fastapi>=0.109.0",
        "pydantic>=2.5.3",
        "psycopg2-binary>=2.9.9",
        "opensearch-py>=2.4.2",
    ],
)
