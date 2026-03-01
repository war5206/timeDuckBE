from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config import SQL_ECHO, require_env

# 数据库创建
# CREATE DATABASE aichat DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

engine = create_engine(require_env("DB_URL"), echo=SQL_ECHO)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
