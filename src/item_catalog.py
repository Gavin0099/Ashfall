import json
from pathlib import Path
from typing import Dict, Any, Optional
from .state_models import EquipmentState, EquipmentSlot

ROOT = Path(__file__).resolve().parents[1]

class ItemCatalog:
    _instance = None
    _items: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ItemCatalog, cls).__new__(cls)
            cls._instance._load_catalog()
        return cls._instance

    def _load_catalog(self):
        catalog_path = ROOT / "data" / "item_catalog.json"
        if catalog_path.exists():
            with open(catalog_path, "r", encoding="utf-8") as f:
                self._items = json.load(f)
        else:
            self._items = {}

    def get_template(self, item_id: str) -> Optional[Dict[str, Any]]:
        return self._items.get(item_id)

    def create_instance(self, item_id: str, affixes: Optional[Dict[str, int]] = None) -> Optional[EquipmentState]:
        template = self.get_template(item_id)
        if not template:
            return None
        
        return EquipmentState(
            id=item_id,
            slot=template["slot"],
            requirements=template.get("requirements", {}),
            scaling=template.get("scaling", {}),
            affixes=affixes or {},
            tags=template.get("tags", [])
        )

    def list_all_ids(self) -> list[str]:
        return list(self._items.keys())

# Global instance
catalog = ItemCatalog()
