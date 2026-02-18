#!/usr/bin/env python3
"""
Migrate VidClaw tasks.json for War Room module.

- Adds project, tags, estimatedHours, actualHours fields to each task
- Creates projects.json with the 10 predefined projects if it doesn't exist

Run from repo root:
    python3 scripts/migrate_warroom_tasks.py
"""

import json
from pathlib import Path

DASHBOARD_DATA = Path.home() / ".openclaw" / "workspace" / "dashboard" / "data"
TASKS_FILE = DASHBOARD_DATA / "tasks.json"
PROJECTS_FILE = DASHBOARD_DATA / "projects.json"

INITIAL_PROJECTS = [
    {"id": "mission-control",  "name": "Mission Control",   "icon": "Scaffold",  "color": "purple",  "description": "Unified dashboard, FastAPI + Vue 3 plugin architecture",                       "status": "active", "order": 1},
    {"id": "matron",           "name": "Matron",            "icon": "Hospital",  "color": "pink",    "description": "School email processing and calendar management for Natty, Elodie, and Florence", "status": "active", "order": 2},
    {"id": "sports-dashboard", "name": "Sports Dashboard",  "icon": "Football",  "color": "green",   "description": "Multi-sport analytics platform: Premier League, cricket, rugby",              "status": "active", "order": 3},
    {"id": "curator",          "name": "The Curator",       "icon": "VHS",       "color": "blue",    "description": "Media library management via Radarr/Sonarr, weekly recommendations",         "status": "active", "order": 4},
    {"id": "archivist",        "name": "The Archivist",     "icon": "Scroll",    "color": "amber",   "description": "Memory curator: processes chat logs, consolidates daily notes",               "status": "active", "order": 5},
    {"id": "job-hunt",         "name": "Job Hunt",          "icon": "Briefcase", "color": "indigo",  "description": "Seven-agent autonomous job search: market intelligence, CV tailoring, interview prep", "status": "active", "order": 6},
    {"id": "openclaw-platform","name": "OpenClaw Platform", "icon": "Gear",      "color": "red",     "description": "Core platform improvements, skills, security hardening",                      "status": "active", "order": 7},
    {"id": "war-room",         "name": "War Room",          "icon": "Lightning", "color": "orange",  "description": "Task management and agent control center, VidClaw to Mission Control migration", "status": "active", "order": 8},
    {"id": "social-media",     "name": "Social Media",      "icon": "Phone",     "color": "cyan",    "description": "Threads and X monitoring, weekly social briefing, influencer tracking",       "status": "active", "order": 9},
    {"id": "side-hustles",     "name": "Side Hustles",      "icon": "Bulb",      "color": "yellow",  "description": "Various business ventures and experiments",                                    "status": "active", "order": 10},
]

# Map task titles to project IDs (from War Room - Project Definitions.md)
TASK_PROJECT_MAP = {
    "Build Security Council":                    "openclaw-platform",
    "Build Job Hunt Decision Council":           "job-hunt",
    "Build Knowledge Base with RAG":             "openclaw-platform",
    "Build Daily Briefing System":               "openclaw-platform",
    "Implement Model-Specific Prompt Optimization": "openclaw-platform",
    "Adopt Hybrid Code Philosophy":              "openclaw-platform",
    "Build Platform Council":                    "openclaw-platform",
    "Implement Urgent Email Monitoring":         "matron",
    "Self-Updating OpenClaw Checker":            "openclaw-platform",
    "Learning from Feedback System":             "openclaw-platform",
    "Cron Job Monitoring Dashboard":             "mission-control",
}


def migrate_tasks() -> int:
    if not TASKS_FILE.exists():
        print(f"No tasks file found at {TASKS_FILE} — nothing to migrate.")
        return 0

    raw = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    migrated = 0

    for task in raw:
        changed = False
        if "project" not in task:
            task["project"] = TASK_PROJECT_MAP.get(task.get("title", ""), None)
            changed = True
        if "tags" not in task:
            task["tags"] = []
            changed = True
        if "estimatedHours" not in task:
            task["estimatedHours"] = None
            changed = True
        if "actualHours" not in task:
            task["actualHours"] = None
            changed = True
        if changed:
            migrated += 1

    TASKS_FILE.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    return migrated


def create_projects() -> bool:
    if PROJECTS_FILE.exists():
        print(f"projects.json already exists at {PROJECTS_FILE} — skipping creation.")
        return False

    DASHBOARD_DATA.mkdir(parents=True, exist_ok=True)
    PROJECTS_FILE.write_text(json.dumps(INITIAL_PROJECTS, indent=2), encoding="utf-8")
    return True


def main() -> None:
    print(f"Dashboard data directory: {DASHBOARD_DATA}")
    print()

    migrated = migrate_tasks()
    if migrated > 0:
        print(f"✓ Migrated {migrated} task(s) — added project, tags, estimatedHours, actualHours fields")
    else:
        print("✓ All tasks already have required fields (no changes needed)")

    created = create_projects()
    if created:
        print(f"✓ Created projects.json with {len(INITIAL_PROJECTS)} projects")

    print()
    print("Migration complete. You can now start Mission Control and verify:")
    print(f"  GET http://localhost:5055/api/warroom/tasks")
    print(f"  GET http://localhost:5055/api/warroom/projects")


if __name__ == "__main__":
    main()
