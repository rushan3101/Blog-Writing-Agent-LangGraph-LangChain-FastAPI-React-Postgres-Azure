from app.db.session import engine

with engine.connect() as conn:
    print("Connected to Azure Postgres successfully")