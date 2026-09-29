import sqlite3
from caspian_surveyor.bootstrap.cs_baseline_config import (
    DATABASE_SCHEMA,
    DATABASE_FILE,
    DATABASE_DIRECTORY
)

# --- if directory doesn't exist, create
DATABASE_DIRECTORY.mkdir(parents=True, exist_ok=True)

with DATABASE_SCHEMA.open("r", encoding="utf-8") as file:
    schema = file.read()

conn = sqlite3.connect(DATABASE_FILE)
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript(schema)

try:
    conn.execute("""
        INSERT INTO bodies (
            database_system_id,
            elite_body_id,
            body_name
        )
        VALUES (?, ?, ?)
    """, (999999, 1, "Definitely Not Real"))

    conn.commit()

except sqlite3.IntegrityError as error:
    print(f"Foreign key enforcement works: {error}")
    conn.rollback()
# if __name__ == "__main__":
#     print(DATABASE_FILE)
#     print(DATABASE_SCHEMA)