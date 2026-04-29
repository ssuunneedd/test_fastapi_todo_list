from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String)
    priority = Column(Integer, default=0)
    due_date = Column(Date, nullable=True)
    created_date = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
