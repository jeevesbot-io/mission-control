import importlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_KEYS = {"id", "name", "icon", "router", "prefix"}


def discover_modules() -> list[dict]:
    """Scan modules/ directory and import MODULE_INFO from each package."""
    modules_dir = Path(__file__).resolve().parent.parent / "modules"
    discovered = []

    for child in sorted(modules_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue

        module_path = f"modules.{child.name}"
        try:
            mod = importlib.import_module(module_path)
        except Exception:
            logger.exception("Failed to import module: %s", module_path)
            continue

        info = getattr(mod, "MODULE_INFO", None)
        if info is None:
            continue

        missing = REQUIRED_KEYS - set(info.keys())
        if missing:
            logger.error("Module %s missing keys: %s", child.name, missing)
            continue

        discovered.append(info)
        logger.info("Discovered module: %s (%s)", info["name"], info["prefix"])

    return discovered
