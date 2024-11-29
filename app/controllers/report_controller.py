from typing import Dict, Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from app.models.report_model import report_collection, report_helper, Report
from datetime import datetime
from app.utils.report_generator import ReportGenerator
from app.models.scraped_data_model import scraped_data_collection
from pymongo.errors import PyMongoError

# CRUD Operations for Report


# Get all reports
async def get_all_reports():
    reports = await report_collection.find().to_list(1000)
    return [report_helper(report) for report in reports]


# Get a specific report by ID
async def get_report_by_id(id: str):
    report = await report_collection.find_one({"_id": ObjectId(id)})
    if report:
        return report_helper(report)
    return None


# Create a new report
async def create_report(report: Report):
    report_dict = report.dict(by_alias=True)
    report_dict["created_at"] = datetime.utcnow()
    new_report = await report_collection.insert_one(report_dict)
    created_report = await report_collection.find_one({"_id": new_report.inserted_id})
    return report_helper(created_report)


# Update an existing report by ID
async def update_report(id: str, report_data: Report):
    updated_report = await report_collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": report_data.dict(exclude_unset=True)},
        return_document=True,
    )
    if updated_report:
        return report_helper(updated_report)
    return None


# Delete a report by ID
async def delete_report(id: str):
    result = await report_collection.delete_one({"_id": ObjectId(id)})
    return result.deleted_count > 0


async def generate_report(url: str, clientId: str) -> dict:
    """
    Fetch company data, check if a report already exists for the given URL and clientId,
    and either return the existing report or generate a new one.

    :param url: The company URL.
    :param clientId: The client ID for the report.
    :return: The generated or existing report data.
    """
    try:
        # Check if a report already exists for this url and clientId
        existing_report = await report_collection.find_one(
            {"company_url": url, "client_id": clientId}
        )

        if existing_report:
            # If a report already exists, return it
            return existing_report.get("chapters", {})

        # If no existing report is found, proceed with generating a new report
        # Fetch the company data from the database
        company_data = await scraped_data_collection.find_one({"company_url": url})
        if not company_data:
            return None  # No company data found, so no report can be generated

        # Use the ReportGenerator to create the report
        report = await ReportGenerator.generate_report(company_data)

        # Create the new report object
        report_data = {
            "number": "RPT-DEFAULT",  # Or generate a unique identifier if needed
            "chapters": report,  # Store the provided chapters
            "tone": "neutral",  # Default or set dynamically
            "downloaded": False,  # Initial state
            "created_at": datetime.utcnow(),
            "client_id": clientId,
            "account_id": "UNKNOWN_ACCOUNT",  # Update based on your requirements
            "company_url": url,
        }

        # Insert the new report into the database
        await report_collection.insert_one(report_data)

        # Return the inserted report
        return report_data["chapters"]

    except PyMongoError as e:
        print(f"Database error in generate_report: {str(e)}")
        raise Exception("Database error occurred.")
    except Exception as e:
        print(f"Error in generate_report: {str(e)}")
        raise Exception("An error occurred while generating the report.")
