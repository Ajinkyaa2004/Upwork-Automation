from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from .config import config
import os

os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{config.DATABASE_PATH}")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Draft(Base):
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True)
    room_id = Column(String, index=True)
    room_name = Column(String, nullable=True)
    client_message = Column(Text)
    draft_text = Column(Text)
    status = Column(String, default="pending")  # pending, approved, rejected, sent, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    upwork_message_id = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
