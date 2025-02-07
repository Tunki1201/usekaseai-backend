from fastapi import FastAPI
from app.views import (
    account_view,
    api_usage_view,
    audit_log_view,
    chapter_view,
    error_log_view,
    notification_view,
    payments_view,
    report_view,
    scraped_data_view,
    user_view,
)

# from app.controllers.user_controller import router as user_router  # Import the router

from app.db import (
    client,
    close_connection,
)  # Use MongoDB client and close function from db.py
from fastapi.middleware.cors import CORSMiddleware  # If you need CORS support
import uvicorn

# Create FastAPI app instance
app = FastAPI()

# CORS middleware to allow all origins (if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this according to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # Add JWT Auth Middleware
# app.add_middleware(AuthMiddleware)


# Event handler for MongoDB connection on startup
@app.on_event("startup")
async def startup_db():
    try:
        # Ping MongoDB to check connection
        await client.admin.command("ping")
        print("Connected to MongoDB!")
    except Exception as e:
        print("Error connecting to MongoDB:", e)


# Event handler to close MongoDB connection on shutdown
@app.on_event("shutdown")
async def shutdown_db():
    await close_connection()


# Include routers
app.include_router(user_view.router, prefix="/users")
app.include_router(scraped_data_view.router, prefix="/scraped_data")
app.include_router(error_log_view.router, prefix="/error_log")
app.include_router(notification_view.router, prefix="/notification")
app.include_router(chapter_view.router, prefix="/chapter")
app.include_router(api_usage_view.router, prefix="/api_usage")
app.include_router(audit_log_view.router, prefix="/audit_log")
app.include_router(payments_view.router, prefix="/payments")
app.include_router(account_view.router, prefix="/account")
app.include_router(report_view.router, prefix="/report")

# If running this script directly, start Uvicorn server
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
