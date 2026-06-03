"""
Bulk label assignment for Apache Atlas columns based on domain mapping rules.
Processes all columns in a schema and assigns labels based on table prefix patterns.

Usage:
    python scripts/assign_labels.py --schema MY_SCHEMA --database MY_DB
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.atlas_client import AtlasClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_domain_mapping(config_path: str = "config/domain_mapping.json") -> dict:
    with open(config_path) as f:
        return json.load(f)


def get_domain_for_table(table_name: str, mapping: dict) -> dict:
    """Determine domain and labels for a table based on prefix rules."""
    for rule in mapping["domain_rules"]:
        if table_name.upper().startswith(rule["table_prefix"]):
            return {
                "domain": rule["domain"],
                "labels": rule["labels"],
                "source_system": rule.get("source_system", "Unknown"),
            }
    return {
        "domain": mapping.get("default_domain", "General"),
        "labels": mapping.get("default_labels", ["Uncategorized"]),
        "source_system": "Unknown",
    }


def assign_labels_for_schema(client: AtlasClient, schema: str, database: str, mapping: dict):
    """Process all tables in a schema and assign labels to their columns."""
    tables = client.search_entities(query=f"*", type_name="rdbms_table")
    schema_tables = [t for t in tables if schema.lower() in t.get("attributes", {}).get("qualifiedName", "").lower()]

    logger.info("Found %d tables in schema %s", len(schema_tables), schema)

    stats = {"tables": 0, "columns": 0, "labels_assigned": 0, "errors": 0}

    for table in schema_tables:
        table_name = table["attributes"]["name"]
        table_guid = table["guid"]
        domain_info = get_domain_for_table(table_name, mapping)

        logger.info("Processing table: %s (domain: %s)", table_name, domain_info["domain"])

        for label in domain_info["labels"]:
            if client.assign_label(table_guid, label):
                stats["labels_assigned"] += 1
            else:
                stats["errors"] += 1

        columns = client.get_entity_columns(table["attributes"]["qualifiedName"])
        for col in columns:
            col_guid = col.get("guid")
            if not col_guid:
                continue

            for label in domain_info["labels"]:
                if client.assign_label(col_guid, label):
                    stats["labels_assigned"] += 1
                else:
                    stats["errors"] += 1
            stats["columns"] += 1

        stats["tables"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Assign labels to Atlas entities")
    parser.add_argument("--schema", required=True, help="Database schema name")
    parser.add_argument("--database", required=True, help="Database name")
    parser.add_argument("--config", default="config/domain_mapping.json", help="Domain mapping config file")
    parser.add_argument("--env", default="config/atlas_config.env", help="Environment file")
    args = parser.parse_args()

    load_dotenv(args.env)
    client = AtlasClient.from_env()
    mapping = load_domain_mapping(args.config)

    logger.info("Starting label assignment for %s.%s", args.database, args.schema)
    stats = assign_labels_for_schema(client, args.schema, args.database, mapping)

    logger.info("=== Results ===")
    logger.info("Tables processed: %d", stats["tables"])
    logger.info("Columns processed: %d", stats["columns"])
    logger.info("Labels assigned: %d", stats["labels_assigned"])
    logger.info("Errors: %d", stats["errors"])


if __name__ == "__main__":
    main()
