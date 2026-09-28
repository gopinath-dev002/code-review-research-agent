from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from ..setting import credentials
import logging
logger=logging.getLogger(__name__)

class Database:
    _instance = None   

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        self.engine = self._create_engine()
        self.session_local = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False
        )

        self._initialized = True  

    def _create_engine(self):
        db_url = (
            f"postgresql+psycopg://{credentials.db_username}:"
            f"{credentials.db_password}@"
            f"{credentials.db_host}:"
            f"{credentials.db_port}/"
            f"{credentials.db_name}"
        )
        return create_engine(db_url, pool_pre_ping=True)

    def get_session(self):
        return self.SessionLocal()

    def inspector(self):
        return inspect(self.engine)

    def test_connection(self):
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print("DB Connection Error:", e)
            logger.exception("DB connection error:",e)
            return False


db = Database()