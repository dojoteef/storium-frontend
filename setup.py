"""
Setup script for Storium's writing suggestions web service
"""

import sys
from setuptools import setup, find_packages


REQUIRES = ["fastapi", "uvicorn", "gunicorn", "SQLAlchemy"]
if sys.version_info < (3, 7):
    REQUIRES += ["async-exit-stack", "async-generator"]


EXTRAS_REQUIRE = {}
EXTRAS_REQUIRE["all"] = ["psycopg2"]
EXTRAS_REQUIRE["postgres"] = ["psycopg2"]
print(f"{EXTRAS_REQUIRE}")


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
    package_data={"": ["*.sql"]},
    scripts=["scripts/gw"],
    install_requires=REQUIRES,
    extras_require=EXTRAS_REQUIRE,
)
