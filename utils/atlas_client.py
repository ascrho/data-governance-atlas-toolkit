"""
Apache Atlas REST API client for metadata management operations.
Supports label assignment, business metadata, foreign key creation,
and PII classification at scale.
"""

import json
import logging
import os
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class AtlasClient:
    """Wrapper around Apache Atlas REST API v2."""

    def __init__(self, host: str, port: int, username: str, password: str):
        self.base_url = f"http://{host}:{port}/api/atlas/v2"
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({"Content-Type": "application/json"})

    @classmethod
    def from_env(cls) -> "AtlasClient":
        """Create client from environment variables."""
        return cls(
            host=os.environ["ATLAS_HOST"],
            port=int(os.environ.get("ATLAS_PORT", "21000")),
            username=os.environ["ATLAS_USER"],
            password=os.environ["ATLAS_PASSWORD"],
        )

    def get_entity_by_name(self, qualified_name: str, type_name: str = "rdbms_column") -> dict | None:
        """Look up an entity by its qualifiedName."""
        params = {
            "attr:qualifiedName": qualified_name,
            "typeName": type_name,
        }
        resp = self.session.get(f"{self.base_url}/entity/uniqueAttribute/type/{type_name}", params=params)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def get_entity_columns(self, table_qualified_name: str) -> list[dict]:
        """Get all columns for a table entity."""
        entity = self.get_entity_by_name(table_qualified_name, type_name="rdbms_table")
        if not entity:
            logger.warning("Table not found: %s", table_qualified_name)
            return []

        columns = entity.get("entity", {}).get("relationshipAttributes", {}).get("columns", [])
        return columns

    def assign_label(self, entity_guid: str, label: str) -> bool:
        """Assign a label (tag) to an entity."""
        url = f"{self.base_url}/entity/guid/{entity_guid}/labels"
        resp = self.session.put(url, json=[label])
        if resp.status_code in (200, 204):
            logger.info("Label '%s' assigned to %s", label, entity_guid)
            return True
        logger.error("Failed to assign label: %s", resp.text)
        return False

    def set_business_metadata(self, entity_guid: str, bm_name: str, metadata: dict[str, Any]) -> bool:
        """Assign business metadata attributes to an entity."""
        url = f"{self.base_url}/entity/guid/{entity_guid}/businessmetadata/{bm_name}"
        resp = self.session.put(url, json=metadata)
        if resp.status_code in (200, 204):
            logger.info("Business metadata '%s' set on %s", bm_name, entity_guid)
            return True
        logger.error("Failed to set business metadata: %s", resp.text)
        return False

    def create_relationship(self, from_guid: str, to_guid: str, relationship_type: str = "atlas_foreign_key") -> bool:
        """Create a relationship (e.g., foreign key) between two entities."""
        payload = {
            "typeName": relationship_type,
            "end1": {"guid": from_guid, "typeName": "rdbms_column"},
            "end2": {"guid": to_guid, "typeName": "rdbms_column"},
        }
        resp = self.session.post(f"{self.base_url}/relationship", json=payload)
        if resp.status_code in (200, 201):
            logger.info("Relationship created: %s -> %s", from_guid, to_guid)
            return True
        if resp.status_code == 409:
            logger.info("Relationship already exists: %s -> %s", from_guid, to_guid)
            return True
        logger.error("Failed to create relationship: %s", resp.text)
        return False

    def search_entities(self, query: str, type_name: str = "rdbms_table", limit: int = 100) -> list[dict]:
        """Search for entities using Atlas DSL."""
        payload = {
            "typeName": type_name,
            "query": query,
            "limit": limit,
            "offset": 0,
        }
        resp = self.session.post(f"{self.base_url}/search/basic", json=payload)
        resp.raise_for_status()
        return resp.json().get("entities", [])
