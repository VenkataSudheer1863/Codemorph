"""Analyzer Service.

Extracts API endpoints, DB calls, SQL queries, ORM mappings,
stored procedures, and message queue patterns from parsed results.
"""

import re
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def analyze_codebase(parse_results: list[dict], files: list[dict]) -> dict:
    """Analyze parsed results to extract APIs, DB schema, and integrations.

    Returns:
        dict with:
          - apis: list of detected API endpoints
          - tables: list of detected DB objects
          - stored_procedures: list of stored procedures
          - orm_entities: list of ORM entity mappings
          - message_queues: list of MQ producer/consumer patterns
          - soap_services: list of SOAP service endpoints
    """
    apis = []
    tables = []
    stored_procedures = []
    orm_entities = []
    message_queues = []
    soap_services = []

    seen_apis = set()
    seen_tables = set()

    for parse_result in parse_results:
        file_path = parse_result.get("path", "")

        # Collect API endpoints
        for ep in parse_result.get("endpoints", []):
            key = (ep["method"], ep["path"])
            if key not in seen_apis:
                seen_apis.add(key)
                # Try to find the handler class
                handler_class = ""
                for cls in parse_result.get("classes", []):
                    handler_class = cls["name"]
                    break

                apis.append({
                    "method": ep["method"],
                    "path": ep["path"],
                    "handler": handler_class or file_path,
                    "type": ep.get("type", "REST"),
                    "file": file_path,
                })

        # Collect DB tables from SQL and entity annotations
        for tbl in parse_result.get("tables", []):
            table_name = tbl["name"]
            if table_name.lower() not in seen_tables:
                seen_tables.add(table_name.lower())

                # Try to count columns from SQL content
                col_count = _count_columns_for_table(table_name, files, file_path)
                relationships = _find_relationships_for_table(table_name, parse_results)

                tables.append({
                    "name": table_name,
                    "type": tbl.get("type", "Table"),
                    "columns": col_count,
                    "relationships": len(relationships),
                    "relationship_details": relationships,
                    "file": tbl.get("file", file_path),
                })

                if tbl.get("type") == "Procedure":
                    stored_procedures.append({
                        "name": table_name,
                        "file": file_path,
                    })

        # Collect ORM entities
        for entity in parse_result.get("entities", []):
            orm_entities.append({
                "name": entity["name"],
                "file": entity.get("file", file_path),
                "table": _find_table_for_entity(entity["name"], parse_result),
            })

        # Detect SOAP services
        for fp in parse_result.get("framework_patterns", []):
            if fp.get("type") == "framework" and "SOAP" in fp.get("framework", ""):
                for cls in parse_result.get("classes", []):
                    soap_services.append({
                        "name": cls["name"],
                        "file": file_path,
                        "type": "SOAP",
                    })

        # Detect message queue patterns
        _detect_mq_patterns(parse_result, file_path, message_queues)

    return {
        "apis": apis,
        "tables": tables,
        "stored_procedures": stored_procedures,
        "orm_entities": orm_entities,
        "message_queues": message_queues,
        "soap_services": soap_services,
    }


def _count_columns_for_table(table_name: str, files: list[dict], current_file: str) -> int:
    """Estimate column count for a table from SQL content."""
    for f in files:
        content = f.get("content", "")
        if table_name.upper() in content.upper():
            # Try regex to count column definitions
            pattern = re.compile(
                rf"CREATE\s+TABLE\s+(?:\w+\.)?{re.escape(table_name)}\s*\((.*?)\)",
                re.IGNORECASE | re.DOTALL,
            )
            match = pattern.search(content)
            if match:
                body = match.group(1)
                # Count lines that look like column definitions
                columns = [
                    line.strip()
                    for line in body.split(",")
                    if line.strip() and not re.match(
                        r"^\s*(PRIMARY|FOREIGN|UNIQUE|INDEX|KEY|CONSTRAINT|CHECK)",
                        line.strip(),
                        re.IGNORECASE,
                    )
                ]
                return len(columns)
    return 0


def _find_relationships_for_table(table_name: str, parse_results: list[dict]) -> list[dict]:
    """Find foreign key relationships for a table."""
    relationships = []
    for pr in parse_results:
        for query in pr.get("sql_queries", []):
            if table_name.upper() in query.upper() and "JOIN" in query.upper():
                # Extract joined table
                join_match = re.search(
                    rf"JOIN\s+(?:\w+\.)?(\w+)\s+", query, re.IGNORECASE
                )
                if join_match:
                    relationships.append({
                        "type": "JOIN",
                        "target": join_match.group(1),
                    })
    return relationships


def _find_table_for_entity(entity_name: str, parse_result: dict) -> str:
    """Find the table name associated with an ORM entity."""
    for tbl in parse_result.get("tables", []):
        if tbl.get("type") == "Entity":
            return tbl["name"]
    return entity_name.lower() + "s"


def _detect_mq_patterns(parse_result: dict, file_path: str, message_queues: list):
    """Detect message queue producer/consumer patterns."""
    mq_indicators = {
        "IBM MQ": [
            "com.ibm.mq", "MQQueueManager", "MQQueue", "JMSContext",
            "jms.Queue", "ConnectionFactory",
        ],
        "Kafka": [
            "KafkaProducer", "KafkaConsumer", "KafkaTemplate",
            "@KafkaListener", "kafka-clients", "confluent_kafka",
        ],
        "RabbitMQ": [
            "RabbitTemplate", "@RabbitListener", "pika",
            "amqp", "RabbitMQ",
        ],
        "ActiveMQ": [
            "ActiveMQConnectionFactory", "activemq",
        ],
    }

    imports_str = " ".join(parse_result.get("imports", []))
    annotations = parse_result.get("annotations", [])
    framework_patterns = parse_result.get("framework_patterns", [])

    for mq_type, indicators in mq_indicators.items():
        for indicator in indicators:
            if indicator in imports_str or indicator in " ".join(annotations):
                role = "consumer" if "Listener" in indicator or "Consumer" in indicator else "producer"
                message_queues.append({
                    "type": mq_type,
                    "role": role,
                    "indicator": indicator,
                    "file": file_path,
                })
                break
