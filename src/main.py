from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from .setting import credentials
from .utils.logger import setup_logging
setup_logging()
from .routes.route import router
from .repository.database_connection import db
from .migrations.migration import Migration


logger = logging.getLogger(__name__)



def create_app():

    app = FastAPI(
        title="Coffee shop Bot",
        description="Manage coffee shop",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    @app.on_event("startup")
    def stateup_event():

        if not db.test_connection():
            logger.error("Database connection failed")
            sys.exit(1)
        else:
            logger.info("Database connected Successfully")

        migration = Migration()
        migration.create_table()

        logger.info("Tables created successfully")

    return app


app = create_app()