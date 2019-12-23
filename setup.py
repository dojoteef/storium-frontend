"""
Setup script for Storium's writing suggestions web service
"""

import glob
from setuptools import setup, find_packages


EXTRAS_REQUIRE = {}
EXTRAS_REQUIRE["sqlite"] = ["aiosqlite==0.10.0"]
EXTRAS_REQUIRE["postgresql"] = ["asyncpg==0.20.0", "psycopg2==2.8.4"]


setup(
    name="woolgatherer",
    version="0.1",
    description="Web service which provides writing suggestions to the Storium platform",
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
    data_files=[
        ("share/woolgatherer", ["alembic.ini"]),
        ("share/woolgatherer/alembic", ["alembic/env.py", "alembic/script.py.mako"]),
        ("share/woolgatherer/alembic/versions", glob.glob("alembic/versions/*.py")),
    ],
    install_requires=[
        "aiohttp==3.6.2",
        "alembic==1.2.1",
        "alembic-autogenerate-enums==0.0.2",
        "celery==4.3.0",
        "asgiref==3.2.2",
        "fastapi==0.45.0",
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
