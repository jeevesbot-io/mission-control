"""Shared constants used across modules."""

# Canonical agent registry: agent_id -> display name.
# Used by agents, office, and any module that needs a full agent list.
KNOWN_AGENTS: dict[str, str] = {
    "main": "Jeeves",
    "matron": "Matron",
    "archivist": "The Archivist",
    "curator": "The Curator",
    "foundry-blacksmith": "The Blacksmith",
    "foundry-scout": "Scout",
    "foundry-spec": "Spec Writer",
    "foundry-builder": "Builder",
}

# Rich agent metadata: role, model tier, workspace path, capabilities.
AGENT_METADATA: dict[str, dict] = {
    "main": {
        "role": "Chief of Staff",
        "model": "claude-sonnet-4-6",
        "tier": "persistent",
        "workspace": "~/.openclaw/workspace",
        "can_spawn": True,
        "responsibilities": ["Orchestration", "User interface", "Task routing", "Daily briefings"],
    },
    "matron": {
        "role": "School Communications",
        "model": "claude-sonnet-4-5",
        "tier": "persistent",
        "workspace": "~/.openclaw/workspace-matron",
        "can_spawn": False,
        "responsibilities": [
            "School emails",
            "Calendar events",
            "Homework tracking",
            "Parent comms",
        ],
    },
    "archivist": {
        "role": "Memory & Knowledge",
        "model": "claude-sonnet-4-5",
        "tier": "persistent",
        "workspace": "~/.openclaw/workspace-archivist",
        "can_spawn": False,
        "responsibilities": [
            "Chat log processing",
            "Memory consolidation",
            "Knowledge indexing",
            "Obsidian maintenance",
        ],
    },
    "curator": {
        "role": "Content Curator",
        "model": "claude-sonnet-4-5",
        "tier": "persistent",
        "workspace": "~/.openclaw/workspace-curator",
        "can_spawn": False,
        "responsibilities": ["Reading list", "Media recommendations", "Content discovery"],
    },
    "foundry-blacksmith": {
        "role": "Build Orchestrator",
        "model": "claude-sonnet-4-5",
        "tier": "persistent",
        "workspace": "~/.openclaw/workspace-foundry",
        "can_spawn": True,
        "responsibilities": [
            "Overnight builds",
            "Pipeline orchestration",
            "Scout→Spec→Builder flow",
        ],
    },
    "foundry-scout": {
        "role": "Trend Discovery",
        "model": "claude-haiku-4",
        "tier": "on-demand",
        "workspace": "~/.openclaw/workspace-foundry",
        "can_spawn": False,
        "responsibilities": ["AI trend scanning", "Opportunity identification"],
    },
    "foundry-spec": {
        "role": "Product Specification",
        "model": "claude-sonnet-4-5",
        "tier": "on-demand",
        "workspace": "~/.openclaw/workspace-foundry",
        "can_spawn": False,
        "responsibilities": ["Spec writing", "Architecture design", "Feasibility analysis"],
    },
    "foundry-builder": {
        "role": "Code Builder",
        "model": "claude-opus-4-6",
        "tier": "on-demand",
        "workspace": "~/.openclaw/workspace-foundry",
        "can_spawn": False,
        "responsibilities": ["Code generation", "Testing", "Deployment"],
    },
}
