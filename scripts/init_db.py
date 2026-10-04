import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import create_engine
from app import models

db_url = os.environ["DATABASE_URL"]
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

print("Connecting to database and creating all tables (if not already present)...")
engine = create_engine(db_url)
models.Base.metadata.create_all(bind=engine)
print("Done. Tables now in the database:")
for table in models.Base.metadata.tables.keys():
    print(f"  - {table}")
