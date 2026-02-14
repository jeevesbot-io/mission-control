"""Pydantic schemas for the School module."""

import datetime

from pydantic import BaseModel


class SchoolEvent(BaseModel):
    id: int
    child: str | None
    summary: str
    description: str | None
    event_date: str | None
    event_end_date: str | None
    event_time: str | None
    school_id: str | None


class CalendarEvent(BaseModel):
    id: str
    summary: str
    start_date: str | None  # YYYY-MM-DD for all-day
    start_datetime: str | None  # ISO for timed
    end_date: str | None
    end_datetime: str | None
    all_day: bool
    child: str | None  # inferred from summary


class CalendarEventsResponse(BaseModel):
    events: list[CalendarEvent]
    total: int
    window_start: str
    window_end: str


class SchoolEventsResponse(BaseModel):
    events: list[SchoolEvent]
    total: int


class SchoolEmail(BaseModel):
    id: int
    email_id: str
    subject: str | None
    sender: str | None
    child: str | None
    school_id: str | None
    preview: str | None
    processed_at: datetime.datetime | None


class SchoolEmailsResponse(BaseModel):
    emails: list[SchoolEmail]
    total: int


class TodoistTask(BaseModel):
    id: str
    content: str
    description: str | None
    due_date: str | None
    todoist_id: str | None
    created_at: datetime.datetime | None


class TodoistTasksResponse(BaseModel):
    tasks: list[TodoistTask]
    total: int


class SchoolStatsResponse(BaseModel):
    upcoming_events: int
    total_emails: int
    total_tasks: int
