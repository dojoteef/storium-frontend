"""
The base class for all SQLAlchemy models
"""
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class DBBaseModel(object):
    """ The base DB model """

    @classmethod
    @declared_attr
    def __tablename__(cls):
        """ Automatically generate the table name from the class name """
        return cls.__name__.lower()

    id: Column = Column(Integer, primary_key=True)
