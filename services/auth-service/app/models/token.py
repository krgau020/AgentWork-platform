"""
Stores refresh tokens for revocation control.
"""

from sqlalchemy import Column, Integer, String
from app.db.base import Base

class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    refresh_token = Column(String, unique=True)