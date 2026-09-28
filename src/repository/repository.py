from .database_connection import db
from sqlalchemy.orm import Session
from .schemas.schema import Error
import logging
logger=logging.getLogger(__name__)
class GraphRespository:

    def __init__(self):
        self.db: Session = db.get_session()
    def save_error_to_db(self,exception: str,function_name: str,file_name: str) -> None:
        session = db.get_session()
        try:
            error_row = Error(function_name=function_name,file_name=file_name,exception=exception,created_by="system",is_active=True)
            session.add(error_row)
            logger.error("error log  added to db")
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()