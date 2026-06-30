"""Context Builder Service.

Builds a code graph connecting services, modules, APIs, database tables.
Identifies architecture layers and maps inter-service dependencies.
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

LAYER_KEYWORDS = {
    "frontend": {
        "frameworks": ["React", "Angular", "Vue", "JSF", "JSP"],
        "extensions": [".html", ".htm", ".css", ".scss", ".jsx", ".tsx", ".xhtml", ".jsp"],
        "paths": ["frontend", "client", "web", "ui", "webapp", "static", "public", "views", "templates"],
    },
    "backend": {
        "frameworks": [
            "Spring Boot", "Spring MVC", "Java EE / EJB", "Django",
            "Flask", "FastAPI", "Express", "ASP.NET",
        ],
        "extensions": [".java", ".py", ".cs", ".go", ".rs"],
        "paths": [
            "backend", "server", "api", "service", "controller",
            "handler", "resource", "ejb", "src/main/java",
        ],
    },
    "database": {
        "frameworks": ["Hibernate", "JPA / OpenJPA"],
        "extensions": [".sql", ".ddl", ".plsql"],
        "paths": ["database", "db", "migration", "schema", "repository", "dao", "model", "entity"],
    },
    "integration": {
        "frameworks": ["SOAP / JAX-WS"],
        "extensions": [],
        "paths": ["integration", "connector", "adapter", "client", "gateway", "messaging", "queue", "mq"],
    },
    "deployment": {
        "frameworks": [],
        "extensions": [".yaml", ".yml"],
        "paths": ["deploy", "deployment", "infra", "infrastructure", "k8s", "kubernetes", "docker", "helm", "terraform"],
    },
}


def build_context(parse_results: list[dict], files: list[dict]) -> dict:
    """Build a code context/graph from parse results.

    Returns:
        dict with:
          - layers: architecture layer breakdown
          - components: list of identified components
          - dependencies: inter-module dependency graph
          - service_map: service-to-file mapping
    """
    layers = {layer: {"files": [], "components": [], "frameworks": set()} for layer in LAYER_KEYWORDS}
    components = []
    dependencies = defaultdict(set)
    service_map = defaultdict(list)

    # Classify files into layers
    for file_info, parse_result in zip(files, parse_results):
        path = file_info.get("path", "").lower()
        ext = file_info.get("extension", "")
        language = file_info.get("language", "")

        assigned_layer = _classify_layer(path, ext, parse_result)
        layers[assigned_layer]["files"].append(file_info["path"])

        # Extract components
        for cls in parse_result.get("classes", []):
            component = {
                "name": cls["name"],
                "type": cls.get("type", "class"),
                "file": file_info["path"],
                "layer": assigned_layer,
                "language": language,
            }
            components.append(component)
            layers[assigned_layer]["components"].append(cls["name"])
            service_map[cls["name"]].append(file_info["path"])

        # Track framework associations
        for fp in parse_result.get("framework_patterns", []):
            fw = fp.get("framework", fp.get("type", ""))
            if fw:
                layers[assigned_layer]["frameworks"].add(fw)

        # Build dependency graph from imports
        for imp in parse_result.get("imports", []):
            for cls in parse_result.get("classes", []):
                dependencies[cls["name"]].add(imp)

    # Convert sets to lists for JSON serialization
    for layer in layers:
        layers[layer]["frameworks"] = list(layers[layer]["frameworks"])
        layers[layer]["file_count"] = len(layers[layer]["files"])

    dependency_graph = {k: list(v) for k, v in dependencies.items()}

    # Generate project summary
    summary = _generate_project_summary(layers, components, files, parse_results)

    return {
        "layers": layers,
        "components": components,
        "dependencies": dependency_graph,
        "service_map": dict(service_map),
        "total_components": len(components),
        "project_summary": summary,
    }


def _generate_project_summary(layers: dict, components: list, files: list, parse_results: list) -> str:
    """Generate a comprehensive business-focused project summary."""
    from .business_analyzer import BusinessAnalyzer
    
    # Use the business analyzer to get detailed business insights
    business_analyzer = BusinessAnalyzer()
    business_analysis = business_analyzer.analyze_business_rules(files, parse_results)
    
    # Return the business-focused summary
    return business_analysis.get('business_summary', 'Business analysis could not be completed.')


def _analyze_business_domain(files: list, components: list, parse_results: list) -> dict:
    """Analyze business domain from code artifacts."""
    # Common business domain keywords
    domain_keywords = {
        'ecommerce': ['order', 'product', 'cart', 'payment', 'checkout', 'inventory', 'customer', 'shop'],
        'finance': ['account', 'transaction', 'payment', 'invoice', 'billing', 'finance', 'money', 'bank'],
        'healthcare': ['patient', 'doctor', 'medical', 'health', 'appointment', 'diagnosis', 'treatment'],
        'education': ['student', 'course', 'grade', 'teacher', 'class', 'assignment', 'exam', 'school'],
        'hr': ['employee', 'payroll', 'attendance', 'leave', 'performance', 'recruitment', 'staff'],
        'crm': ['customer', 'lead', 'contact', 'opportunity', 'sales', 'marketing', 'campaign'],
        'inventory': ['warehouse', 'stock', 'item', 'supplier', 'purchase', 'inventory', 'asset'],
        'content': ['article', 'blog', 'post', 'content', 'media', 'publish', 'cms', 'news'],
        'social': ['user', 'profile', 'friend', 'message', 'post', 'comment', 'social', 'feed'],
        'booking': ['reservation', 'booking', 'schedule', 'appointment', 'calendar', 'availability']
    }
    
    # Analyze file names and component names
    all_text = []
    for file_info in files:
        all_text.append(file_info.get("path", "").lower())
    for component in components:
        all_text.append(component.get("name", "").lower())
    
    combined_text = " ".join(all_text)
    
    domain_scores = {}
    for domain, keywords in domain_keywords.items():
        score = sum(1 for keyword in keywords if keyword in combined_text)
        if score > 0:
            domain_scores[domain] = score
    
    primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0] if domain_scores else 'general'
    
    return {
        'primary_domain': primary_domain,
        'domain_scores': domain_scores,
        'confidence': max(domain_scores.values()) if domain_scores else 0
    }


def _analyze_database_operations(parse_results: list) -> dict:
    """Analyze database operation complexity."""
    total_tables = sum(len(pr.get("tables", [])) for pr in parse_results)
    total_relationships = 0
    operation_types = set()
    
    for pr in parse_results:
        for table in pr.get("tables", []):
            if isinstance(table, dict):
                total_relationships += len(table.get("foreign_keys", []))
        
        # Analyze SQL operations if present
        for query in pr.get("sql_queries", []):
            if isinstance(query, dict):
                operation_types.add(query.get("type", "SELECT"))
    
    complexity = "complex" if total_relationships > 10 else "moderate" if total_relationships > 3 else "simple"
    operations = ", ".join(sorted(operation_types)) if operation_types else "CRUD operations"
    
    return {
        'complexity': complexity,
        'operations': operations,
        'relationship_count': total_relationships
    }


def _calculate_complexity_score(files: int, components: int, apis: int, tables: int, has_integration: bool) -> int:
    """Calculate overall system complexity score (0-100)."""
    score = 0
    score += min(files * 0.5, 25)  # File count contribution (max 25)
    score += min(components * 0.8, 25)  # Component count contribution (max 25)
    score += min(apis * 2, 20)  # API count contribution (max 20)
    score += min(tables * 1.5, 15)  # Table count contribution (max 15)
    score += 15 if has_integration else 0  # Integration complexity (max 15)
    
    return int(score)


def _identify_business_functions(business_indicators: dict, apis: int, tables: int, components: list) -> dict:
    """Identify business functions based on analysis."""
    domain = business_indicators['primary_domain']
    
    # Domain-specific descriptions
    domain_descriptions = {
        'ecommerce': {
            'primary_purpose': 'an e-commerce platform facilitating online retail operations',
            'core_capabilities': 'manage product catalogs, process customer orders, handle payments, and track inventory',
            'user_interactions': 'customer shopping experiences, merchant management, and administrative oversight',
            'ui_description': 'customer-facing shopping interfaces and administrative dashboards',
            'backend_description': 'order processing, payment handling, inventory management, and customer service logic',
            'data_description': 'product catalogs, customer profiles, order histories, and transaction records',
            'integration_description': 'payment gateways, shipping providers, and third-party marketplace integrations',
            'api_purpose': 'mobile app integration, partner system connectivity, and microservice communication',
            'data_operations': 'customer relationship management, order fulfillment, and business analytics',
            'value_proposition': 'streamlined online commerce operations and enhanced customer shopping experiences',
            'market_position': 'a comprehensive e-commerce solution for digital retail transformation',
            'business_processes': 'end-to-end retail operations from product discovery to order fulfillment'
        },
        'finance': {
            'primary_purpose': 'a financial management system supporting monetary transactions and accounting operations',
            'core_capabilities': 'process financial transactions, manage accounts, generate reports, and ensure compliance',
            'user_interactions': 'financial data entry, transaction monitoring, and regulatory reporting',
            'ui_description': 'financial dashboards, transaction interfaces, and reporting tools',
            'backend_description': 'transaction processing, account management, compliance checking, and financial calculations',
            'data_description': 'account balances, transaction histories, financial statements, and audit trails',
            'integration_description': 'banking systems, payment processors, and regulatory reporting platforms',
            'api_purpose': 'financial data exchange, third-party integrations, and mobile banking services',
            'data_operations': 'financial record keeping, transaction reconciliation, and regulatory compliance',
            'value_proposition': 'accurate financial management and streamlined monetary operations',
            'market_position': 'a robust financial platform for enterprise money management',
            'business_processes': 'comprehensive financial workflows from transaction capture to financial reporting'
        },
        'general': {
            'primary_purpose': 'a business application supporting organizational operations and data management',
            'core_capabilities': 'manage business data, automate workflows, and provide user interfaces',
            'user_interactions': 'data entry, information retrieval, and business process execution',
            'ui_description': 'user interfaces for data interaction and business process management',
            'backend_description': 'business logic implementation, data processing, and workflow automation',
            'data_description': 'business entities, operational data, and system configurations',
            'integration_description': 'external system connectivity and data exchange protocols',
            'api_purpose': 'system integration, data access, and service-to-service communication',
            'data_operations': 'business data management, process automation, and information analysis',
            'value_proposition': 'improved operational efficiency and streamlined business processes',
            'market_position': 'a versatile business application for organizational productivity',
            'business_processes': 'core business operations and data-driven decision making'
        }
    }
    
    return domain_descriptions.get(domain, domain_descriptions['general'])


def _classify_layer(path: str, ext: str, parse_result: dict) -> str:
    """Classify a file into an architecture layer."""
    path_lower = path.lower().replace("\\", "/")

    # Check path-based classification first
    for layer, config in LAYER_KEYWORDS.items():
        for keyword in config["paths"]:
            if keyword in path_lower.split("/"):
                return layer

    # Check extension-based classification
    for layer, config in LAYER_KEYWORDS.items():
        if ext in config["extensions"]:
            return layer

    # Check framework-based classification
    detected_frameworks = {
        fp.get("framework", "") for fp in parse_result.get("framework_patterns", [])
    }
    for layer, config in LAYER_KEYWORDS.items():
        for fw in config["frameworks"]:
            if fw in detected_frameworks:
                return layer

    # Default to backend
    return "backend"
