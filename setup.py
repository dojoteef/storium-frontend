"""
Setup script for Storium's writing suggestions web service
"""

import os
from typing import List, Tuple
from setuptools import setup, find_packages


EXTRAS_REQUIRE = {}
EXTRAS_REQUIRE["sqlite"] = ["aiosqlite==0.10.0"]
EXTRAS_REQUIRE["postgresql"] = ["asyncpg==0.20.0", "psycopg2==2.8.4"]

EXCLUDE_DIRS = ["__pycache__"]
EXCLUDE_EXTS = [".pyc", ".pyo"]
DATA_DIR = os.path.join("share", "woolgatherer")


def collect_data_files(paths: List[str]):
    """
    Include all files underneath the base_dir
    """
    base_files: List[str] = []
    data_files: List[Tuple[str, List[str]]] = []
    for path in paths:
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                if os.path.basename(root) in EXCLUDE_DIRS:
                    continue
                root_files = [
                    os.path.join(root, f)
                    for f in files
                    if os.path.splitext(f) not in EXCLUDE_EXTS
                ]

                if root_files:
                    data_files.append((os.path.join(DATA_DIR, root), root_files))
        else:
            base_files.append(path)

    if base_files:
        data_files.append((DATA_DIR, base_files))

    return data_files


DATA_FILES = collect_data_files(
    ["alembic.ini", "alembic", "sql", "static", "templates"]
)


setup(
    name="woolgatherer",
    version="0.1",
    description="Web service that provides writing suggestions to the Storium platform",
    author="Nader Akoury",
    author_email="nsa@cs.umass.edu",
    url="https://github.com/ngram-lab/woolgatherer",
    python_requires=">=3.6",
    package_dir={"": "src"},
    packages=find_packages("src"),
    scripts=[
        "scripts/gw",
        "scripts/gw-model",
        "scripts/gw-tasks",
        "scripts/gw-createdb",
    ],
    data_files=DATA_FILES,
    install_requires=[
        "aiofiles==0.4.0",
        "aiohttp==3.6.2",
        "alembic==1.2.1",
        "alembic-autogenerate-enums==0.0.2",
        "celery==4.3.0",
        "jinja2==2.10.3",
        "asgiref==3.2.2",
        "fastapi==0.45.0",
        "regex==2020.1.8",
        "pydantic==1.1.1",
        "uvicorn==0.9.0",
        "gunicorn==19.9.0",
        "databases==0.2.5",
        "sqlalchemy==1.3.10",
        "sqlalchemy-utils==0.34.2",
        "async-generator==1.10;python_version<'3.7'",
        "async-exit-stack==1.0.1;python_version<'3.7'",
    ],
    extras_require=EXTRAS_REQUIRE,
)
