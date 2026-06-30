"""Enhanced Database Analysis Service with DDL Parsing and ORM Generation."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types."""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"
    SQL_SERVER = "sql_server"
    SQLITE = "sqlite"
    UNKNOWN = "unknown"


class ColumnType(Enum):
    """Database column types."""
    INTEGER = "integer"
    STRING = "string"
    TEXT = "text"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIMESTAMP = "timestamp"
    BLOB = "blob"
    JSON = "json"
    UNKNOWN = "unknown"


@dataclass
class Column:
    """Database column definition."""
    name: str
    type: ColumnType
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    default_value: Optional[str] = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    auto_increment: bool = False
    unique: bool = False
    comment: Optional[str] = None


@dataclass
class Index:
    """Database index definition."""
    name: str
    columns: List[str]
    unique: bool = False
    type: str = "btree"


@dataclass
class ForeignKey:
    """Foreign key constraint definition."""
    name: str
    columns: List[str]
    referenced_table: str
    referenced_columns: List[str]
    on_delete: str = "RESTRICT"
    on_update: str = "RESTRICT"

@dataclass
class Table:
    """Database table definition."""
    name: str
    columns: List[Column]
    primary_keys: List[str]
    foreign_keys: List[ForeignKey]
    indexes: List[Index]
    comment: Optional[str] = None
    engine: Optional[str] = None
    charset: Optional[str] = None


@dataclass
class DatabaseSchema:
    """Complete database schema."""
    name: str
    tables: List[Table]
    views: List[Dict[str, Any]]
    procedures: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    triggers: List[Dict[str, Any]]
    database_type: DatabaseType


class DDLParser:
    """Parser for DDL (Data Definition Language) statements."""
    
    def __init__(self):
        self.database_type = DatabaseType.UNKNOWN
        self._type_mappings = self._build_type_mappings()
    
    def parse_ddl_file(self, content: str, file_path: str) -> DatabaseSchema:
        """Parse DDL file and extract schema information."""
        self.database_type = self._detect_database_type(content)
        
        tables = self._extract_tables(content)
        views = self._extract_views(content)
        procedures = self._extract_procedures(content)
        functions = self._extract_functions(content)
        triggers = self._extract_triggers(content)
        
        schema_name = self._extract_schema_name(content, file_path)
        
        return DatabaseSchema(
            name=schema_name,
            tables=tables,
            views=views,
            procedures=procedures,
            functions=functions,
            triggers=triggers,
            database_type=self.database_type
        )
    
    def _detect_database_type(self, content: str) -> DatabaseType:
        """Detect database type from DDL content."""
        content_lower = content.lower()
        
        # MySQL indicators
        if any(indicator in content_lower for indicator in [
            "auto_increment", "engine=innodb", "charset=utf8", "mysql"
        ]):
            return DatabaseType.MYSQL
        
        # PostgreSQL indicators
        if any(indicator in content_lower for indicator in [
            "serial", "bigserial", "uuid", "postgresql", "postgres"
        ]):
            return DatabaseType.POSTGRESQL
        
        # Oracle indicators
        if any(indicator in content_lower for indicator in [
            "number(", "varchar2", "clob", "blob", "oracle"
        ]):
            return DatabaseType.ORACLE
        
        # SQL Server indicators
        if any(indicator in content_lower for indicator in [
            "identity(", "nvarchar", "uniqueidentifier", "sql server"
        ]):
            return DatabaseType.SQL_SERVER
        
        # SQLite indicators
        if any(indicator in content_lower for indicator in [
            "sqlite", "autoincrement"
        ]):
            return DatabaseType.SQLITE
        
        return DatabaseType.UNKNOWN
    
    def _extract_tables(self, content: str) -> List[Table]:
        """Extract table definitions from DDL."""
        tables = []
        
        # Pattern to match CREATE TABLE statements
        table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`"]?\w+[`"]?)\s*\((.*?)\)(?:\s*ENGINE\s*=\s*(\w+))?(?:\s*CHARSET\s*=\s*(\w+))?'
        
        matches = re.finditer(table_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            table_name = match.group(1).strip('`"')
            table_definition = match.group(2)
            engine = match.group(3) if match.group(3) else None
            charset = match.group(4) if match.group(4) else None
            
            columns, primary_keys, foreign_keys, indexes = self._parse_table_definition(table_definition)
            
            table = Table(
                name=table_name,
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys,
                indexes=indexes,
                engine=engine,
                charset=charset
            )
            tables.append(table)
        
        return tables
    
    def _parse_table_definition(self, definition: str) -> Tuple[List[Column], List[str], List[ForeignKey], List[Index]]:
        """Parse table definition to extract columns, keys, and constraints."""
        columns = []
        primary_keys = []
        foreign_keys = []
        indexes = []
        
        # Split by commas, but be careful with nested parentheses
        parts = self._split_table_definition(definition)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            if part.upper().startswith('PRIMARY KEY'):
                primary_keys.extend(self._extract_primary_key_columns(part))
            elif part.upper().startswith('FOREIGN KEY') or 'REFERENCES' in part.upper():
                fk = self._extract_foreign_key(part)
                if fk:
                    foreign_keys.append(fk)
            elif part.upper().startswith('INDEX') or part.upper().startswith('KEY'):
                index = self._extract_index(part)
                if index:
                    indexes.append(index)
            else:
                # This should be a column definition
                column = self._parse_column_definition(part)
                if column:
                    columns.append(column)
                    if column.primary_key:
                        primary_keys.append(column.name)
        
        return columns, primary_keys, foreign_keys, indexes
    def _split_table_definition(self, definition: str) -> List[str]:
        """Split table definition by commas, handling nested parentheses."""
        parts = []
        current_part = ""
        paren_count = 0
        
        for char in definition:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                parts.append(current_part.strip())
                current_part = ""
                continue
            
            current_part += char
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts
    
    def _parse_column_definition(self, definition: str) -> Optional[Column]:
        """Parse a single column definition."""
        # Basic column pattern: column_name data_type [constraints]
        pattern = r'([`"]?\w+[`"]?)\s+(\w+(?:\(\d+(?:,\d+)?\))?)\s*(.*)'
        match = re.match(pattern, definition.strip(), re.IGNORECASE)
        
        if not match:
            return None
        
        column_name = match.group(1).strip('`"')
        data_type = match.group(2)
        constraints = match.group(3) if match.group(3) else ""
        
        # Parse data type
        column_type, max_length, precision, scale = self._parse_data_type(data_type)
        
        # Parse constraints
        nullable = "NOT NULL" not in constraints.upper()
        primary_key = "PRIMARY KEY" in constraints.upper()
        auto_increment = any(keyword in constraints.upper() for keyword in ["AUTO_INCREMENT", "IDENTITY", "SERIAL"])
        unique = "UNIQUE" in constraints.upper()
        
        # Extract default value
        default_match = re.search(r'DEFAULT\s+([^,\s]+)', constraints, re.IGNORECASE)
        default_value = default_match.group(1) if default_match else None
        
        # Extract foreign key reference
        foreign_key = None
        fk_match = re.search(r'REFERENCES\s+(\w+)\s*\((\w+)\)', constraints, re.IGNORECASE)
        if fk_match:
            foreign_key = f"{fk_match.group(1)}.{fk_match.group(2)}"
        
        return Column(
            name=column_name,
            type=column_type,
            nullable=nullable,
            primary_key=primary_key,
            foreign_key=foreign_key,
            default_value=default_value,
            max_length=max_length,
            precision=precision,
            scale=scale,
            auto_increment=auto_increment,
            unique=unique
        )
    
    def _parse_data_type(self, data_type: str) -> Tuple[ColumnType, Optional[int], Optional[int], Optional[int]]:
        """Parse data type and extract type, length, precision, scale."""
        # Extract type name and parameters
        type_match = re.match(r'(\w+)(?:\((\d+)(?:,(\d+))?\))?', data_type, re.IGNORECASE)
        
        if not type_match:
            return ColumnType.UNKNOWN, None, None, None
        
        type_name = type_match.group(1).lower()
        param1 = int(type_match.group(2)) if type_match.group(2) else None
        param2 = int(type_match.group(3)) if type_match.group(3) else None
        
        # Map to standard column type
        column_type = self._map_column_type(type_name)
        
        # Determine what the parameters mean based on type
        max_length = None
        precision = None
        scale = None
        
        if column_type in [ColumnType.STRING, ColumnType.TEXT]:
            max_length = param1
        elif column_type == ColumnType.DECIMAL:
            precision = param1
            scale = param2
        
        return column_type, max_length, precision, scale
    
    def _map_column_type(self, type_name: str) -> ColumnType:
        """Map database-specific type to standard column type."""
        type_mappings = {
            # Integer types
            'int': ColumnType.INTEGER,
            'integer': ColumnType.INTEGER,
            'bigint': ColumnType.INTEGER,
            'smallint': ColumnType.INTEGER,
            'tinyint': ColumnType.INTEGER,
            'serial': ColumnType.INTEGER,
            'bigserial': ColumnType.INTEGER,
            'number': ColumnType.INTEGER,
            
            # String types
            'varchar': ColumnType.STRING,
            'varchar2': ColumnType.STRING,
            'char': ColumnType.STRING,
            'nvarchar': ColumnType.STRING,
            'nchar': ColumnType.STRING,
            'text': ColumnType.TEXT,
            'longtext': ColumnType.TEXT,
            'mediumtext': ColumnType.TEXT,
            'clob': ColumnType.TEXT,
            
            # Decimal types
            'decimal': ColumnType.DECIMAL,
            'numeric': ColumnType.DECIMAL,
            'float': ColumnType.DECIMAL,
            'double': ColumnType.DECIMAL,
            'real': ColumnType.DECIMAL,
            
            # Boolean types
            'boolean': ColumnType.BOOLEAN,
            'bool': ColumnType.BOOLEAN,
            'bit': ColumnType.BOOLEAN,
            
            # Date/Time types
            'date': ColumnType.DATE,
            'datetime': ColumnType.DATETIME,
            'timestamp': ColumnType.TIMESTAMP,
            'time': ColumnType.DATETIME,
            
            # Binary types
            'blob': ColumnType.BLOB,
            'longblob': ColumnType.BLOB,
            'mediumblob': ColumnType.BLOB,
            'binary': ColumnType.BLOB,
            'varbinary': ColumnType.BLOB,
            
            # JSON types
            'json': ColumnType.JSON,
            'jsonb': ColumnType.JSON,
        }
        
        return type_mappings.get(type_name.lower(), ColumnType.UNKNOWN)
    
    def _extract_primary_key_columns(self, constraint: str) -> List[str]:
        """Extract primary key column names."""
        # Pattern: PRIMARY KEY (col1, col2, ...)
        pattern = r'PRIMARY\s+KEY\s*\(\s*([^)]+)\s*\)'
        match = re.search(pattern, constraint, re.IGNORECASE)
        
        if match:
            columns_str = match.group(1)
            return [col.strip().strip('`"') for col in columns_str.split(',')]
        
        return []
    
    def _extract_foreign_key(self, constraint: str) -> Optional[ForeignKey]:
        """Extract foreign key constraint."""
        # Pattern: FOREIGN KEY (col1, col2) REFERENCES table (ref_col1, ref_col2)
        pattern = r'FOREIGN\s+KEY\s*\(\s*([^)]+)\s*\)\s+REFERENCES\s+([`"]?\w+[`"]?)\s*\(\s*([^)]+)\s*\)'
        match = re.search(pattern, constraint, re.IGNORECASE)
        
        if match:
            columns = [col.strip().strip('`"') for col in match.group(1).split(',')]
            ref_table = match.group(2).strip('`"')
            ref_columns = [col.strip().strip('`"') for col in match.group(3).split(',')]
            
            # Extract ON DELETE/UPDATE actions
            on_delete = "RESTRICT"
            on_update = "RESTRICT"
            
            delete_match = re.search(r'ON\s+DELETE\s+(\w+)', constraint, re.IGNORECASE)
            if delete_match:
                on_delete = delete_match.group(1).upper()
            
            update_match = re.search(r'ON\s+UPDATE\s+(\w+)', constraint, re.IGNORECASE)
            if update_match:
                on_update = update_match.group(1).upper()
            
            return ForeignKey(
                name=f"fk_{ref_table}_{'_'.join(columns)}",
                columns=columns,
                referenced_table=ref_table,
                referenced_columns=ref_columns,
                on_delete=on_delete,
                on_update=on_update
            )
        
        return None
    
    def _extract_index(self, constraint: str) -> Optional[Index]:
        """Extract index definition."""
        # Pattern: INDEX index_name (col1, col2) or KEY index_name (col1, col2)
        pattern = r'(?:INDEX|KEY)\s+([`"]?\w+[`"]?)\s*\(\s*([^)]+)\s*\)'
        match = re.search(pattern, constraint, re.IGNORECASE)
        
        if match:
            index_name = match.group(1).strip('`"')
            columns = [col.strip().strip('`"') for col in match.group(2).split(',')]
            unique = "UNIQUE" in constraint.upper()
            
            return Index(
                name=index_name,
                columns=columns,
                unique=unique
            )
        
        return None
    def _extract_views(self, content: str) -> List[Dict[str, Any]]:
        """Extract view definitions."""
        views = []
        pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+([`"]?\w+[`"]?)\s+AS\s+(.*?)(?=CREATE|$)'
        
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            view_name = match.group(1).strip('`"')
            view_definition = match.group(2).strip()
            
            views.append({
                "name": view_name,
                "definition": view_definition,
                "type": "view"
            })
        
        return views
    
    def _extract_procedures(self, content: str) -> List[Dict[str, Any]]:
        """Extract stored procedure definitions."""
        procedures = []
        pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+([`"]?\w+[`"]?)\s*\((.*?)\)\s+(.*?)(?=CREATE|$)'
        
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            proc_name = match.group(1).strip('`"')
            parameters = match.group(2).strip()
            body = match.group(3).strip()
            
            procedures.append({
                "name": proc_name,
                "parameters": parameters,
                "body": body,
                "type": "procedure"
            })
        
        return procedures
    
    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function definitions."""
        functions = []
        pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+([`"]?\w+[`"]?)\s*\((.*?)\)\s+RETURNS\s+(\w+)\s+(.*?)(?=CREATE|$)'
        
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            func_name = match.group(1).strip('`"')
            parameters = match.group(2).strip()
            return_type = match.group(3).strip()
            body = match.group(4).strip()
            
            functions.append({
                "name": func_name,
                "parameters": parameters,
                "return_type": return_type,
                "body": body,
                "type": "function"
            })
        
        return functions
    
    def _extract_triggers(self, content: str) -> List[Dict[str, Any]]:
        """Extract trigger definitions."""
        triggers = []
        pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER\s+([`"]?\w+[`"]?)\s+(BEFORE|AFTER)\s+(\w+)\s+ON\s+([`"]?\w+[`"]?)\s+(.*?)(?=CREATE|$)'
        
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            trigger_name = match.group(1).strip('`"')
            timing = match.group(2).upper()
            event = match.group(3).upper()
            table_name = match.group(4).strip('`"')
            body = match.group(5).strip()
            
            triggers.append({
                "name": trigger_name,
                "timing": timing,
                "event": event,
                "table": table_name,
                "body": body,
                "type": "trigger"
            })
        
        return triggers
    
    def _extract_schema_name(self, content: str, file_path: str) -> str:
        """Extract schema name from content or file path."""
        # Try to find schema name in USE statement
        use_match = re.search(r'USE\s+([`"]?\w+[`"]?)', content, re.IGNORECASE)
        if use_match:
            return use_match.group(1).strip('`"')
        
        # Try to find schema name in CREATE SCHEMA statement
        schema_match = re.search(r'CREATE\s+SCHEMA\s+([`"]?\w+[`"]?)', content, re.IGNORECASE)
        if schema_match:
            return schema_match.group(1).strip('`"')
        
        # Fall back to file name
        import os
        return os.path.splitext(os.path.basename(file_path))[0]
    
    def _build_type_mappings(self) -> Dict[str, ColumnType]:
        """Build comprehensive type mappings for all supported databases."""
        return {
            # MySQL types
            'tinyint': ColumnType.INTEGER,
            'smallint': ColumnType.INTEGER,
            'mediumint': ColumnType.INTEGER,
            'int': ColumnType.INTEGER,
            'bigint': ColumnType.INTEGER,
            'decimal': ColumnType.DECIMAL,
            'float': ColumnType.DECIMAL,
            'double': ColumnType.DECIMAL,
            'bit': ColumnType.BOOLEAN,
            'char': ColumnType.STRING,
            'varchar': ColumnType.STRING,
            'binary': ColumnType.BLOB,
            'varbinary': ColumnType.BLOB,
            'tinyblob': ColumnType.BLOB,
            'blob': ColumnType.BLOB,
            'mediumblob': ColumnType.BLOB,
            'longblob': ColumnType.BLOB,
            'tinytext': ColumnType.TEXT,
            'text': ColumnType.TEXT,
            'mediumtext': ColumnType.TEXT,
            'longtext': ColumnType.TEXT,
            'date': ColumnType.DATE,
            'time': ColumnType.DATETIME,
            'datetime': ColumnType.DATETIME,
            'timestamp': ColumnType.TIMESTAMP,
            'year': ColumnType.INTEGER,
            'json': ColumnType.JSON,
            
            # PostgreSQL types
            'smallserial': ColumnType.INTEGER,
            'serial': ColumnType.INTEGER,
            'bigserial': ColumnType.INTEGER,
            'integer': ColumnType.INTEGER,
            'numeric': ColumnType.DECIMAL,
            'real': ColumnType.DECIMAL,
            'double precision': ColumnType.DECIMAL,
            'boolean': ColumnType.BOOLEAN,
            'character': ColumnType.STRING,
            'character varying': ColumnType.STRING,
            'bytea': ColumnType.BLOB,
            'timestamp without time zone': ColumnType.TIMESTAMP,
            'timestamp with time zone': ColumnType.TIMESTAMP,
            'time without time zone': ColumnType.DATETIME,
            'time with time zone': ColumnType.DATETIME,
            'interval': ColumnType.STRING,
            'uuid': ColumnType.STRING,
            'jsonb': ColumnType.JSON,
            
            # Oracle types
            'number': ColumnType.DECIMAL,
            'varchar2': ColumnType.STRING,
            'nvarchar2': ColumnType.STRING,
            'char': ColumnType.STRING,
            'nchar': ColumnType.STRING,
            'clob': ColumnType.TEXT,
            'nclob': ColumnType.TEXT,
            'blob': ColumnType.BLOB,
            'bfile': ColumnType.BLOB,
            'raw': ColumnType.BLOB,
            'long raw': ColumnType.BLOB,
            'date': ColumnType.DATETIME,  # Oracle DATE includes time
            'timestamp': ColumnType.TIMESTAMP,
            'timestamp with time zone': ColumnType.TIMESTAMP,
            'timestamp with local time zone': ColumnType.TIMESTAMP,
            'interval year to month': ColumnType.STRING,
            'interval day to second': ColumnType.STRING,
            
            # SQL Server types
            'tinyint': ColumnType.INTEGER,
            'smallint': ColumnType.INTEGER,
            'int': ColumnType.INTEGER,
            'bigint': ColumnType.INTEGER,
            'decimal': ColumnType.DECIMAL,
            'numeric': ColumnType.DECIMAL,
            'float': ColumnType.DECIMAL,
            'real': ColumnType.DECIMAL,
            'money': ColumnType.DECIMAL,
            'smallmoney': ColumnType.DECIMAL,
            'bit': ColumnType.BOOLEAN,
            'char': ColumnType.STRING,
            'varchar': ColumnType.STRING,
            'nchar': ColumnType.STRING,
            'nvarchar': ColumnType.STRING,
            'text': ColumnType.TEXT,
            'ntext': ColumnType.TEXT,
            'binary': ColumnType.BLOB,
            'varbinary': ColumnType.BLOB,
            'image': ColumnType.BLOB,
            'date': ColumnType.DATE,
            'time': ColumnType.DATETIME,
            'datetime': ColumnType.DATETIME,
            'datetime2': ColumnType.DATETIME,
            'smalldatetime': ColumnType.DATETIME,
            'datetimeoffset': ColumnType.TIMESTAMP,
            'timestamp': ColumnType.BLOB,  # SQL Server timestamp is binary
            'uniqueidentifier': ColumnType.STRING,
            'xml': ColumnType.TEXT,
        }


class ORMGenerator:
    """Generate ORM models from database schema."""
    
    def __init__(self, target_language: str = "python"):
        self.target_language = target_language.lower()
    
    def generate_orm_models(self, schema: DatabaseSchema) -> Dict[str, str]:
        """Generate ORM model files from database schema."""
        if self.target_language == "python":
            return self._generate_python_models(schema)
        elif self.target_language == "java":
            return self._generate_java_models(schema)
        elif self.target_language == "csharp":
            return self._generate_csharp_models(schema)
        else:
            raise ValueError(f"Unsupported target language: {self.target_language}")
    
    def _generate_python_models(self, schema: DatabaseSchema) -> Dict[str, str]:
        """Generate Python SQLAlchemy models."""
        models = {}
        
        # Generate base imports
        imports = [
            "from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Decimal, ForeignKey, Index",
            "from sqlalchemy.ext.declarative import declarative_base",
            "from sqlalchemy.orm import relationship",
            "from datetime import datetime",
            "from typing import Optional",
            "",
            "Base = declarative_base()",
            ""
        ]
        
        model_classes = []
        
        for table in schema.tables:
            class_name = self._to_pascal_case(table.name)
            
            class_def = [f"class {class_name}(Base):"]
            class_def.append(f'    __tablename__ = "{table.name}"')
            class_def.append("")
            
            # Generate columns
            for column in table.columns:
                column_def = self._generate_python_column(column)
                class_def.append(f"    {column_def}")
            
            # Generate indexes
            if table.indexes:
                class_def.append("")
                for index in table.indexes:
                    index_def = self._generate_python_index(index)
                    class_def.append(f"    {index_def}")
            
            class_def.append("")
            model_classes.extend(class_def)
        
        # Combine all parts
        full_content = "\n".join(imports + model_classes)
        models[f"{schema.name}_models.py"] = full_content
        
        return models
    def _generate_python_column(self, column: Column) -> str:
        """Generate Python SQLAlchemy column definition."""
        # Map column type to SQLAlchemy type
        type_mapping = {
            ColumnType.INTEGER: "Integer",
            ColumnType.STRING: f"String({column.max_length})" if column.max_length else "String",
            ColumnType.TEXT: "Text",
            ColumnType.DECIMAL: f"Decimal({column.precision}, {column.scale})" if column.precision else "Decimal",
            ColumnType.BOOLEAN: "Boolean",
            ColumnType.DATE: "Date",
            ColumnType.DATETIME: "DateTime",
            ColumnType.TIMESTAMP: "DateTime",
            ColumnType.BLOB: "LargeBinary",
            ColumnType.JSON: "JSON",
            ColumnType.UNKNOWN: "String"
        }
        
        column_type = type_mapping.get(column.type, "String")
        
        # Build column definition
        parts = [f"{column.name} = Column({column_type}"]
        
        if column.primary_key:
            parts.append("primary_key=True")
        
        if column.foreign_key:
            fk_table, fk_column = column.foreign_key.split('.')
            parts.append(f'ForeignKey("{fk_table}.{fk_column}")')
        
        if not column.nullable:
            parts.append("nullable=False")
        
        if column.unique:
            parts.append("unique=True")
        
        if column.default_value:
            parts.append(f"default={column.default_value}")
        
        if column.auto_increment:
            parts.append("autoincrement=True")
        
        return ", ".join(parts) + ")"
    
    def _generate_python_index(self, index: Index) -> str:
        """Generate Python SQLAlchemy index definition."""
        columns_str = ", ".join([f'"{col}"' for col in index.columns])
        unique_str = ", unique=True" if index.unique else ""
        return f'__table_args__ = (Index("{index.name}", {columns_str}{unique_str}),)'
    
    def _generate_java_models(self, schema: DatabaseSchema) -> Dict[str, str]:
        """Generate Java JPA entity models."""
        models = {}
        
        for table in schema.tables:
            class_name = self._to_pascal_case(table.name)
            
            # Generate imports
            imports = [
                "import javax.persistence.*;",
                "import java.time.LocalDateTime;",
                "import java.math.BigDecimal;",
                "import java.util.Date;",
                ""
            ]
            
            # Generate class
            class_def = [
                "@Entity",
                f'@Table(name = "{table.name}")',
                f"public class {class_name} {{",
                ""
            ]
            
            # Generate fields
            for column in table.columns:
                field_def = self._generate_java_field(column)
                class_def.extend(field_def)
                class_def.append("")
            
            # Generate getters and setters
            for column in table.columns:
                getter_setter = self._generate_java_getter_setter(column)
                class_def.extend(getter_setter)
                class_def.append("")
            
            class_def.append("}")
            
            # Combine all parts
            full_content = "\n".join(imports + class_def)
            models[f"{class_name}.java"] = full_content
        
        return models
    
    def _generate_java_field(self, column: Column) -> List[str]:
        """Generate Java JPA field definition."""
        field_def = []
        
        # Add annotations
        if column.primary_key:
            field_def.append("    @Id")
            if column.auto_increment:
                field_def.append("    @GeneratedValue(strategy = GenerationType.IDENTITY)")
        
        if column.foreign_key:
            field_def.append("    @ManyToOne")
            field_def.append("    @JoinColumn(name = \"" + column.name + "\")")
        else:
            field_def.append(f'    @Column(name = "{column.name}")')
        
        # Map column type to Java type
        java_type = self._map_to_java_type(column)
        field_name = self._to_camel_case(column.name)
        
        field_def.append(f"    private {java_type} {field_name};")
        
        return field_def
    
    def _generate_java_getter_setter(self, column: Column) -> List[str]:
        """Generate Java getter and setter methods."""
        java_type = self._map_to_java_type(column)
        field_name = self._to_camel_case(column.name)
        method_name = self._to_pascal_case(column.name)
        
        getter_setter = [
            f"    public {java_type} get{method_name}() {{",
            f"        return {field_name};",
            "    }",
            "",
            f"    public void set{method_name}({java_type} {field_name}) {{",
            f"        this.{field_name} = {field_name};",
            "    }"
        ]
        
        return getter_setter
    
    def _map_to_java_type(self, column: Column) -> str:
        """Map column type to Java type."""
        type_mapping = {
            ColumnType.INTEGER: "Integer",
            ColumnType.STRING: "String",
            ColumnType.TEXT: "String",
            ColumnType.DECIMAL: "BigDecimal",
            ColumnType.BOOLEAN: "Boolean",
            ColumnType.DATE: "Date",
            ColumnType.DATETIME: "LocalDateTime",
            ColumnType.TIMESTAMP: "LocalDateTime",
            ColumnType.BLOB: "byte[]",
            ColumnType.JSON: "String",
            ColumnType.UNKNOWN: "String"
        }
        
        return type_mapping.get(column.type, "String")
    
    def _generate_csharp_models(self, schema: DatabaseSchema) -> Dict[str, str]:
        """Generate C# Entity Framework models."""
        models = {}
        
        for table in schema.tables:
            class_name = self._to_pascal_case(table.name)
            
            # Generate using statements
            usings = [
                "using System;",
                "using System.ComponentModel.DataAnnotations;",
                "using System.ComponentModel.DataAnnotations.Schema;",
                "",
                f"namespace {schema.name}.Models",
                "{",
                ""
            ]
            
            # Generate class
            class_def = [
                f'    [Table("{table.name}")]',
                f"    public class {class_name}",
                "    {",
                ""
            ]
            
            # Generate properties
            for column in table.columns:
                prop_def = self._generate_csharp_property(column)
                class_def.extend(prop_def)
                class_def.append("")
            
            class_def.extend(["    }", "}"])
            
            # Combine all parts
            full_content = "\n".join(usings + class_def)
            models[f"{class_name}.cs"] = full_content
        
        return models
    
    def _generate_csharp_property(self, column: Column) -> List[str]:
        """Generate C# property definition."""
        prop_def = []
        
        # Add attributes
        if column.primary_key:
            prop_def.append("        [Key]")
        
        if not column.nullable and column.type != ColumnType.BOOLEAN:
            prop_def.append("        [Required]")
        
        if column.max_length:
            prop_def.append(f"        [MaxLength({column.max_length})]")
        
        prop_def.append(f'        [Column("{column.name}")]')
        
        # Map column type to C# type
        csharp_type = self._map_to_csharp_type(column)
        prop_name = self._to_pascal_case(column.name)
        
        prop_def.append(f"        public {csharp_type} {prop_name} {{ get; set; }}")
        
        return prop_def
    
    def _map_to_csharp_type(self, column: Column) -> str:
        """Map column type to C# type."""
        type_mapping = {
            ColumnType.INTEGER: "int" if column.nullable else "int?",
            ColumnType.STRING: "string",
            ColumnType.TEXT: "string",
            ColumnType.DECIMAL: "decimal" if column.nullable else "decimal?",
            ColumnType.BOOLEAN: "bool" if column.nullable else "bool?",
            ColumnType.DATE: "DateTime" if column.nullable else "DateTime?",
            ColumnType.DATETIME: "DateTime" if column.nullable else "DateTime?",
            ColumnType.TIMESTAMP: "DateTime" if column.nullable else "DateTime?",
            ColumnType.BLOB: "byte[]",
            ColumnType.JSON: "string",
            ColumnType.UNKNOWN: "string"
        }
        
        return type_mapping.get(column.type, "string")
    
    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase."""
        return ''.join(word.capitalize() for word in snake_str.split('_'))
    
    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split('_')
        return components[0] + ''.join(word.capitalize() for word in components[1:])


class DatabaseAnalyzer:
    """Main database analyzer service."""
    
    def __init__(self):
        self.ddl_parser = DDLParser()
        self.orm_generator = ORMGenerator()
    
    def analyze_database_files(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze database files and generate comprehensive analysis."""
        schemas = []
        orm_models = {}
        
        for file_info in files:
            if self._is_database_file(file_info):
                try:
                    schema = self.ddl_parser.parse_ddl_file(
                        file_info.get("content", ""),
                        file_info.get("path", "")
                    )
                    schemas.append(schema)
                    
                    # Generate ORM models
                    models = self.orm_generator.generate_orm_models(schema)
                    orm_models.update(models)
                    
                except Exception as e:
                    logger.error(f"Error analyzing database file {file_info.get('path')}: {e}")
        
        # Generate analysis summary
        analysis = self._generate_database_analysis(schemas)
        
        return {
            "schemas": [self._schema_to_dict(schema) for schema in schemas],
            "orm_models": orm_models,
            "analysis": analysis,
            "recommendations": self._generate_database_recommendations(schemas)
        }
    
    def _is_database_file(self, file_info: Dict[str, Any]) -> bool:
        """Check if file is a database-related file."""
        path = file_info.get("path", "").lower()
        extension = file_info.get("extension", "").lower()
        content = file_info.get("content", "").lower()
        
        # Check file extension
        if extension in [".sql", ".ddl", ".dml"]:
            return True
        
        # Check path patterns
        if any(pattern in path for pattern in ["database", "db", "schema", "migration"]):
            return True
        
        # Check content patterns
        if any(keyword in content for keyword in ["create table", "create view", "create procedure"]):
            return True
        
        return False
    
    def _schema_to_dict(self, schema: DatabaseSchema) -> Dict[str, Any]:
        """Convert schema object to dictionary."""
        return {
            "name": schema.name,
            "database_type": schema.database_type.value,
            "tables": [self._table_to_dict(table) for table in schema.tables],
            "views": schema.views,
            "procedures": schema.procedures,
            "functions": schema.functions,
            "triggers": schema.triggers
        }
    
    def _table_to_dict(self, table: Table) -> Dict[str, Any]:
        """Convert table object to dictionary."""
        return {
            "name": table.name,
            "columns": [self._column_to_dict(col) for col in table.columns],
            "primary_keys": table.primary_keys,
            "foreign_keys": [self._foreign_key_to_dict(fk) for fk in table.foreign_keys],
            "indexes": [self._index_to_dict(idx) for idx in table.indexes],
            "comment": table.comment,
            "engine": table.engine,
            "charset": table.charset
        }
    
    def _column_to_dict(self, column: Column) -> Dict[str, Any]:
        """Convert column object to dictionary."""
        return {
            "name": column.name,
            "type": column.type.value,
            "nullable": column.nullable,
            "primary_key": column.primary_key,
            "foreign_key": column.foreign_key,
            "default_value": column.default_value,
            "max_length": column.max_length,
            "precision": column.precision,
            "scale": column.scale,
            "auto_increment": column.auto_increment,
            "unique": column.unique,
            "comment": column.comment
        }
    
    def _foreign_key_to_dict(self, fk: ForeignKey) -> Dict[str, Any]:
        """Convert foreign key object to dictionary."""
        return {
            "name": fk.name,
            "columns": fk.columns,
            "referenced_table": fk.referenced_table,
            "referenced_columns": fk.referenced_columns,
            "on_delete": fk.on_delete,
            "on_update": fk.on_update
        }
    
    def _index_to_dict(self, index: Index) -> Dict[str, Any]:
        """Convert index object to dictionary."""
        return {
            "name": index.name,
            "columns": index.columns,
            "unique": index.unique,
            "type": index.type
        }
    
    def _generate_database_analysis(self, schemas: List[DatabaseSchema]) -> Dict[str, Any]:
        """Generate comprehensive database analysis."""
        if not schemas:
            return {"error": "No database schemas found"}
        
        total_tables = sum(len(schema.tables) for schema in schemas)
        total_columns = sum(len(table.columns) for schema in schemas for table in schema.tables)
        total_indexes = sum(len(table.indexes) for schema in schemas for table in schema.tables)
        total_foreign_keys = sum(len(table.foreign_keys) for schema in schemas for table in schema.tables)
        
        # Analyze database types
        db_types = [schema.database_type.value for schema in schemas]
        primary_db_type = max(set(db_types), key=db_types.count) if db_types else "unknown"
        
        # Analyze table relationships
        relationship_analysis = self._analyze_table_relationships(schemas)
        
        # Analyze data types usage
        type_analysis = self._analyze_column_types(schemas)
        
        return {
            "total_schemas": len(schemas),
            "total_tables": total_tables,
            "total_columns": total_columns,
            "total_indexes": total_indexes,
            "total_foreign_keys": total_foreign_keys,
            "primary_database_type": primary_db_type,
            "relationship_analysis": relationship_analysis,
            "type_analysis": type_analysis,
            "complexity_score": self._calculate_database_complexity(schemas)
        }
    
    def _analyze_table_relationships(self, schemas: List[DatabaseSchema]) -> Dict[str, Any]:
        """Analyze relationships between tables."""
        all_tables = [table for schema in schemas for table in schema.tables]
        
        # Build relationship graph
        relationships = {}
        for table in all_tables:
            relationships[table.name] = {
                "references": [],
                "referenced_by": []
            }
        
        for table in all_tables:
            for fk in table.foreign_keys:
                if fk.referenced_table in relationships:
                    relationships[table.name]["references"].append(fk.referenced_table)
                    relationships[fk.referenced_table]["referenced_by"].append(table.name)
        
        # Calculate relationship metrics
        isolated_tables = [name for name, rels in relationships.items() 
                          if not rels["references"] and not rels["referenced_by"]]
        
        highly_connected = [name for name, rels in relationships.items() 
                           if len(rels["references"]) + len(rels["referenced_by"]) > 5]
        
        return {
            "total_relationships": sum(len(table.foreign_keys) for table in all_tables),
            "isolated_tables": len(isolated_tables),
            "highly_connected_tables": len(highly_connected),
            "relationship_graph": relationships
        }
    
    def _analyze_column_types(self, schemas: List[DatabaseSchema]) -> Dict[str, Any]:
        """Analyze column type usage across schemas."""
        type_counts = {}
        all_columns = [col for schema in schemas for table in schema.tables for col in table.columns]
        
        for column in all_columns:
            type_name = column.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            "type_distribution": type_counts,
            "most_common_type": max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None,
            "total_columns": len(all_columns)
        }
    
    def _calculate_database_complexity(self, schemas: List[DatabaseSchema]) -> float:
        """Calculate database complexity score."""
        if not schemas:
            return 0.0
        
        total_tables = sum(len(schema.tables) for schema in schemas)
        total_relationships = sum(len(table.foreign_keys) for schema in schemas for table in schema.tables)
        total_indexes = sum(len(table.indexes) for schema in schemas for table in schema.tables)
        
        # Normalize scores
        table_score = min(total_tables / 20.0, 1.0)  # Normalize to 20 tables
        relationship_score = min(total_relationships / 30.0, 1.0)  # Normalize to 30 relationships
        index_score = min(total_indexes / 50.0, 1.0)  # Normalize to 50 indexes
        
        # Weighted complexity score
        complexity = (table_score * 0.4 + relationship_score * 0.4 + index_score * 0.2)
        
        return round(complexity, 2)
    
    def _generate_database_recommendations(self, schemas: List[DatabaseSchema]) -> List[Dict[str, Any]]:
        """Generate database improvement recommendations."""
        recommendations = []
        
        if not schemas:
            return recommendations
        
        all_tables = [table for schema in schemas for table in schema.tables]
        
        # Check for missing indexes
        tables_without_indexes = [table for table in all_tables if not table.indexes]
        if tables_without_indexes:
            recommendations.append({
                "type": "performance",
                "priority": "medium",
                "title": "Add indexes to improve query performance",
                "description": f"{len(tables_without_indexes)} tables have no indexes defined",
                "affected_tables": [table.name for table in tables_without_indexes]
            })
        
        # Check for missing foreign key constraints
        potential_fks = []
        for table in all_tables:
            for column in table.columns:
                if column.name.endswith('_id') and not column.foreign_key:
                    potential_fks.append(f"{table.name}.{column.name}")
        
        if potential_fks:
            recommendations.append({
                "type": "data_integrity",
                "priority": "high",
                "title": "Consider adding foreign key constraints",
                "description": f"Found {len(potential_fks)} columns that might need foreign key constraints",
                "affected_columns": potential_fks[:10]  # Limit to first 10
            })
        
        # Check for tables without primary keys
        tables_without_pk = [table for table in all_tables if not table.primary_keys]
        if tables_without_pk:
            recommendations.append({
                "type": "data_integrity",
                "priority": "high",
                "title": "Add primary keys to tables",
                "description": f"{len(tables_without_pk)} tables have no primary key defined",
                "affected_tables": [table.name for table in tables_without_pk]
            })
        
        return recommendations