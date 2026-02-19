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
