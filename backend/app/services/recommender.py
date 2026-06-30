"""Recommender Service.

Generates modern stack suggestions based on detected legacy technologies.
"""

import logging

logger = logging.getLogger(__name__)

# Modernization recommendations mapping
RECOMMENDATIONS = {
    "frontend_framework": {
        "JSF": ["React", "Angular", "Next.js", "Vue.js"],
        "JSP": ["React", "Angular", "Next.js", "Vue.js"],
        "Thymeleaf": ["React", "Next.js", "Vue.js"],
        "React": ["Next.js", "Remix"],
        "Angular": ["React", "Next.js"],
        "Vue.js": ["Nuxt.js", "React"],
    },
    "backend_framework": {
        "Java EE / EJB": ["Spring Boot", "Micronaut", "Quarkus"],
        "Spring MVC": ["Spring Boot", "Micronaut", "Quarkus"],
        "Spring Boot": ["Spring Boot 3.x", "Micronaut", "Quarkus"],
        "Django": ["FastAPI", "Django 5.x"],
        "Flask": ["FastAPI", "Litestar"],
        "Express.js": ["NestJS", "Fastify", "Hono"],
        "ASP.NET Core": ["ASP.NET Core 8", "Minimal APIs"],
    },
    "runtime": {
        "Java 8": ["Java 21", "Java 17", "Kotlin"],
        "Java 11": ["Java 21", "Java 17", "Kotlin"],
        "Java 17": ["Java 21", "Kotlin"],
        "Python 3": ["Python 3.12"],
        "Node.js": ["Node.js 20 LTS", "Bun", "Deno"],
        ".NET 6+": [".NET 8", ".NET 9"],
    },
    "app_server": {
        "WebSphere": ["Kubernetes + Docker", "OpenShift", "Embedded Tomcat"],
        "WebLogic": ["Kubernetes + Docker", "OpenShift", "Embedded Tomcat"],
        "JBoss / WildFly": ["Kubernetes + Docker", "Embedded Tomcat", "Quarkus Native"],
        "Tomcat": ["Kubernetes + Docker", "Embedded Tomcat", "Cloud Run"],
        "Embedded (Spring Boot)": ["Kubernetes + Docker", "Cloud Run", "AWS Lambda"],
    },
    "database": {
        "DB2": ["PostgreSQL", "MySQL", "Amazon Aurora"],
        "Oracle": ["PostgreSQL", "MySQL", "Amazon Aurora"],
        "SQL Server": ["PostgreSQL", "MySQL"],
        "MySQL": ["PostgreSQL", "PlanetScale"],
        "PostgreSQL": ["CockroachDB", "Supabase"],
        "SQLite": ["PostgreSQL", "MySQL"],
    },
    "messaging": {
        "IBM MQ": ["Apache Kafka", "RabbitMQ", "Amazon SQS"],
        "ActiveMQ": ["Apache Kafka", "RabbitMQ", "Amazon SQS"],
        "Kafka": ["Apache Kafka (managed)", "Amazon MSK"],
        "RabbitMQ": ["Apache Kafka", "Amazon SQS"],
    },
    "build_tool": {
        "Maven": ["Gradle", "Maven 4"],
        "Gradle": ["Gradle (latest)"],
        "npm": ["pnpm", "Bun"],
        "pip": ["Poetry", "uv", "PDM"],
        "dotnet CLI": ["dotnet CLI (latest)"],
    },
    "orm": {
        "OpenJPA": ["Spring Data JPA", "Hibernate 6", "jOOQ"],
        "Hibernate": ["Spring Data JPA", "Hibernate 6", "jOOQ"],
        "EclipseLink": ["Spring Data JPA", "Hibernate 6", "jOOQ"],
        "Spring Data JPA": ["Spring Data JPA (latest)", "jOOQ"],
        "SQLAlchemy": ["SQLAlchemy 2.0", "SQLModel", "Tortoise ORM"],
        "Django ORM": ["Django ORM (latest)", "SQLAlchemy"],
    },
}


def generate_recommendations(detected_stack: list[dict]) -> list[dict]:
    """Generate modernization recommendations for each detected technology.

    Returns list of recommendation dicts:
      - category: str
      - label: str
      - detected: str
      - confidence: int
      - suggestions: list[str]
    """
    recommendations = []

    for item in detected_stack:
        category = item["category"]
        detected = item["detected"]

        suggestions = RECOMMENDATIONS.get(category, {}).get(detected, [])

        if not suggestions:
            # Provide generic suggestions
            suggestions = [f"{detected} (latest version)"]

        recommendations.append({
            "category": category,
            "label": item["label"],
            "detected": detected,
            "confidence": item["confidence"],
            "suggestions": suggestions,
        })

    return recommendations
