# for runtime
import sys
# for creating mapper/database code
from sqlalchemy import Column, ForeignKey, Integer, String
# configure class code
from sqlalchemy.ext.declarative import declarative_base
# for foreign keys mapper code
from sqlalchemy.orm import relationship
# for creating engine
from sqlalchemy import create_engine

Base = declarative_base()

# creating database table class
class Restaurant(Base):
    __tablename__ = 'restaurant'

    # creating column
    name = Column(
        String(80), nullable = False)
    # creating column
    id = Column(
        Integer, primary_key = True)
# creating database table class
class MenuItem(Base):
    __tablename__ = 'menu_item'

    name = Column(
        String(80), nullable = False)

    id = Column(Integer, primary_key = True)

    course = Column(String(250))

    description = Column(String(250))

    price = Column(String(8))

    restaurant_id = Column(
        Integer, ForeignKey('restaurant.id'))

    restaurant = relationship(Restaurant)

    @property
    def serialize(self):
        #Return object data in json format
        return {
            'name' : self.name,
            'description' : self.description,
            'id' : self.id,
            'price' : self.price,
            'course' : self.course,
        }


# creating instance of engine with database
engine = create_engine(
    'sqlite:///restaurantmenu.db')

# sets up database
Base.metadata.create_all(engine)