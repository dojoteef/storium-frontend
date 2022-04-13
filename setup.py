"""
Setup script for Storium's writing suggestions web service
"""

import os
from typing import List, Tuple
from setuptools import setup, find_packages


EXTRAS_REQUIRE = {}
EXTRAS_REQUIRE["dev"] = [
    "jedi",
    "mypy",
    "black",
    "pylint",
    "pyyaml",
    "pytest",
    "coverage",
    "requests",
]
EXTRAS_REQUIRE["redis"] = ["aioredis==1.3.1"]
EXTRAS_REQUIRE["build"] = ["docker-compose==1.25.5", "idna==2.7"]
EXTRAS_REQUIRE["scipy"] = ["scipy==1.3.3"]
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
                    if os.path.splitext(f)[1] not in EXCLUDE_EXTS
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
        "nltk==3.4.5",
        "py-rouge==1.1",
        "aiocache==0.11.1",
        "aiofiles==0.4.0",
        "aiohttp==3.6.2",
        "alembic==1.2.1",
        "alembic-autogenerate-enums==0.0.2",
        "async_lru==1.0.2",
        "authlib==0.15.2",
        "httpx==0.16.1",  # required by authlib
        "celery==4.3.0",
        "jinja2==2.10.3",
        "asgiref==3.2.2",
        "fastapi==0.45.0",
        "markdown==3.3.3",
        "itsdangerous==1.1.0",  # required by starlette for sessions
        "regex==2020.1.8",
        "pydantic==1.1.1",
        "uvicorn[standard]==0.13.4",
        "gunicorn==19.9.0",
        "databases==0.2.5",
        "sqlalchemy==1.3.10",
        "sqlalchemy-utils==0.34.2",
        "async-generator==1.10;python_version<'3.7'",
        "async-exit-stack==1.0.1;python_version<'3.7'",
        # we don't explicitly use vine, but packages like celery do and they do
        # not correctly pin the version which causes issues with the latest
        # release of vine; make sure to use a compatible version
        "vine==1.3.0",
        # we don't explicitly use markupsafe, but jinja2 does and they do
        # not correctly pin the version which causes issues with the latest
        # release of markupsafe; make sure to use a compatible version
        # https://github.com/pallets/jinja/issues/1585
        "markupsafe<2.1",
    ],
    extras_require=EXTRAS_REQUIRE,
)
