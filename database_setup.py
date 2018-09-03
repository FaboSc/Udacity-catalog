import os
import sys
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key = True)
    name = Column(String(100), nullable = False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }



class User(Base):
    __tablename__ = 'user'

    name = Column(String(100), nullable = False)
    email = Column(String(100), nullable = False)
    picture = Column(String(100), nullable = True)
    id = Column(Integer, primary_key = True)


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey(User.id), nullable = True)
    name = Column(String(100), nullable = False)
    description = Column(String(10000), nullable = False)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    category_name = Column(String, ForeignKey(Category.name))
    category = relationship(Category)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
        'name': self.name,
        'description' : self.description,
        'id': self.id,
        'user_id': self.user_id

    }

engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)