#!/usr/bin/env python3
"""
plugin_loader.py – Data Fusion Plugin System for Cathedral.
Uses exec() to load plugins – simpler and more reliable than importlib.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

PLUGIN_DIR = Path("plugins/")
PLUGIN_REGISTRY = {}

class OSINTPlugin:
    """Base class for OSINT plugins."""
    def __init__(self):
        self.name = "BasePlugin"
        self.description = "Base OSINT plugin"
        self.source = "unknown"
    
    def fetch(self):
        raise NotImplementedError("fetch() must be implemented")

def discover_plugins():
    """Load all plugins from plugins/ directory."""
    if not PLUGIN_DIR.exists():
        PLUGIN_DIR.mkdir(exist_ok=True)
        # Create example plugin
        example = PLUGIN_DIR / "example_plugin.py"
        example.write_text("""
from plugin_loader import OSINTPlugin

class ExamplePlugin(OSINTPlugin):
    def __init__(self):
        super().__init__()
        self.name = "Example Plugin"
        self.description = "A sample OSINT plugin"
        self.source = "example"
    
    def fetch(self):
        return {
            "source": self.source,
            "status": "success",
            "data": [{"title": "Example alert", "description": "This is a test feed"}]
        }
""")
        logging.info("Created example plugin.")

    # Load all .py files
    py_files = list(PLUGIN_DIR.glob("*.py"))
    logging.info(f"Found {len(py_files)} plugin files: {[f.name for f in py_files]}")

    for py_file in py_files:
        if py_file.name == "__init__.py":
            continue
        try:
            # Read the file content
            code = py_file.read_text()
            
            # Create a namespace for the plugin
            namespace = {
                '__name__': f'plugins.{py_file.stem}',
                '__file__': str(py_file),
                'OSINTPlugin': OSINTPlugin,
                'plugin_loader': sys.modules[__name__],
                'PLUGIN_REGISTRY': PLUGIN_REGISTRY,
            }
            
            # Execute the code
            exec(code, namespace)
            
            # Find and register plugin classes
            for name, obj in namespace.items():
                if (isinstance(obj, type) and 
                    issubclass(obj, OSINTPlugin) and 
                    obj is not OSINTPlugin):
                    instance = obj()
                    PLUGIN_REGISTRY[instance.name] = instance
                    logging.info(f"Loaded plugin: {instance.name}")
                    
        except Exception as e:
            logging.error(f"Failed to load {py_file.name}: {e}")
            import traceback
            traceback.print_exc()

def run_all_plugins() -> Dict[str, Dict]:
    """Run all loaded plugins."""
    results = {}
    for name, plugin in PLUGIN_REGISTRY.items():
        try:
            results[name] = plugin.fetch()
        except Exception as e:
            results[name] = {"source": name, "status": "error", "error": str(e)}
    return results

def list_plugins() -> List[Dict]:
    """List all loaded plugins."""
    return [{"name": p.name, "description": p.description, "source": p.source} 
            for p in PLUGIN_REGISTRY.values()]

if __name__ == "__main__":
    discover_plugins()
    print(f"\n✅ Loaded {len(PLUGIN_REGISTRY)} plugins:")
    for p in list_plugins():
        print(f"  - {p['name']}: {p['description']}")
