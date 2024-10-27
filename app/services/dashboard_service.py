# app/services/dashboard_service.py

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi import HTTPException
from typing import List, Dict
from datetime import datetime, timedelta
from app.schemas.dashboard import DashboardItem

class Dashboard_Service:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.assigned_slates = self.db.get_collection("Assigned_Slates")
        self.projects = self.db.get_collection("Projects")
        self.users = self.db.get_collection("Users")
        self.org_metrics = self.db.get_collection("OrganizationMetrics")

    async def get_dashboard_data(self, owner_org: str) -> List[DashboardItem]:
        pipeline = [
            {"$match": {"owner_org": owner_org}},
            {"$lookup": {
                "from": "Projects",
                "localField": "projectId",
                "foreignField": "projectId",
                "as": "project_info"
            }},
            {"$unwind": {
                "path": "$project_info",
                "preserveNullAndEmptyArrays": True
            }},
            {"$lookup": {
                "from": "Users",
                "localField": "assignee",
                "foreignField": "email",
                "as": "user_info"
            }},
            {"$unwind": {
                "path": "$user_info",
                "preserveNullAndEmptyArrays": True
            }},
            {"$project": {
                "id": {"$toString": "$_id"},
                "project_name": "$project_info.projectName",
                "project_type": "$project_info.projectType",
                "slate_name": "$title",
                "status": {"$cond": ["$status", "Completed", "Active"]},
                "assignee_name": "$user_info.name",
                "assignee_email": "$assignee",
                "assigned_date": "$assigned_date",
                "due_date": "$due_date",
                "description": "$description",
                "owner_org": "$owner_org",
                "last_updated": "$last_updated"
            }}
        ]
        
        result = await self.db.Assigned_Slates.aggregate(pipeline).to_list(None)
        return [DashboardItem(**item) for item in result]

    async def get_dashboard_kpis(self, owner_org: str) -> Dict:
        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        three_months_ago = current_date - timedelta(days=90)
        
        latest_metrics = await self.org_metrics.find_one(
            {"owner_org": owner_org},
            sort=[("date", -1)]
        )
        
        month_ago_metrics = await self.org_metrics.find_one({
            "owner_org": owner_org,
            "date": {"$gte": current_date - timedelta(days=31), "$lt": current_date - timedelta(days=29)}
        })
        
        if month_ago_metrics and month_ago_metrics["average_overdue"] > 0:
            percentage_change = ((latest_metrics["average_overdue"] - month_ago_metrics["average_overdue"]) / 
                                 month_ago_metrics["average_overdue"]) * 100
        else:
            percentage_change = 0
        
        project_health_data = await self.org_metrics.find(
            {
                "owner_org": owner_org,
                "date": {"$gte": three_months_ago}
            },
            {"date": 1, "project_health": 1, "_id": 0}
        ).sort("date", 1).to_list(None)
        
        return {
            "average_overdue": {
                "current": latest_metrics["average_overdue"],
                "percentage_change": round(percentage_change, 2)
            },
            "project_health": [
                {
                    "date": item["date"].strftime("%Y-%m-%d"),
                    "health": item["project_health"]
                } for item in project_health_data
            ]
        }