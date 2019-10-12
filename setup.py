"""
Setup script for Storium's writing suggestions web service
"""

from setuptools import setup, find_packages


setup(
    name="woolgatherer",
    version="0.1",
    description="Web service which provides writing suggestions to the Storium platform",
    author="Nader Akoury",
    author_email="nsa@cs.umass.edu",
    url="https://github.com/ngram-lab/woolgatherer",
    python_requires=">=3.6.2",
    package_dir={"": "src"},
    packages=find_packages("src"),
    package_data={"": ["*.sql"]},
    scripts=["scripts/gw"],
    install_requires=["fastapi", "uvicorn", "gunicorn"],
)
