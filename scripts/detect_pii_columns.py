"""
Automatic PII detection and classification for Apache Atlas columns.
Scans column names against configurable patterns and assigns PII classifications.

Usage:
    python scripts/detect_pii_columns.py --schema MY_SCHEMA
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


def load_pii_patterns(config_path: str = "config/domain_mapping.json") -> list[str]:
    with open(config_path) as f:
        config = json.load(f)
    return config.get("pii_column_patterns", [])


def is_pii_column(column_name: str, patterns: list[str]) -> bool:
    """Check if a column name matches any PII pattern."""
    name_lower = column_name.lower()
    return any(re.search(pattern, name_lower) for pattern in patterns)


def classify_pii_columns(client: AtlasClient, schema: str, patterns: list[str]) -> dict:
    """Scan all columns in a schema and classify PII columns."""
    tables = client.search_entities(query="*", type_name="rdbms_table")
    schema_tables = [t for t in tables if schema.lower() in t.get("attributes", {}).get("qualifiedName", "").lower()]

    stats = {"total_columns": 0, "pii_detected": 0, "classified": 0, "errors": 0}
    pii_report = []

    for table in schema_tables:
        table_name = table["attributes"]["name"]
        columns = client.get_entity_columns(table["attributes"]["qualifiedName"])

        for col in columns:
            col_name = col.get("displayText", col.get("attributes", {}).get("name", ""))
            col_guid = col.get("guid")
            stats["total_columns"] += 1

            if is_pii_column(col_name, patterns):
                stats["pii_detected"] += 1
                pii_report.append({"table": table_name, "column": col_name, "guid": col_guid})

                if col_guid and client.assign_label(col_guid, "PII"):
                    stats["classified"] += 1
                else:
                    stats["errors"] += 1

                logger.info("PII detected: %s.%s", table_name, col_name)

    return {"stats": stats, "report": pii_report}


def main():
    parser = argparse.ArgumentParser(description="Detect and classify PII columns in Atlas")
    parser.add_argument("--schema", required=True, help="Database schema name")
    parser.add_argument("--config", default="config/domain_mapping.json")
    parser.add_argument("--env", default="config/atlas_config.env")
    parser.add_argument("--report", action="store_true", help="Output detailed PII report")
    args = parser.parse_args()

    load_dotenv(args.env)
    client = AtlasClient.from_env()
    patterns = load_pii_patterns(args.config)

    logger.info("Starting PII detection for schema: %s", args.schema)
    logger.info("Using %d PII patterns", len(patterns))

    result = classify_pii_columns(client, args.schema, patterns)

    logger.info("=== PII Detection Results ===")
    logger.info("Total columns scanned: %d", result["stats"]["total_columns"])
    logger.info("PII columns detected: %d", result["stats"]["pii_detected"])
    logger.info("Successfully classified: %d", result["stats"]["classified"])
    logger.info("Errors: %d", result["stats"]["errors"])

    if args.report:
        print("\n--- PII Report ---")
        for item in result["report"]:
            print(f"  {item['table']}.{item['column']}")


if __name__ == "__main__":
    main()
