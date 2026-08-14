from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pymysql

from config.settings import settings

connect_args = {
    "host": settings.MYSQL_HOST,
    "user": settings.MYSQL_USER,
    "password": settings.MYSQL_PASSWORD,
    "database": settings.MYSQL_DATABASE,
    "port": settings.MYSQL_PORT,
    "charset": "utf8mb4",
    }

# verify pymysql works
conn = pymysql.connect(**connect_args)
print("✅ Raw PyMySQL connection successful")
conn.close()

# sqlalchemy use the exact same connection
engine = create_engine(
    "mysql+pymysql://",
    creator=lambda: pymysql.connect(**connect_args),
    echo=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

if __name__ == "__main__":
    from sqlalchemy import text

    with engine.connect() as conn:
        print(conn.execute(text("SELECT VERSION")).scalar())
