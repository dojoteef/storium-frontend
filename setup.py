"""
Setup script for Storium's writing suggestions web service
"""

import glob
from setuptools import setup, find_packages


EXTRAS_REQUIRE = {}
EXTRAS_REQUIRE["sqlite"] = ["aiosqlite"]
EXTRAS_REQUIRE["postgresql"] = ["asyncpg", "psycopg2"]


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
    scripts=["scripts/gw", "scripts/gw-createdb"],
    data_files=[
        ("share/woolgatherer", ["alembic.ini"]),
        ("share/woolgatherer/alembic", ["alembic/env.py", "alembic/script.py.mako"]),
        ("share/woolgatherer/alembic/versions", glob.glob("alembic/versions/*.py")),
    ],
    install_requires=[
        "alembic",
        "celery",
        "asgiref",
        "fastapi",
        "uvicorn",
        "gunicorn",
        "databases",
        "sqlalchemy",
        "sqlalchemy-utils",
        "async-generator;python_version<'3.7'",
        "async-exit-stack;python_version<'3.7'",
    ],
    extras_require=EXTRAS_REQUIRE,
)
