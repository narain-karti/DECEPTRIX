from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime

from core.database import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True) # case_id
    modality = Column(String) # "media" or "text"
    status = Column(String, default="pending") # pending, processing, completed, failed
    progress = Column(Integer, default=0)
    current_step = Column(String, default="Initializing")
    
    # Media specific
    filename = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    sha256 = Column(String, nullable=True)
    
    # Text specific
    text_content = Column(String, nullable=True)
    
    # Results
    verdict = Column(String, nullable=True)
    evidence = Column(JSON, nullable=True)
    report_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
