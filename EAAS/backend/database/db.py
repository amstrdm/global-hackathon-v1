import os
from contextlib import contextmanager

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.logging_config import get_logger

from .models import Base

logger = get_logger("database.db")

current_dir = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(current_dir, "data")
os.makedirs(DB_FOLDER, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(DB_FOLDER, "escrow.db")}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Creates all Tables if they don't exist.
    """

    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Yields a Database Session for dependency injection.
    Closes automatically after use.
    - Commits successful transactions.
    - Rolls back transactions on any exception.
    - Logs only unexpected exceptions as errors.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except HTTPException:
        # If an HTTPException is raised, the request is ending.
        # We should roll back any potential changes and re-raise the exception.
        # We DON'T log this as an error because it's expected application flow.
        db.rollback()
        raise
    except Exception as e:
        # This catches actual database or other unexpected code errors.
        # These are the ones we want to log as a DB_ERROR.
        db.rollback()
        logger.error(f"[DB_ERROR]: {e}")
        raise
    finally:
        db.close()
        logger.debug("Database connection closed")


@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()
