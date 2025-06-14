from fastapi import FastAPI
from app.database.connection import initialize_database
from app.routes import channels, countrys, priorities, alert_categories, messages


app = FastAPI(
    title="News API",
    version="1.0.0"
)

initialize_database()

app.include_router(messages.router)
app.include_router(alert_categories.router)
app.include_router(priorities.router)
app.include_router(channels.router)
app.include_router(countrys.router)
