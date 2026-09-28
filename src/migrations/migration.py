from ..repository.schemas.schema import Error
from ..repository.database_connection import db
import inspect
LIST_OF_TABLES=[Error]

class Migration:
    def __init__(self):
        self.engine=db.engine
        self.inspector=db.inspector()
        
    def create_table(self):
        for model in LIST_OF_TABLES:
            if self.inspector.has_table(model.__tablename__):
                model.__table__.create(bind=self.engine)

