import importlib
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

REGISTERED_PLUGINS: Dict[str, Dict[str, Any]] = {}

BUILTIN_PLUGINS = {
    "biology": {
        "name": "Biology / Drug Discovery",
        "module": "app.services.biology_service",
        "description": "BioNeMo-powered molecular generation, protein analysis, and drug discovery",
        "category": "science",
        "status": "active",
    },
    "vision": {
        "name": "Vision / Multimodal Reasoning",
        "module": "app.services.vision_service",
        "description": "Cosmos R2-powered embodied reasoning, image/video analysis",
        "category": "perception",
        "status": "active",
    },
    "robotics": {
        "name": "Robotics / Physical AI",
        "module": "app.services.robotics_service",
        "description": "ROS2/Isaac-compatible robot planning, navigation, and simulation",
        "category": "control",
        "status": "active",
    },
}


def register_plugin(plugin_id: str, config: Dict[str, Any]) -> bool:
    try:
        module = importlib.import_module(config["module"])
        REGISTERED_PLUGINS[plugin_id] = {
            **config,
            "loaded": True,
            "module_ref": module,
        }
        logger.info(f"Plugin registered: {plugin_id}")
        return True
    except ImportError as e:
        logger.warning(f"Plugin {plugin_id} module not found: {e}")
        REGISTERED_PLUGINS[plugin_id] = {
            **config,
            "loaded": False,
            "error": str(e),
        }
        return False
    except Exception as e:
        logger.error(f"Plugin {plugin_id} registration failed: {e}")
        return False


def load_plugin(name: str) -> Optional[Any]:
    if name in REGISTERED_PLUGINS and REGISTERED_PLUGINS[name].get("loaded"):
        return REGISTERED_PLUGINS[name]["module_ref"]

    if name in BUILTIN_PLUGINS:
        config = BUILTIN_PLUGINS[name]
        if register_plugin(name, config):
            return REGISTERED_PLUGINS[name]["module_ref"]

    try:
        module = importlib.import_module(name)
        REGISTERED_PLUGINS[name] = {
            "name": name,
            "module": name,
            "loaded": True,
            "module_ref": module,
            "category": "external",
            "status": "active",
        }
        return module
    except ImportError:
        logger.warning(f"Plugin '{name}' not available")
        return None


def list_plugins() -> List[Dict[str, Any]]:
    all_plugins = {}

    for pid, config in BUILTIN_PLUGINS.items():
        all_plugins[pid] = {
            "id": pid,
            "name": config["name"],
            "description": config["description"],
            "category": config["category"],
            "status": config["status"],
            "type": "builtin",
            "loaded": pid in REGISTERED_PLUGINS and REGISTERED_PLUGINS[pid].get("loaded", False),
        }

    for pid, config in REGISTERED_PLUGINS.items():
        if pid not in all_plugins:
            all_plugins[pid] = {
                "id": pid,
                "name": config.get("name", pid),
                "description": config.get("description", ""),
                "category": config.get("category", "custom"),
                "status": config.get("status", "unknown"),
                "type": "custom",
                "loaded": config.get("loaded", False),
            }

    return list(all_plugins.values())


def get_plugin_capabilities(plugin_id: str) -> Optional[Dict[str, Any]]:
    module = load_plugin(plugin_id)
    if module and hasattr(module, f"{plugin_id.upper()}_CAPABILITIES"):
        return getattr(module, f"{plugin_id.upper()}_CAPABILITIES")
    if module:
        caps_attr = [a for a in dir(module) if a.endswith("_CAPABILITIES")]
        if caps_attr:
            return getattr(module, caps_attr[0])
    return None


def initialize_builtin_plugins():
    for pid, config in BUILTIN_PLUGINS.items():
        register_plugin(pid, config)
    logger.info(f"Initialized {len(BUILTIN_PLUGINS)} builtin plugins")
