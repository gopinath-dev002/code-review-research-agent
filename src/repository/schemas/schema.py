from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column,String,Integer,Text,TIMESTAMP,func,Boolean)
Base=declarative_base()
class Error(Base):
    __tablename__ = "errors"
    error_id = Column(Integer, primary_key=True)
    function_name = Column(String(30), nullable=False)
    file_name = Column(String(30), nullable=False)
    exception = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    created_by = Column(String(30), nullable=False)
    updated_by = Column(String(30))
    is_active = Column(Boolean, default=True)