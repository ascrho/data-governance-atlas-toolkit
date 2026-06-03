# Data Governance Atlas Toolkit

> Automated metadata management framework for Apache Atlas — labels, classifications, foreign keys, and business metadata at scale.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Apache Atlas](https://img.shields.io/badge/Apache_Atlas-2.x-D22128?style=flat-square&logo=apache&logoColor=white)](https://atlas.apache.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## Problem

Managing metadata for hundreds of database tables and thousands of columns in Apache Atlas manually is:

- **Time-consuming** — each column requires individual API calls for labels, classifications, and business metadata
- **Error-prone** — manual assignment leads to inconsistencies
- **Not scalable** — enterprise databases grow faster than manual processes can keep up

## Solution

This toolkit automates the entire metadata lifecycle in Apache Atlas:

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Database       │     │  Atlas Toolkit       │     │  Apache Atlas   │
│  Schema         │────▶│                      │────▶│  Catalog        │
│  (Oracle/PG)    │     │  - Column discovery  │     │                 │
└─────────────────┘     │  - Label assignment  │     │  - Labels       │
                        │  - FK creation       │     │  - Classifications│
                        │  - PII detection     │     │  - FK Relations  │
                        │  - Business metadata │     │  - Business Meta │
                        └──────────────────────┘     └─────────────────┘
```

## Features

- **Bulk metadata assignment** — Process 5,000+ columns in a single run
- **Automatic PII detection** — Classify columns containing personal data based on naming patterns
- **Foreign key creation** — Define relationships between entities from a declarative config
- **Business metadata** — Assign domain, source system, and data steward information
- **Label management** — Categorize columns by business domain (e.g., "Customer", "Transaction", "Regulatory")
- **Idempotent operations** — Safe to re-run; existing metadata is preserved
- **SSH tunnel support** — Connect to Atlas instances behind firewalls

## Architecture

```
atlas_toolkit/
├── config/
│   ├── atlas_config.env.example    # Connection settings
│   ├── domain_mapping.json         # Column-to-domain mapping rules
│   └── fk_definitions.json         # Foreign key relationship config
├── scripts/
│   ├── assign_labels.py            # Bulk label assignment
│   ├── assign_business_metadata.py # Business metadata assignment
│   ├── create_foreign_keys.py      # FK relationship creation
│   ├── detect_pii_columns.py       # PII classification
│   └── verify_metadata.py          # Verification and reporting
├── utils/
│   ├── atlas_client.py             # Atlas REST API wrapper
│   └── ssh_tunnel.py               # SSH tunnel management
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Configure

```bash
cp config/atlas_config.env.example config/atlas_config.env
# Edit with your Atlas credentials
```

```env
# config/atlas_config.env.example
ATLAS_HOST=your-atlas-host
ATLAS_PORT=21000
ATLAS_USER=admin
ATLAS_PASSWORD=changeme
SSH_HOST=your-ssh-host          # Optional: if Atlas is behind firewall
SSH_USER=your-ssh-user
SSH_KEY_PATH=~/.ssh/id_rsa
```

### 2. Define Domain Mapping

```json
{
  "domain_rules": [
    {
      "pattern": "^(customer|client|person|affiliate)_",
      "domain": "Customer",
      "pii_candidate": true
    },
    {
      "pattern": "^(balance|amount|total)_",
      "domain": "Financial",
      "pii_candidate": false
    },
    {
      "pattern": "^(trx|transaction|movement)_",
      "domain": "Transactions",
      "pii_candidate": false
    }
  ]
}
```

### 3. Run

```bash
# Assign labels to all columns in a schema
python scripts/assign_labels.py --schema MY_SCHEMA --database MY_DB

# Detect and classify PII columns
python scripts/detect_pii_columns.py --schema MY_SCHEMA

# Create foreign key relationships
python scripts/create_foreign_keys.py --config config/fk_definitions.json

# Verify all metadata assignments
python scripts/verify_metadata.py --schema MY_SCHEMA --report
```

## Domain Mapping Logic

The toolkit assigns labels based on configurable table prefix patterns:

| Table Prefix | Domain | Example Tables |
|:-------------|:-------|:---------------|
| `CUSTOMER_*` | Customer Management | `CUSTOMER_ACCOUNTS`, `CUSTOMER_CONTACTS` |
| `TRX_*` | Transactions | `TRX_DEPOSITS`, `TRX_WITHDRAWALS` |
| `BALANCE_*` | Financial | `BALANCE_DAILY`, `BALANCE_MONTHLY` |
| `REG_*` | Regulatory | `REG_REPORTS`, `REG_COMPLIANCE` |
| `PROC_*` | Operations | `PROC_CLAIMS`, `PROC_REQUESTS` |

## PII Detection Rules

Columns are classified as PII based on name patterns:

```python
PII_PATTERNS = [
    r"(first|last|full)_?name",
    r"(email|correo)",
    r"(phone|telefono|celular)",
    r"(address|direccion|domicilio)",
    r"(rut|dni|ssn|passport|cedula)",
    r"(birth|nacimiento)_?date",
    r"(salary|sueldo|remuneracion)",
]
```

## API Reference

### Atlas Client

```python
from utils.atlas_client import AtlasClient

client = AtlasClient(
    host="atlas-server",
    port=21000,
    username="admin",
    password="changeme"
)

# Get all columns for a table
columns = client.get_entity_columns("MY_SCHEMA.MY_TABLE")

# Assign a label
client.assign_label(entity_guid="abc-123", label="Customer")

# Create a foreign key
client.create_relationship(
    from_entity="ORDERS.CUSTOMER_ID",
    to_entity="CUSTOMERS.ID",
    relationship_type="foreign_key"
)

# Assign business metadata
client.set_business_metadata(
    entity_guid="abc-123",
    metadata={
        "domain": "Customer",
        "data_steward": "Data Governance Team",
        "source_system": "Core Banking",
        "update_frequency": "Daily"
    }
)
```

## Results

In production use, this toolkit processed:

- **5,500+ columns** across **80+ tables**
- **3 business metadata types** assigned to all entities
- **200+ foreign key relationships** created
- **150+ PII columns** automatically detected and classified
- **Processing time:** ~15 minutes for full schema

## Technologies

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Atlas API | REST API v2 |
| SSH | Paramiko |
| HTTP | requests |
| Config | python-dotenv, JSON |

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

**Marcos Quintero** — Data Engineer  
[GitHub](https://github.com/ascrho) | [LinkedIn](https://www.linkedin.com/in/marcos-quintero)
