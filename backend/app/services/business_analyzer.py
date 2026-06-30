#!/usr/bin/env python3
"""
Business Rules Analyzer - Extracts business logic and rules from codebase.
"""

import re
import json
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class BusinessRule:
    """Represents a business rule found in the code."""
    rule_type: str
    description: str
    location: str
    confidence: float
    code_snippet: str
    impact: str

@dataclass
class BusinessProcess:
    """Represents a business process identified in the code."""
    name: str
    description: str
    steps: List[str]
    entities_involved: List[str]
    business_value: str
    complexity: str

class BusinessAnalyzer:
    """Analyzes codebase to extract business rules and processes."""
    
    def __init__(self):
        self.business_patterns = {
            'validation_rules': [
                r'if\s+.*\s*(validate|check|verify|ensure)',
                r'(required|mandatory|must|should).*field',
                r'(min|max|length|range).*validation',
                r'email.*valid|phone.*valid|format.*check'
            ],
            'business_logic': [
                r'calculate.*\((.*?)\)',
                r'process.*\((.*?)\)',
                r'generate.*\((.*?)\)',
                r'approve.*\((.*?)\)',
                r'reject.*\((.*?)\)',
                r'workflow.*\((.*?)\)'
            ],
            'authorization_rules': [
                r'(admin|manager|user).*permission',
                r'role.*check|access.*control',
                r'authorize|authenticate|login',
                r'permission.*required|access.*denied'
            ],
            'data_rules': [
                r'foreign.*key|primary.*key',
                r'unique.*constraint|not.*null',
                r'cascade.*delete|on.*update',
                r'index.*on|constraint.*check'
            ],
            'workflow_rules': [
                r'status.*change|state.*transition',
                r'approve.*workflow|reject.*workflow',
                r'next.*step|previous.*step',
                r'complete.*process|start.*process'
            ]
        }
        
        self.entity_patterns = [
            r'class\s+(\w+).*Entity',
            r'class\s+(\w+).*Model',
            r'table\s+(\w+)',
            r'entity\s+(\w+)',
            r'@Entity.*class\s+(\w+)'
        ]
        
        self.business_keywords = {
            'financial': ['payment', 'invoice', 'billing', 'transaction', 'account', 'balance', 'credit', 'debit'],
            'ecommerce': ['order', 'product', 'cart', 'checkout', 'inventory', 'shipping', 'customer'],
            'healthcare': ['patient', 'doctor', 'appointment', 'diagnosis', 'treatment', 'medical'],
            'education': ['student', 'course', 'grade', 'assignment', 'exam', 'enrollment'],
            'hr': ['employee', 'payroll', 'attendance', 'leave', 'performance', 'recruitment'],
            'crm': ['lead', 'opportunity', 'contact', 'sales', 'marketing', 'campaign'],
            'logistics': ['warehouse', 'shipping', 'delivery', 'tracking', 'supplier', 'procurement']
        }

    def analyze_business_rules(self, files: List[Dict[str, Any]], parse_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract business rules and processes from the codebase."""
        try:
            business_rules = []
            business_processes = []
            entities = []
            domain_analysis = self._analyze_business_domain(files, parse_results)
            
            # Analyze each file for business logic
            for i, file_info in enumerate(files):
                if i < len(parse_results):
                    parse_result = parse_results[i]
                    file_rules = self._extract_file_business_rules(file_info, parse_result)
                    business_rules.extend(file_rules)
                    
                    file_entities = self._extract_business_entities(file_info, parse_result)
                    entities.extend(file_entities)
            
            # Identify business processes
            business_processes = self._identify_business_processes(business_rules, entities, parse_results)
            
            # Generate business summary
            business_summary = self._generate_business_summary(
                domain_analysis, business_rules, business_processes, entities
            )
            
            return {
                'business_summary': business_summary,
                'domain_analysis': domain_analysis,
                'business_rules': [self._rule_to_dict(rule) for rule in business_rules],
                'business_processes': [self._process_to_dict(process) for process in business_processes],
                'business_entities': entities,
                'rule_categories': self._categorize_rules(business_rules),
                'complexity_assessment': self._assess_business_complexity(business_rules, business_processes)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing business rules: {e}")
            return {
                'business_summary': "Business analysis could not be completed due to parsing errors.",
                'domain_analysis': {'primary_domain': 'unknown', 'confidence': 0},
                'business_rules': [],
                'business_processes': [],
                'business_entities': [],
                'rule_categories': {},
                'complexity_assessment': 'unknown'
            }

    def _analyze_business_domain(self, files: List[Dict[str, Any]], parse_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the business domain of the application."""
        domain_scores = {domain: 0 for domain in self.business_keywords.keys()}
        
        # Analyze file names, class names, function names
        all_text = []
        
        for file_info in files:
            file_path = file_info.get('path', '').lower()
            file_content = file_info.get('content', '').lower()
            all_text.append(file_path)
            all_text.append(file_content[:1000])  # First 1000 chars for performance
        
        for parse_result in parse_results:
            # Add class names
            for cls in parse_result.get('classes', []):
                all_text.append(cls.get('name', '').lower())
            
            # Add function names
            for func in parse_result.get('functions', []):
                all_text.append(func.get('name', '').lower())
            
            # Add endpoint paths
            for endpoint in parse_result.get('endpoints', []):
                all_text.append(endpoint.get('path', '').lower())
        
        combined_text = ' '.join(all_text)
        
        # Score each domain
        for domain, keywords in self.business_keywords.items():
            for keyword in keywords:
                domain_scores[domain] += combined_text.count(keyword)
        
        # Find primary domain
        primary_domain = max(domain_scores.items(), key=lambda x: x[1])
        
        return {
            'primary_domain': primary_domain[0] if primary_domain[1] > 0 else 'general',
            'domain_scores': domain_scores,
            'confidence': min(100, primary_domain[1] * 10) if primary_domain[1] > 0 else 0,
            'detected_keywords': self._get_detected_keywords(combined_text)
        }

    def _extract_file_business_rules(self, file_info: Dict[str, Any], parse_result: Dict[str, Any]) -> List[BusinessRule]:
        """Extract business rules from a single file."""
        rules = []
        content = file_info.get('content', '')
        file_path = file_info.get('path', '')
        
        # Look for validation rules
        for pattern in self.business_patterns['validation_rules']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                rule = BusinessRule(
                    rule_type='validation',
                    description=f"Validation rule: {match.group(0)}",
                    location=file_path,
                    confidence=0.8,
                    code_snippet=self._extract_context(content, match.start(), match.end()),
                    impact='data_integrity'
                )
                rules.append(rule)
        
        # Look for business logic
        for pattern in self.business_patterns['business_logic']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                rule = BusinessRule(
                    rule_type='business_logic',
                    description=f"Business logic: {match.group(0)}",
                    location=file_path,
                    confidence=0.9,
                    code_snippet=self._extract_context(content, match.start(), match.end()),
                    impact='business_process'
                )
                rules.append(rule)
        
        # Look for authorization rules
        for pattern in self.business_patterns['authorization_rules']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                rule = BusinessRule(
                    rule_type='authorization',
                    description=f"Authorization rule: {match.group(0)}",
                    location=file_path,
                    confidence=0.85,
                    code_snippet=self._extract_context(content, match.start(), match.end()),
                    impact='security'
                )
                rules.append(rule)
        
        return rules

    def _extract_business_entities(self, file_info: Dict[str, Any], parse_result: Dict[str, Any]) -> List[str]:
        """Extract business entities from file."""
        entities = []
        content = file_info.get('content', '')
        
        # Extract from class names
        for cls in parse_result.get('classes', []):
            class_name = cls.get('name', '')
            if self._is_business_entity(class_name):
                entities.append(class_name)
        
        # Extract from table names
        for table in parse_result.get('tables', []):
            table_name = table.get('name', '')
            if self._is_business_entity(table_name):
                entities.append(table_name)
        
        return entities

    def _identify_business_processes(self, rules: List[BusinessRule], entities: List[str], parse_results: List[Dict[str, Any]]) -> List[BusinessProcess]:
        """Identify business processes from rules and entities."""
        processes = []
        
        # Group rules by type and analyze patterns
        validation_rules = [r for r in rules if r.rule_type == 'validation']
        business_logic_rules = [r for r in rules if r.rule_type == 'business_logic']
        
        # Identify common processes based on entities and rules
        entity_groups = self._group_related_entities(entities)
        
        for group_name, group_entities in entity_groups.items():
            related_rules = [r for r in business_logic_rules if any(entity.lower() in r.description.lower() for entity in group_entities)]
            
            if related_rules:
                process = BusinessProcess(
                    name=f"{group_name.title()} Management Process",
                    description=f"Business process involving {', '.join(group_entities)}",
                    steps=self._extract_process_steps(related_rules),
                    entities_involved=group_entities,
                    business_value=f"Manages {group_name} operations and ensures business rules compliance",
                    complexity='medium' if len(related_rules) > 3 else 'low'
                )
                processes.append(process)
        
        return processes

    def _generate_business_summary(self, domain_analysis: Dict[str, Any], rules: List[BusinessRule], 
                                 processes: List[BusinessProcess], entities: List[str]) -> str:
        """Generate a comprehensive business summary."""
        primary_domain = domain_analysis['primary_domain']
        confidence = domain_analysis['confidence']
        
        # Business domain description
        domain_descriptions = {
            'financial': 'a financial services application handling monetary transactions, accounts, and payment processing',
            'ecommerce': 'an e-commerce platform managing products, orders, customers, and online sales operations',
            'healthcare': 'a healthcare management system handling patient records, appointments, and medical workflows',
            'education': 'an educational platform managing students, courses, grades, and academic processes',
            'hr': 'a human resources management system handling employee data, payroll, and organizational processes',
            'crm': 'a customer relationship management system managing leads, contacts, and sales processes',
            'logistics': 'a logistics and supply chain management system handling inventory, shipping, and procurement'
        }
        
        domain_desc = domain_descriptions.get(primary_domain, 'a business application with specialized domain logic')
        
        # Business rules analysis
        rule_types = {}
        for rule in rules:
            rule_types[rule.rule_type] = rule_types.get(rule.rule_type, 0) + 1
        
        # Business processes analysis
        process_complexity = {}
        for process in processes:
            process_complexity[process.complexity] = process_complexity.get(process.complexity, 0) + 1
        
        # Generate summary
        summary_parts = []
        
        # Domain and purpose
        summary_parts.append(f"BUSINESS DOMAIN: This system operates as {domain_desc} with {confidence}% domain confidence.")
        
        # Core business entities
        if entities:
            key_entities = entities[:5]  # Top 5 entities
            summary_parts.append(f"CORE BUSINESS ENTITIES: The system manages {len(entities)} business entities including {', '.join(key_entities)}, representing the fundamental data structures that drive business operations.")
        
        # Business rules
        if rules:
            summary_parts.append(f"BUSINESS RULES: The application implements {len(rules)} business rules across {len(rule_types)} categories:")
            for rule_type, count in rule_types.items():
                summary_parts.append(f"- {rule_type.replace('_', ' ').title()}: {count} rules ensuring {self._get_rule_purpose(rule_type)}")
        
        # Business processes
        if processes:
            summary_parts.append(f"BUSINESS PROCESSES: The system orchestrates {len(processes)} key business processes:")
            for process in processes[:3]:  # Top 3 processes
                summary_parts.append(f"- {process.name}: {process.description} involving {', '.join(process.entities_involved[:3])}")
        
        # Business value and operations
        business_operations = self._identify_business_operations(rules, processes, entities)
        if business_operations:
            summary_parts.append(f"BUSINESS OPERATIONS: The system supports {business_operations}")
        
        # Compliance and governance
        compliance_rules = [r for r in rules if r.rule_type in ['validation', 'authorization']]
        if compliance_rules:
            summary_parts.append(f"COMPLIANCE & GOVERNANCE: {len(compliance_rules)} rules ensure data integrity, security, and regulatory compliance across business operations.")
        
        return ' '.join(summary_parts)

    def _extract_context(self, content: str, start: int, end: int, context_size: int = 100) -> str:
        """Extract code context around a match."""
        context_start = max(0, start - context_size)
        context_end = min(len(content), end + context_size)
        return content[context_start:context_end].strip()

    def _is_business_entity(self, name: str) -> bool:
        """Check if a name represents a business entity."""
        business_suffixes = ['entity', 'model', 'dto', 'vo', 'data']
        business_prefixes = ['user', 'customer', 'order', 'product', 'account', 'transaction']
        
        name_lower = name.lower()
        
        # Check suffixes
        if any(name_lower.endswith(suffix) for suffix in business_suffixes):
            return True
        
        # Check prefixes
        if any(name_lower.startswith(prefix) for prefix in business_prefixes):
            return True
        
        # Check if contains business keywords
        for keywords in self.business_keywords.values():
            if any(keyword in name_lower for keyword in keywords):
                return True
        
        return False

    def _group_related_entities(self, entities: List[str]) -> Dict[str, List[str]]:
        """Group related business entities."""
        groups = {}
        
        for entity in entities:
            entity_lower = entity.lower()
            
            # Determine group based on business domain
            group_assigned = False
            for domain, keywords in self.business_keywords.items():
                if any(keyword in entity_lower for keyword in keywords):
                    if domain not in groups:
                        groups[domain] = []
                    groups[domain].append(entity)
                    group_assigned = True
                    break
            
            if not group_assigned:
                if 'general' not in groups:
                    groups['general'] = []
                groups['general'].append(entity)
        
        return groups

    def _extract_process_steps(self, rules: List[BusinessRule]) -> List[str]:
        """Extract process steps from business rules."""
        steps = []
        for rule in rules:
            if 'calculate' in rule.description.lower():
                steps.append("Perform calculations and business logic")
            elif 'validate' in rule.description.lower():
                steps.append("Validate input data and business constraints")
            elif 'process' in rule.description.lower():
                steps.append("Process business transaction")
            elif 'approve' in rule.description.lower():
                steps.append("Execute approval workflow")
        
        return list(set(steps))  # Remove duplicates

    def _get_rule_purpose(self, rule_type: str) -> str:
        """Get the business purpose of a rule type."""
        purposes = {
            'validation': 'data quality and business constraint compliance',
            'business_logic': 'core business operations and calculations',
            'authorization': 'security and access control',
            'workflow': 'process orchestration and state management',
            'data': 'data integrity and relationship management'
        }
        return purposes.get(rule_type, 'business operations')

    def _identify_business_operations(self, rules: List[BusinessRule], processes: List[BusinessProcess], entities: List[str]) -> str:
        """Identify key business operations."""
        operations = []
        
        # From rules
        if any('payment' in r.description.lower() for r in rules):
            operations.append("payment processing")
        if any('order' in r.description.lower() for r in rules):
            operations.append("order management")
        if any('user' in r.description.lower() for r in rules):
            operations.append("user management")
        if any('inventory' in r.description.lower() for r in rules):
            operations.append("inventory control")
        
        # From entities
        entity_text = ' '.join(entities).lower()
        if 'customer' in entity_text:
            operations.append("customer relationship management")
        if 'product' in entity_text:
            operations.append("product catalog management")
        if 'transaction' in entity_text:
            operations.append("transaction processing")
        
        return ', '.join(operations) if operations else "general business operations"

    def _categorize_rules(self, rules: List[BusinessRule]) -> Dict[str, int]:
        """Categorize business rules by type."""
        categories = {}
        for rule in rules:
            categories[rule.rule_type] = categories.get(rule.rule_type, 0) + 1
        return categories

    def _assess_business_complexity(self, rules: List[BusinessRule], processes: List[BusinessProcess]) -> str:
        """Assess the business complexity of the system."""
        total_rules = len(rules)
        total_processes = len(processes)
        
        if total_rules > 20 or total_processes > 5:
            return 'high'
        elif total_rules > 10 or total_processes > 2:
            return 'medium'
        else:
            return 'low'

    def _get_detected_keywords(self, text: str) -> List[str]:
        """Get the most frequently detected business keywords."""
        detected = []
        for domain, keywords in self.business_keywords.items():
            for keyword in keywords:
                if keyword in text and text.count(keyword) > 1:
                    detected.append(keyword)
        return detected[:10]  # Top 10

    def _rule_to_dict(self, rule: BusinessRule) -> Dict[str, Any]:
        """Convert BusinessRule to dictionary."""
        return {
            'rule_type': rule.rule_type,
            'description': rule.description,
            'location': rule.location,
            'confidence': rule.confidence,
            'code_snippet': rule.code_snippet,
            'impact': rule.impact
        }

    def _process_to_dict(self, process: BusinessProcess) -> Dict[str, Any]:
        """Convert BusinessProcess to dictionary."""
        return {
            'name': process.name,
            'description': process.description,
            'steps': process.steps,
            'entities_involved': process.entities_involved,
            'business_value': process.business_value,
            'complexity': process.complexity
        }