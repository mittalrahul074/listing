from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

engine = create_engine("sqlite:///listings.db", echo=True)

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String, nullable=False,unique=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    reviews = relationship("Review", back_populates="product")