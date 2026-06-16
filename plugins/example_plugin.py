"""
example_plugin.py – A simple OSINT plugin for Cathedral.
Just drop .py files in the plugins/ folder and they auto-load.
"""

from plugin_loader import OSINTPlugin

class ExamplePlugin(OSINTPlugin):
    def __init__(self):
        super().__init__()
        self.name = "Example Plugin"
        self.description = "A sample OSINT plugin – replace with your own source"
        self.source = "example"
    
    def fetch(self):
        return {
            "source": self.source,
            "status": "success",
            "data": [
                {"title": "Example alert", "description": "This is a test feed"}
            ]
        }
