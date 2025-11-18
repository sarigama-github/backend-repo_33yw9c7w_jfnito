"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Example schemas (kept for reference):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# SaaS Construction Time Tracking Schemas

class Project(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    client: Optional[str] = Field(None, description="Client name")

class Task(BaseModel):
    project_id: str = Field(..., description="Related project id (stringified ObjectId)")
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task details")
    status: str = Field("open", description="open | in_progress | done")

class TimeEntry(BaseModel):
    task_id: str = Field(..., description="Related task id (stringified ObjectId)")
    user_id: Optional[str] = Field(None, description="User id if applicable")
    start_time: datetime = Field(..., description="When the timer started (UTC)")
    end_time: Optional[datetime] = Field(None, description="When the timer stopped (UTC)")
    duration_sec: Optional[int] = Field(None, ge=0, description="Duration in seconds (computed when stopped)")
    note: Optional[str] = Field(None, description="Optional note")
