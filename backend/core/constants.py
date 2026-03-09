"""Shared constants — agent registry loaded live from openclaw.json."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Fallback display names (used when openclaw.json name field is empty) ──────
_DISPLAY_NAMES: dict[str, str] = {
    "main": "Jeeves",
    "matron": "Matron",
    "archivist": "The Archivist",
    "curator": "The Curator",
    "coordinator": "Coordinator",
    "market-intel": "Market Intel",
    "app-tracker": "App Tracker",
    "cv-tailor": "CV Tailor",
    "cover-letter": "Cover Letter",
    "interview-prep": "Interview Prep",
    "networking": "Networking",
    "portfolio-curator": "Portfolio Curator",
    "foundry-blacksmith": "The Blacksmith",
    "foundry-scout": "Scout",
    "foundry-spec": "Spec Writer",
    "foundry-builder": "Builder",
    "researcher": "Researcher",
    "strategist": "Strategist",
    "builder": "Builder",
    "designer": "Designer",
    "scribe": "Scribe",
    "consultant": "The Consultant",
    "board-chair": "Board Chair",
    "board-contrarian": "Contrarian",
    "board-risk": "Risk Officer",
    "board-quant": "Quant",
    "board-stakeholder": "Stakeholder",
    "board-strategy": "Strategist",
    "board-ops": "Ops",
    "dev-lead": "Dev Lead",
    "dev-recon": "Recon",
    "dev-spec": "Spec",
    "dev-impl": "Impl",
    "dev-gate": "Gate",
    "dev-verify": "Verify",
    "dev-shipper": "Shipper",
    "design-cd": "Creative Director",
    "design-ui": "UI/UX Designer",
    "design-copy": "Copywriter",
    "design-social": "Social Media",
    "design-guard": "Brand Guardian",
    "design-qa": "Design QA",
    "mktg-director": "Marketing Director",
    "mktg-pulse": "Pulse",
    "mktg-strat": "Strategy",
    "mktg-quill": "Quill",
    "mktg-canvas": "Canvas",
    "mktg-herald": "Herald",
    "mktg-gauge": "Gauge",
    "mktg-outpost": "Outpost",
}


def _load_from_openclaw() -> dict[str, str]:
    """Parse ~/.openclaw/openclaw.json and return id → display name mapping."""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    try:
        with open(config_path) as f:
            config = json.load(f)
        agents = config.get("agents", {}).get("list", [])
        result: dict[str, str] = {}
        for agent in agents:
            agent_id = agent.get("id", "").strip()
            if not agent_id:
                continue
            raw_name = agent.get("name", "")
            # Use the raw name if it's meaningfully different from the id,
            # otherwise fall back to our curated display names, then title-case the id.
            if raw_name and raw_name != agent_id:
                display = raw_name
            else:
                display = _DISPLAY_NAMES.get(
                    agent_id,
                    agent_id.replace("-", " ").title(),
                )
            result[agent_id] = display
        logger.info("Loaded %d agents from openclaw.json", len(result))
        return result
    except FileNotFoundError:
        logger.warning("openclaw.json not found; using fallback agent list")
        return _DISPLAY_NAMES.copy()
    except Exception as exc:
        logger.warning("Failed to load openclaw.json: %s; using fallback", exc)
        return _DISPLAY_NAMES.copy()


# Live-loaded canonical agent registry: agent_id → display name.
KNOWN_AGENTS: dict[str, str] = _load_from_openclaw()


# ── Rich metadata (hand-maintained for agents that matter) ────────────────────
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
        "responsibilities": ["School emails", "Calendar events", "Homework tracking", "Parent comms"],
    },
    "archivist": {
        "role": "Memory & Knowledge",
        "model": "claude-sonnet-4-5",
        "tier": "persistent",
        "workspace": "~/.openclaw/workspace",
        "can_spawn": False,
        "responsibilities": ["Chat log processing", "Memory consolidation", "Obsidian maintenance"],
    },
    "coordinator": {
        "role": "Job Search Orchestrator",
        "model": "claude-sonnet-4-5",
        "tier": "on-demand",
        "workspace": "~/.openclaw/workspace-coordinator",
        "can_spawn": True,
        "responsibilities": ["Dispatch job search agents", "Pipeline coherence"],
    },
    "foundry-blacksmith": {
        "role": "Build Orchestrator",
        "model": "claude-sonnet-4-5",
        "tier": "persistent",
        "workspace": "~/.openclaw/workspace-foundry-blacksmith",
        "can_spawn": True,
        "responsibilities": ["Overnight builds", "Scout→Spec→Builder flow"],
    },
    "board-chair": {
        "role": "Advisory Chair",
        "model": "claude-opus-4-6",
        "tier": "on-demand",
        "workspace": "~/.openclaw/workspace-board-chair",
        "can_spawn": True,
        "responsibilities": ["Strategic decisions", "Multi-model advisory panel"],
    },
    "dev-lead": {
        "role": "Dev Pipeline Lead",
        "model": "claude-opus-4-6",
        "tier": "on-demand",
        "workspace": "~/.openclaw/workspace-dev-lead",
        "can_spawn": True,
        "responsibilities": ["Feature implementation", "Code review", "PR shipping"],
    },
    "design-cd": {
        "role": "Creative Director",
        "model": "claude-opus-4-6",
        "tier": "on-demand",
        "workspace": "~/.openclaw/ws-design-cd",
        "can_spawn": True,
        "responsibilities": ["UI/UX", "Brand", "Social graphics", "Design QA"],
    },
    "mktg-director": {
        "role": "Marketing Director",
        "model": "claude-opus-4-6",
        "tier": "on-demand",
        "workspace": "~/.openclaw/workspace-mktg-director",
        "can_spawn": True,
        "responsibilities": ["Content strategy", "Campaign management", "Analytics"],
    },
    "researcher": {
        "role": "Researcher",
        "model": "claude-sonnet-4-6",
        "tier": "on-demand",
        "workspace": "~/.openclaw/workspace-researcher",
        "can_spawn": False,
        "responsibilities": ["Market research", "Fact-checking", "Competitive analysis"],
    },
    "strategist": {
        "role": "Strategist",
        "model": "claude-opus-4-6",
        "tier": "on-demand",
        "workspace": "~/.openclaw/workspace-strategist",
        "can_spawn": False,
        "responsibilities": ["Planning", "Risk assessment", "Roadmap decisions"],
    },
    "scribe": {
        "role": "Scribe",
        "model": "claude-sonnet-4-6",
        "tier": "on-demand",
        "workspace": "~/.openclaw/workspace-scribe",
        "can_spawn": False,
        "responsibilities": ["Documentation", "Reports", "Changelogs"],
    },
}
