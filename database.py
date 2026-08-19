# Database connection. One place that knows how to reach the database and how
# to hand out a session for a request.

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Postgres when DATABASE_URL is set, which is what happens in Kubernetes, and
# a SQLite file otherwise. Same code either way because SQLAlchemy hides the
# difference, and it means the tests run without a database server.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./hr_interview.db")

# SQLite refuses to let one thread use a connection another thread opened, and
# FastAPI answers requests on several threads. Postgres has no such rule, so
# this setting is only passed when we are actually on SQLite.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def get_db():
    # A FastAPI dependency. Each request gets its own session, and the finally
    # block closes it even when the endpoint raises, so connections are not
    # leaked back into the pool.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
