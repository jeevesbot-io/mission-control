"""Pydantic schemas for the School module."""

import datetime

from pydantic import BaseModel


class SchoolEvent(BaseModel):
    id: int
    title: str
    description: str | None
    start_time: datetime.datetime
    end_time: datetime.datetime | None
    location: str | None
    all_day: bool


class SchoolEventsResponse(BaseModel):
    events: list[SchoolEvent]
    total: int


class SchoolEmail(BaseModel):
    id: int
    subject: str
    sender: str
    preview: str
    received_at: datetime.datetime
    is_read: bool


class SchoolEmailsResponse(BaseModel):
    emails: list[SchoolEmail]
    total: int


class TodoistTask(BaseModel):
    id: str
    content: str
    description: str | None
    priority: int
    due_date: str | None
    is_completed: bool
    project_name: str | None


class TodoistTasksResponse(BaseModel):
    tasks: list[TodoistTask]
    total: int


class SchoolStatsResponse(BaseModel):
    upcoming_events: int
    unread_emails: int
    pending_tasks: int
    completed_today: int
