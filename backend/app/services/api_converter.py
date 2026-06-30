"""API Conversion Service with Annotation and Route Extraction."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HTTPMethod(Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class APIFramework(Enum):
    """Supported API frameworks."""
    SPRING_BOOT = "spring_boot"
    FLASK = "flask"
    FASTAPI = "fastapi"
    EXPRESS = "express"
    ASP_NET = "asp_net"
    DJANGO = "django"
    UNKNOWN = "unknown"


@dataclass
class Parameter:
    """API parameter definition."""
    name: str
    type: str
    required: bool = True
    location: str = "query"  # query, path, body, header
    description: Optional[str] = None
    default_value: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None


@dataclass
class Response:
    """API response definition."""
    status_code: int
    description: str
    content_type: str = "application/json"
    schema: Optional[Dict[str, Any]] = None
    examples: Optional[List[Dict[str, Any]]] = None


@dataclass
class APIEndpoint:
    """API endpoint definition."""
    path: str
    method: HTTPMethod
    function_name: str
    parameters: List[Parameter]
    responses: List[Response]
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    deprecated: bool = False
    security: Optional[List[str]] = None
    file_path: str = ""
    line_number: int = 0


@dataclass
class APIModel:
    """API data model definition."""
    name: str
    properties: Dict[str, Dict[str, Any]]
    required_fields: List[str]
    description: Optional[str] = None
    example: Optional[Dict[str, Any]] = None


class APIExtractor:
    """Extract API information from source code."""
    
    def __init__(self):
        self.framework_detectors = {
            APIFramework.SPRING_BOOT: self._detect_spring_boot,
            APIFramework.FLASK: self._detect_flask,
            APIFramework.FASTAPI: self._detect_fastapi,
            APIFramework.EXPRESS: self._detect_express,
            APIFramework.ASP_NET: self._detect_asp_net,
            APIFramework.DJANGO: self._detect_django,
        }
    
    def extract_api_info(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract comprehensive API information from files."""
        endpoints = []
        models = []
        frameworks_detected = set()
        
        for file_info in files:
            if self._is_api_file(file_info):
                framework = self._detect_framework(file_info)
                if framework != APIFramework.UNKNOWN:
                    frameworks_detected.add(framework)
                    
                    file_endpoints = self._extract_endpoints(file_info, framework)
                    endpoints.extend(file_endpoints)
                    
                    file_models = self._extract_models(file_info, framework)
                    models.extend(file_models)
        
        # Generate API documentation
        api_spec = self._generate_openapi_spec(endpoints, models, frameworks_detected)
        
        return {
            "endpoints": [self._endpoint_to_dict(ep) for ep in endpoints],
            "models": [self._model_to_dict(model) for model in models],
            "frameworks": [fw.value for fw in frameworks_detected],
            "openapi_spec": api_spec,
            "statistics": self._generate_api_statistics(endpoints, models)
        }
    
    def _is_api_file(self, file_info: Dict[str, Any]) -> bool:
        """Check if file contains API definitions."""
        content = file_info.get("content", "").lower()
        path = file_info.get("path", "").lower()
        
        # Check for API-related patterns
        api_patterns = [
            "@restcontroller", "@controller", "@requestmapping",
            "@app.route", "app.get", "app.post",
            "@router.", "fastapi", "apicontroller",
            "def get", "def post", "def put", "def delete",
            "router.get", "router.post", "express.router"
        ]
        
        if any(pattern in content for pattern in api_patterns):
            return True
        
        # Check path patterns
        if any(pattern in path for pattern in ["controller", "api", "route", "endpoint"]):
            return True
        
        return False
    def _detect_framework(self, file_info: Dict[str, Any]) -> APIFramework:
        """Detect API framework used in the file."""
        content = file_info.get("content", "")
        
        for framework, detector in self.framework_detectors.items():
            if detector(content):
                return framework
        
        return APIFramework.UNKNOWN
    
    def _detect_spring_boot(self, content: str) -> bool:
        """Detect Spring Boot framework."""
        patterns = [
            "@RestController", "@Controller", "@RequestMapping",
            "@GetMapping", "@PostMapping", "@PutMapping", "@DeleteMapping",
            "org.springframework"
        ]
        return any(pattern in content for pattern in patterns)
    
    def _detect_flask(self, content: str) -> bool:
        """Detect Flask framework."""
        patterns = [
            "@app.route", "from flask import", "Flask(__name__)",
            "request.json", "jsonify"
        ]
        return any(pattern in content for pattern in patterns)
    
    def _detect_fastapi(self, content: str) -> bool:
        """Detect FastAPI framework."""
        patterns = [
            "from fastapi import", "FastAPI()", "@app.get", "@app.post",
            "APIRouter", "Depends", "HTTPException"
        ]
        return any(pattern in content for pattern in patterns)
    
    def _detect_express(self, content: str) -> bool:
        """Detect Express.js framework."""
        patterns = [
            "express()", "app.get", "app.post", "router.get",
            "require('express')", "import express"
        ]
        return any(pattern in content for pattern in patterns)
    
    def _detect_asp_net(self, content: str) -> bool:
        """Detect ASP.NET framework."""
        patterns = [
            "[ApiController]", "[Route", "[HttpGet]", "[HttpPost]",
            "Microsoft.AspNetCore", "ControllerBase"
        ]
        return any(pattern in content for pattern in patterns)
    
    def _detect_django(self, content: str) -> bool:
        """Detect Django framework."""
        patterns = [
            "from django", "django.http", "HttpResponse",
            "path(", "url(", "views.py"
        ]
        return any(pattern in content for pattern in patterns)
    
    def _extract_endpoints(self, file_info: Dict[str, Any], framework: APIFramework) -> List[APIEndpoint]:
        """Extract API endpoints from file based on framework."""
        content = file_info.get("content", "")
        file_path = file_info.get("path", "")
        
        if framework == APIFramework.SPRING_BOOT:
            return self._extract_spring_endpoints(content, file_path)
        elif framework == APIFramework.FLASK:
            return self._extract_flask_endpoints(content, file_path)
        elif framework == APIFramework.FASTAPI:
            return self._extract_fastapi_endpoints(content, file_path)
        elif framework == APIFramework.EXPRESS:
            return self._extract_express_endpoints(content, file_path)
        elif framework == APIFramework.ASP_NET:
            return self._extract_aspnet_endpoints(content, file_path)
        elif framework == APIFramework.DJANGO:
            return self._extract_django_endpoints(content, file_path)
        
        return []
    
    def _extract_spring_endpoints(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Extract Spring Boot endpoints."""
        endpoints = []
        lines = content.split('\n')
        
        # Find class-level RequestMapping
        class_path = ""
        class_mapping_match = re.search(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']', content)
        if class_mapping_match:
            class_path = class_mapping_match.group(1)
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for mapping annotations
            mapping_match = re.match(r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*\(([^)]*)\)', line)
            if mapping_match:
                method_type = mapping_match.group(1).upper()
                if method_type == "REQUEST":
                    method_type = "GET"  # Default for RequestMapping
                
                mapping_params = mapping_match.group(2)
                
                # Extract path
                path_match = re.search(r'["\']([^"\']+)["\']', mapping_params)
                endpoint_path = path_match.group(1) if path_match else ""
                full_path = (class_path + endpoint_path).replace('//', '/')
                
                # Find the method definition
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('public'):
                    i += 1
                
                if i < len(lines):
                    method_line = lines[i].strip()
                    method_match = re.search(r'public\s+\w+\s+(\w+)\s*\(([^)]*)\)', method_line)
                    if method_match:
                        function_name = method_match.group(1)
                        params_str = method_match.group(2)
                        
                        # Parse parameters
                        parameters = self._parse_spring_parameters(params_str)
                        
                        # Create endpoint
                        endpoint = APIEndpoint(
                            path=full_path,
                            method=HTTPMethod(method_type),
                            function_name=function_name,
                            parameters=parameters,
                            responses=[Response(200, "Success")],
                            file_path=file_path,
                            line_number=i + 1
                        )
                        endpoints.append(endpoint)
            
            i += 1
        
        return endpoints
    
    def _extract_flask_endpoints(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Extract Flask endpoints."""
        endpoints = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for @app.route decorators
            route_match = re.match(r'@app\.route\s*\(\s*["\']([^"\']+)["\'](?:,\s*methods\s*=\s*\[([^\]]+)\])?\)', line)
            if route_match:
                path = route_match.group(1)
                methods_str = route_match.group(2) if route_match.group(2) else '"GET"'
                methods = [m.strip().strip('"\'') for m in methods_str.split(',')]
                
                # Find the function definition
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('def '):
                    j += 1
                
                if j < len(lines):
                    func_line = lines[j].strip()
                    func_match = re.match(r'def\s+(\w+)\s*\(([^)]*)\):', func_line)
                    if func_match:
                        function_name = func_match.group(1)
                        params_str = func_match.group(2)
                        
                        # Parse parameters
                        parameters = self._parse_flask_parameters(params_str, path)
                        
                        # Create endpoints for each method
                        for method in methods:
                            endpoint = APIEndpoint(
                                path=path,
                                method=HTTPMethod(method.upper()),
                                function_name=function_name,
                                parameters=parameters,
                                responses=[Response(200, "Success")],
                                file_path=file_path,
                                line_number=j + 1
                            )
                            endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_fastapi_endpoints(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Extract FastAPI endpoints."""
        endpoints = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for @app.method or @router.method decorators
            method_match = re.match(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', line)
            if method_match:
                method = method_match.group(1).upper()
                path = method_match.group(2)
                
                # Find the function definition
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('def ') and not lines[j].strip().startswith('async def '):
                    j += 1
                
                if j < len(lines):
                    func_line = lines[j].strip()
                    func_match = re.match(r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\):', func_line)
                    if func_match:
                        function_name = func_match.group(1)
                        params_str = func_match.group(2)
                        
                        # Parse parameters
                        parameters = self._parse_fastapi_parameters(params_str, path)
                        
                        endpoint = APIEndpoint(
                            path=path,
                            method=HTTPMethod(method),
                            function_name=function_name,
                            parameters=parameters,
                            responses=[Response(200, "Success")],
                            file_path=file_path,
                            line_number=j + 1
                        )
                        endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_express_endpoints(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Extract Express.js endpoints."""
        endpoints = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for app.method or router.method calls
            method_match = re.match(r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', line)
            if method_match:
                method = method_match.group(1).upper()
                path = method_match.group(2)
                
                # Extract function name or inline function
                function_name = f"{method.lower()}_{path.replace('/', '_').replace(':', '')}"
                
                # Parse path parameters
                path_params = re.findall(r':(\w+)', path)
                parameters = [
                    Parameter(name=param, type="string", location="path")
                    for param in path_params
                ]
                
                endpoint = APIEndpoint(
                    path=path,
                    method=HTTPMethod(method),
                    function_name=function_name,
                    parameters=parameters,
                    responses=[Response(200, "Success")],
                    file_path=file_path,
                    line_number=i + 1
                )
                endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_aspnet_endpoints(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Extract ASP.NET endpoints."""
        endpoints = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for HTTP method attributes
            method_match = re.match(r'\[Http(Get|Post|Put|Delete|Patch)\s*(?:\(\s*["\']([^"\']*)["\']?\s*\))?\]', line)
            if method_match:
                method = method_match.group(1).upper()
                path = method_match.group(2) if method_match.group(2) else ""
                
                # Find the method definition
                i += 1
                while i < len(lines) and not re.match(r'public\s+\w+\s+\w+\s*\(', lines[i].strip()):
                    i += 1
                
                if i < len(lines):
                    method_line = lines[i].strip()
                    method_def_match = re.search(r'public\s+\w+\s+(\w+)\s*\(([^)]*)\)', method_line)
                    if method_def_match:
                        function_name = method_def_match.group(1)
                        params_str = method_def_match.group(2)
                        
                        # Parse parameters
                        parameters = self._parse_aspnet_parameters(params_str)
                        
                        endpoint = APIEndpoint(
                            path=path,
                            method=HTTPMethod(method),
                            function_name=function_name,
                            parameters=parameters,
                            responses=[Response(200, "Success")],
                            file_path=file_path,
                            line_number=i + 1
                        )
                        endpoints.append(endpoint)
            
            i += 1
        
        return endpoints
    
    def _extract_django_endpoints(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Extract Django endpoints."""
        endpoints = []
        
        # Django URL patterns are typically in urls.py files
        if "urls.py" in file_path:
            # Extract URL patterns
            pattern_matches = re.findall(r'path\s*\(\s*["\']([^"\']+)["\'].*?(\w+)', content)
            for path, view_name in pattern_matches:
                endpoint = APIEndpoint(
                    path=path,
                    method=HTTPMethod.GET,  # Default, would need view analysis for actual methods
                    function_name=view_name,
                    parameters=[],
                    responses=[Response(200, "Success")],
                    file_path=file_path,
                    line_number=0
                )
                endpoints.append(endpoint)
        
        return endpoints
    def _parse_spring_parameters(self, params_str: str) -> List[Parameter]:
        """Parse Spring Boot method parameters."""
        parameters = []
        if not params_str.strip():
            return parameters
        
        # Split parameters by comma, handling nested generics
        param_parts = self._split_parameters(params_str)
        
        for param in param_parts:
            param = param.strip()
            if not param:
                continue
            
            # Check for annotations
            if "@RequestParam" in param:
                param_match = re.search(r'@RequestParam(?:\([^)]*\))?\s+(\w+)\s+(\w+)', param)
                if param_match:
                    param_type = param_match.group(1)
                    param_name = param_match.group(2)
                    parameters.append(Parameter(
                        name=param_name,
                        type=param_type,
                        location="query"
                    ))
            elif "@PathVariable" in param:
                param_match = re.search(r'@PathVariable(?:\([^)]*\))?\s+(\w+)\s+(\w+)', param)
                if param_match:
                    param_type = param_match.group(1)
                    param_name = param_match.group(2)
                    parameters.append(Parameter(
                        name=param_name,
                        type=param_type,
                        location="path"
                    ))
            elif "@RequestBody" in param:
                param_match = re.search(r'@RequestBody\s+(\w+)\s+(\w+)', param)
                if param_match:
                    param_type = param_match.group(1)
                    param_name = param_match.group(2)
                    parameters.append(Parameter(
                        name=param_name,
                        type=param_type,
                        location="body"
                    ))
        
        return parameters
    
    def _parse_flask_parameters(self, params_str: str, path: str) -> List[Parameter]:
        """Parse Flask function parameters."""
        parameters = []
        
        # Extract path parameters from route
        path_params = re.findall(r'<(?:(\w+):)?(\w+)>', path)
        for type_hint, param_name in path_params:
            param_type = type_hint if type_hint else "string"
            parameters.append(Parameter(
                name=param_name,
                type=param_type,
                location="path"
            ))
        
        return parameters
    
    def _parse_fastapi_parameters(self, params_str: str, path: str) -> List[Parameter]:
        """Parse FastAPI function parameters."""
        parameters = []
        if not params_str.strip():
            return parameters
        
        # Extract path parameters from route
        path_params = re.findall(r'{(\w+)}', path)
        path_param_names = set(path_params)
        
        # Split parameters
        param_parts = self._split_parameters(params_str)
        
        for param in param_parts:
            param = param.strip()
            if not param or param == "self":
                continue
            
            # Parse parameter definition
            param_match = re.match(r'(\w+):\s*([^=]+)(?:\s*=\s*(.+))?', param)
            if param_match:
                param_name = param_match.group(1)
                param_type = param_match.group(2).strip()
                default_value = param_match.group(3)
                
                # Determine parameter location
                location = "path" if param_name in path_param_names else "query"
                
                # Handle special FastAPI types
                if "Body(" in param_type or "Request" in param_type:
                    location = "body"
                elif "Header(" in param_type:
                    location = "header"
                
                parameters.append(Parameter(
                    name=param_name,
                    type=param_type,
                    location=location,
                    required=default_value is None,
                    default_value=default_value
                ))
        
        return parameters
    
    def _parse_aspnet_parameters(self, params_str: str) -> List[Parameter]:
        """Parse ASP.NET method parameters."""
        parameters = []
        if not params_str.strip():
            return parameters
        
        param_parts = self._split_parameters(params_str)
        
        for param in param_parts:
            param = param.strip()
            if not param:
                continue
            
            # Check for attributes
            if "[FromQuery]" in param:
                param_match = re.search(r'\[FromQuery\]\s+(\w+)\s+(\w+)', param)
                if param_match:
                    param_type = param_match.group(1)
                    param_name = param_match.group(2)
                    parameters.append(Parameter(
                        name=param_name,
                        type=param_type,
                        location="query"
                    ))
            elif "[FromRoute]" in param:
                param_match = re.search(r'\[FromRoute\]\s+(\w+)\s+(\w+)', param)
                if param_match:
                    param_type = param_match.group(1)
                    param_name = param_match.group(2)
                    parameters.append(Parameter(
                        name=param_name,
                        type=param_type,
                        location="path"
                    ))
            elif "[FromBody]" in param:
                param_match = re.search(r'\[FromBody\]\s+(\w+)\s+(\w+)', param)
                if param_match:
                    param_type = param_match.group(1)
                    param_name = param_match.group(2)
                    parameters.append(Parameter(
                        name=param_name,
                        type=param_type,
                        location="body"
                    ))
            else:
                # Simple parameter without attributes
                param_match = re.match(r'(\w+)\s+(\w+)', param)
                if param_match:
                    param_type = param_match.group(1)
                    param_name = param_match.group(2)
                    parameters.append(Parameter(
                        name=param_name,
                        type=param_type,
                        location="query"
                    ))
        
        return parameters
    
    def _split_parameters(self, params_str: str) -> List[str]:
        """Split parameter string by commas, handling nested brackets."""
        parameters = []
        current_param = ""
        bracket_count = 0
        paren_count = 0
        
        for char in params_str:
            if char == ',' and bracket_count == 0 and paren_count == 0:
                parameters.append(current_param.strip())
                current_param = ""
            else:
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                elif char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                current_param += char
        
        if current_param.strip():
            parameters.append(current_param.strip())
        
        return parameters
    
    def _extract_models(self, file_info: Dict[str, Any], framework: APIFramework) -> List[APIModel]:
        """Extract API data models from file."""
        content = file_info.get("content", "")
        models = []
        
        # Look for class definitions that might be data models
        class_matches = re.finditer(r'class\s+(\w+).*?{(.*?)}', content, re.DOTALL)
        
        for match in class_matches:
            class_name = match.group(1)
            class_body = match.group(2)
            
            # Skip if it's clearly not a data model
            if any(keyword in class_body.lower() for keyword in ['controller', 'service', 'repository']):
                continue
            
            # Extract properties
            properties = {}
            required_fields = []
            
            # Different patterns for different languages
            if framework in [APIFramework.SPRING_BOOT, APIFramework.ASP_NET]:
                # Java/C# style properties
                prop_matches = re.finditer(r'(?:public|private)\s+(\w+)\s+(\w+)', class_body)
                for prop_match in prop_matches:
                    prop_type = prop_match.group(1)
                    prop_name = prop_match.group(2)
                    properties[prop_name] = {"type": prop_type}
            
            elif framework in [APIFramework.FLASK, APIFramework.FASTAPI, APIFramework.DJANGO]:
                # Python style properties (simplified)
                prop_matches = re.finditer(r'(\w+):\s*([^=\n]+)', class_body)
                for prop_match in prop_matches:
                    prop_name = prop_match.group(1)
                    prop_type = prop_match.group(2).strip()
                    properties[prop_name] = {"type": prop_type}
            
            if properties:
                model = APIModel(
                    name=class_name,
                    properties=properties,
                    required_fields=required_fields
                )
                models.append(model)
        
        return models
    
    def _generate_openapi_spec(self, endpoints: List[APIEndpoint], models: List[APIModel], frameworks: set) -> Dict[str, Any]:
        """Generate OpenAPI specification from extracted endpoints and models."""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Generated API Documentation",
                "version": "1.0.0",
                "description": f"API documentation generated from {', '.join([fw.value for fw in frameworks])} code"
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        
        # Add endpoints to paths
        for endpoint in endpoints:
            if endpoint.path not in spec["paths"]:
                spec["paths"][endpoint.path] = {}
            
            method_spec = {
                "summary": endpoint.summary or f"{endpoint.method.value} {endpoint.path}",
                "description": endpoint.description or f"Endpoint: {endpoint.function_name}",
                "parameters": [],
                "responses": {}
            }
            
            # Add parameters
            for param in endpoint.parameters:
                param_spec = {
                    "name": param.name,
                    "in": param.location,
                    "required": param.required,
                    "schema": {"type": self._map_type_to_openapi(param.type)}
                }
                if param.description:
                    param_spec["description"] = param.description
                method_spec["parameters"].append(param_spec)
            
            # Add responses
            for response in endpoint.responses:
                method_spec["responses"][str(response.status_code)] = {
                    "description": response.description,
                    "content": {
                        response.content_type: {
                            "schema": response.schema or {"type": "object"}
                        }
                    }
                }
            
            spec["paths"][endpoint.path][endpoint.method.value.lower()] = method_spec
        
        # Add models to components
        for model in models:
            schema = {
                "type": "object",
                "properties": {},
                "required": model.required_fields
            }
            
            for prop_name, prop_info in model.properties.items():
                schema["properties"][prop_name] = {
                    "type": self._map_type_to_openapi(prop_info["type"])
                }
            
            spec["components"]["schemas"][model.name] = schema
        
        return spec
    
    def _map_type_to_openapi(self, type_str: str) -> str:
        """Map programming language types to OpenAPI types."""
        type_mapping = {
            # Java types
            "String": "string",
            "Integer": "integer",
            "Long": "integer",
            "Boolean": "boolean",
            "Double": "number",
            "Float": "number",
            "Date": "string",
            "LocalDateTime": "string",
            
            # Python types
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "datetime": "string",
            "list": "array",
            "dict": "object",
            
            # C# types
            "string": "string",
            "int": "integer",
            "long": "integer",
            "bool": "boolean",
            "double": "number",
            "decimal": "number",
            "DateTime": "string",
            
            # JavaScript types
            "string": "string",
            "number": "number",
            "boolean": "boolean",
            "object": "object",
            "array": "array"
        }
        
        # Handle generic types
        if "<" in type_str:
            base_type = type_str.split("<")[0]
            if base_type.lower() in ["list", "array"]:
                return "array"
            elif base_type.lower() in ["map", "dict", "object"]:
                return "object"
        
        return type_mapping.get(type_str, "string")
    
    def _endpoint_to_dict(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """Convert endpoint to dictionary."""
        return {
            "path": endpoint.path,
            "method": endpoint.method.value,
            "function_name": endpoint.function_name,
            "parameters": [self._parameter_to_dict(p) for p in endpoint.parameters],
            "responses": [self._response_to_dict(r) for r in endpoint.responses],
            "summary": endpoint.summary,
            "description": endpoint.description,
            "tags": endpoint.tags or [],
            "deprecated": endpoint.deprecated,
            "security": endpoint.security,
            "file_path": endpoint.file_path,
            "line_number": endpoint.line_number
        }
    
    def _parameter_to_dict(self, parameter: Parameter) -> Dict[str, Any]:
        """Convert parameter to dictionary."""
        return {
            "name": parameter.name,
            "type": parameter.type,
            "required": parameter.required,
            "location": parameter.location,
            "description": parameter.description,
            "default_value": parameter.default_value,
            "validation": parameter.validation
        }
    
    def _response_to_dict(self, response: Response) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "status_code": response.status_code,
            "description": response.description,
            "content_type": response.content_type,
            "schema": response.schema,
            "examples": response.examples
        }
    
    def _model_to_dict(self, model: APIModel) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "name": model.name,
            "properties": model.properties,
            "required_fields": model.required_fields,
            "description": model.description,
            "example": model.example
        }
    
    def _generate_api_statistics(self, endpoints: List[APIEndpoint], models: List[APIModel]) -> Dict[str, Any]:
        """Generate API statistics."""
        method_counts = {}
        for endpoint in endpoints:
            method = endpoint.method.value
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            "total_endpoints": len(endpoints),
            "total_models": len(models),
            "methods_distribution": method_counts,
            "unique_paths": len(set(ep.path for ep in endpoints)),
            "parameters_total": sum(len(ep.parameters) for ep in endpoints),
            "avg_parameters_per_endpoint": sum(len(ep.parameters) for ep in endpoints) / len(endpoints) if endpoints else 0
        }


class APIConverter:
    """Main API conversion service."""
    
    def __init__(self):
        self.extractor = APIExtractor()
    
    def convert_api_files(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert API files to comprehensive API documentation."""
        try:
            # Extract API information
            api_info = self.extractor.extract_api_info(files)
            
            # Generate additional documentation
            postman_collection = self._generate_postman_collection(api_info["endpoints"])
            curl_examples = self._generate_curl_examples(api_info["endpoints"])
            
            return {
                **api_info,
                "postman_collection": postman_collection,
                "curl_examples": curl_examples,
                "conversion_summary": self._generate_conversion_summary(api_info)
            }
            
        except Exception as e:
            logger.error(f"Error converting API files: {e}")
            return {
                "error": str(e),
                "endpoints": [],
                "models": [],
                "frameworks": [],
                "openapi_spec": {},
                "statistics": {}
            }
    
    def _generate_postman_collection(self, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate Postman collection from endpoints."""
        collection = {
            "info": {
                "name": "Generated API Collection",
                "description": "Auto-generated from source code",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        
        for endpoint in endpoints:
            item = {
                "name": f"{endpoint['method']} {endpoint['path']}",
                "request": {
                    "method": endpoint["method"],
                    "header": [],
                    "url": {
                        "raw": f"{{{{base_url}}}}{endpoint['path']}",
                        "host": ["{{base_url}}"],
                        "path": endpoint["path"].strip("/").split("/") if endpoint["path"] != "/" else []
                    }
                }
            }
            
            # Add query parameters
            query_params = [p for p in endpoint["parameters"] if p["location"] == "query"]
            if query_params:
                item["request"]["url"]["query"] = [
                    {"key": p["name"], "value": f"{{{{{p['name']}}}}}", "description": p.get("description", "")}
                    for p in query_params
                ]
            
            # Add body for POST/PUT requests
            if endpoint["method"] in ["POST", "PUT", "PATCH"]:
                body_params = [p for p in endpoint["parameters"] if p["location"] == "body"]
                if body_params:
                    item["request"]["body"] = {
                        "mode": "raw",
                        "raw": "{\n  // Add request body here\n}",
                        "options": {
                            "raw": {
                                "language": "json"
                            }
                        }
                    }
            
            collection["item"].append(item)
        
        return collection
    
    def _generate_curl_examples(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate cURL examples for endpoints."""
        examples = []
        
        for endpoint in endpoints:
            curl_cmd = f"curl -X {endpoint['method']} \\\n"
            curl_cmd += f"  '{endpoint['path']}'"
            
            # Add headers
            if endpoint["method"] in ["POST", "PUT", "PATCH"]:
                curl_cmd += " \\\n  -H 'Content-Type: application/json'"
            
            # Add query parameters
            query_params = [p for p in endpoint["parameters"] if p["location"] == "query"]
            if query_params:
                params = "&".join([f"{p['name']}={{value}}" for p in query_params])
                curl_cmd = curl_cmd.replace(endpoint["path"], f"{endpoint['path']}?{params}")
            
            # Add body
            if endpoint["method"] in ["POST", "PUT", "PATCH"]:
                curl_cmd += " \\\n  -d '{\n    // Add request body here\n  }'"
            
            examples.append({
                "endpoint": f"{endpoint['method']} {endpoint['path']}",
                "curl": curl_cmd
            })
        
        return examples
    
    def _generate_conversion_summary(self, api_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate conversion summary."""
        return {
            "endpoints_converted": len(api_info["endpoints"]),
            "models_extracted": len(api_info["models"]),
            "frameworks_detected": api_info["frameworks"],
            "openapi_generated": bool(api_info["openapi_spec"]),
            "postman_collection_generated": True,
            "curl_examples_generated": True
        }