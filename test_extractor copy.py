from sqlalchemy import inspect, text
from backend.db import engine, SessionLocal

def print_all_tables():

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    db = SessionLocal()

    print("\n================ DATABASE SNAPSHOT ================\n")

    for table in tables:

        print(f"\n🔹 TABLE: {table}")
        print("-" * 50)

        result = db.execute(
            text(f"SELECT * FROM {table}")
        )

        rows = result.fetchall()

        if not rows:
            print(" (empty table)")
            continue

        for row in rows:
            print(dict(row._mapping))

    db.close()


if __name__ == "__main__":
    print_all_tables()