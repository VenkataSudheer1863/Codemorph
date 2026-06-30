"""Enhanced Chunking Strategy for CodeMorph."""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import ast

logger = logging.getLogger(__name__)


class ChunkType(Enum):
    """Types of code chunks."""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    IMPORT = "import"
    COMMENT = "comment"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    TEST = "test"


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata."""
    id: str
    content: str
    chunk_type: ChunkType
    language: str
    file_path: str
    start_line: int
    end_line: int
    size: int
    complexity_score: float
    dependencies: List[str]
    metadata: Dict[str, Any]


class EnhancedChunkingStrategy:
    """Enhanced chunking strategy with semantic awareness."""
    
    def __init__(self, max_chunk_size: int = 2000, overlap_size: int = 200):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        
    def chunk_codebase(
        self,
        files: List[Dict[str, Any]],
        parse_results: List[Dict[str, Any]]
    ) -> List[CodeChunk]:
        """Chunk entire codebase with semantic awareness."""
        all_chunks = []
        
        for i, file_info in enumerate(files):
            file_path = file_info.get("path", f"file_{i}")
            content = file_info.get("content", "")
            language = file_info.get("language", "unknown")
            
            parse_result = parse_results[i] if i < len(parse_results) else {}
            
            # Chunk individual file
            file_chunks = self.chunk_file(
                content=content,
                file_path=file_path,
                language=language,
                parse_result=parse_result
            )
            
            all_chunks.extend(file_chunks)
        
        # Post-process chunks for optimization
        optimized_chunks = self._optimize_chunks(all_chunks)
        
        return optimized_chunks
    
    def chunk_file(
        self,
        content: str,
        file_path: str,
        language: str,
        parse_result: Dict[str, Any]
    ) -> List[CodeChunk]:
        """Chunk a single file with semantic boundaries."""
        chunks = []
        
        if language.lower() in ['python', 'py']:
            chunks = self._chunk_python_file(content, file_path, parse_result)
        elif language.lower() in ['java']:
            chunks = self._chunk_java_file(content, file_path, parse_result)
        elif language.lower() in ['javascript', 'js', 'typescript', 'ts']:
            chunks = self._chunk_javascript_file(content, file_path, parse_result)
        else:
            # Generic chunking for unknown languages
            chunks = self._chunk_generic_file(content, file_path, language)
        
        return chunks
    
    def _chunk_python_file(
        self,
        content: str,
        file_path: str,
        parse_result: Dict[str, Any]
    ) -> List[CodeChunk]:
        """Chunk Python file using AST analysis."""
        chunks = []
        lines = content.split('\n')
        
        try:
            tree = ast.parse(content)
            
            # Extract imports
            imports_chunk = self._extract_imports_chunk(tree, lines, file_path)
            if imports_chunk:
                chunks.append(imports_chunk)
            
            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_chunk = self._extract_class_chunk(
                        node, lines, file_path, parse_result
                    )
                    chunks.append(class_chunk)
                
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    # Top-level functions only
                    func_chunk = self._extract_function_chunk(
                        node, lines, file_path, parse_result
                    )
                    chunks.append(func_chunk)
            
            # Handle remaining content
            covered_lines = set()
            for chunk in chunks:
                covered_lines.update(range(chunk.start_line, chunk.end_line + 1))
            
            uncovered_lines = [i for i in range(len(lines)) if i not in covered_lines]
            if uncovered_lines:
                remaining_chunks = self._chunk_remaining_content(
                    uncovered_lines, lines, file_path, "python"
                )
                chunks.extend(remaining_chunks)
        
        except SyntaxError:
            # Fallback to generic chunking
            chunks = self._chunk_generic_file(content, file_path, "python")
        
        return chunks
    
    def _extract_imports_chunk(
        self,
        tree: ast.AST,
        lines: List[str],
        file_path: str
    ) -> Optional[CodeChunk]:
        """Extract imports as a single chunk."""
        import_lines = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_lines.append(node.lineno - 1)  # Convert to 0-based
        
        if not import_lines:
            return None
        
        start_line = min(import_lines)
        end_line = max(import_lines)
        
        # Include docstring if it comes before imports
        if start_line > 0 and '"""' in lines[0]:
            start_line = 0
        
        content = '\n'.join(lines[start_line:end_line + 1])
        
        return CodeChunk(
            id=f"{file_path}:imports",
            content=content,
            chunk_type=ChunkType.IMPORT,
            language="python",
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            size=len(content),
            complexity_score=1.0,
            dependencies=[],
            metadata={"import_count": len(import_lines)}
        )
    
    def _extract_class_chunk(
        self,
        node: ast.ClassDef,
        lines: List[str],
        file_path: str,
        parse_result: Dict[str, Any]
    ) -> CodeChunk:
        """Extract class as a chunk."""
        start_line = node.lineno - 1
        end_line = self._find_node_end_line(node, lines)
        
        content = '\n'.join(lines[start_line:end_line + 1])
        
        # Find class info from parse results
        class_info = None
        for cls in parse_result.get("classes", []):
            if cls["name"] == node.name:
                class_info = cls
                break
        
        dependencies = self._extract_dependencies_from_content(content)
        complexity_score = self._calculate_complexity_score(content, "class")
        
        return CodeChunk(
            id=f"{file_path}:class:{node.name}",
            content=content,
            chunk_type=ChunkType.CLASS,
            language="python",
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            size=len(content),
            complexity_score=complexity_score,
            dependencies=dependencies,
            metadata={
                "class_name": node.name,
                "method_count": len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
                "base_classes": [base.id for base in node.bases if isinstance(base, ast.Name)],
                "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
            }
        )
    
    def _extract_function_chunk(
        self,
        node: ast.FunctionDef,
        lines: List[str],
        file_path: str,
        parse_result: Dict[str, Any]
    ) -> CodeChunk:
        """Extract function as a chunk."""
        start_line = node.lineno - 1
        end_line = self._find_node_end_line(node, lines)
        
        content = '\n'.join(lines[start_line:end_line + 1])
        
        dependencies = self._extract_dependencies_from_content(content)
        complexity_score = self._calculate_complexity_score(content, "function")
        
        return CodeChunk(
            id=f"{file_path}:function:{node.name}",
            content=content,
            chunk_type=ChunkType.FUNCTION,
            language="python",
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            size=len(content),
            complexity_score=complexity_score,
            dependencies=dependencies,
            metadata={
                "function_name": node.name,
                "parameter_count": len(node.args.args),
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
            }
        )
    
    def _chunk_java_file(
        self,
        content: str,
        file_path: str,
        parse_result: Dict[str, Any]
    ) -> List[CodeChunk]:
        """Chunk Java file using regex patterns."""
        chunks = []
        lines = content.split('\n')
        
        # Extract package and imports
        package_imports = self._extract_java_package_imports(lines, file_path)
        if package_imports:
            chunks.append(package_imports)
        
        # Extract classes using regex
        class_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:abstract\s+)?(?:final\s+)?class\s+(\w+)'
        
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            class_name = match.group(1)
            start_pos = match.start()
            
            # Find class boundaries
            start_line = content[:start_pos].count('\n')
            end_line = self._find_java_class_end(content, start_pos)
            
            class_content = '\n'.join(lines[start_line:end_line + 1])
            
            chunks.append(CodeChunk(
                id=f"{file_path}:class:{class_name}",
                content=class_content,
                chunk_type=ChunkType.CLASS,
                language="java",
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                size=len(class_content),
                complexity_score=self._calculate_complexity_score(class_content, "class"),
                dependencies=self._extract_dependencies_from_content(class_content),
                metadata={"class_name": class_name}
            ))
        
        return chunks
    
    def _chunk_javascript_file(
        self,
        content: str,
        file_path: str,
        parse_result: Dict[str, Any]
    ) -> List[CodeChunk]:
        """Chunk JavaScript/TypeScript file."""
        chunks = []
        lines = content.split('\n')
        
        # Extract imports/requires
        import_lines = []
        for i, line in enumerate(lines):
            if re.match(r'^\s*(import|const.*require|from)', line.strip()):
                import_lines.append(i)
        
        if import_lines:
            start_line = min(import_lines)
            end_line = max(import_lines)
            import_content = '\n'.join(lines[start_line:end_line + 1])
            
            chunks.append(CodeChunk(
                id=f"{file_path}:imports",
                content=import_content,
                chunk_type=ChunkType.IMPORT,
                language="javascript",
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                size=len(import_content),
                complexity_score=1.0,
                dependencies=[],
                metadata={"import_count": len(import_lines)}
            ))
        
        # Extract functions and classes
        function_pattern = r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?\(|(\w+)\s*:\s*(?:async\s+)?function)'
        class_pattern = r'class\s+(\w+)'
        
        # Process functions
        for match in re.finditer(function_pattern, content, re.MULTILINE):
            func_name = match.group(1) or match.group(2) or match.group(3)
            if func_name:
                start_pos = match.start()
                start_line = content[:start_pos].count('\n')
                end_line = self._find_js_function_end(content, start_pos)
                
                func_content = '\n'.join(lines[start_line:end_line + 1])
                
                chunks.append(CodeChunk(
                    id=f"{file_path}:function:{func_name}",
                    content=func_content,
                    chunk_type=ChunkType.FUNCTION,
                    language="javascript",
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    size=len(func_content),
                    complexity_score=self._calculate_complexity_score(func_content, "function"),
                    dependencies=self._extract_dependencies_from_content(func_content),
                    metadata={"function_name": func_name}
                ))
        
        return chunks
    
    def _chunk_generic_file(
        self,
        content: str,
        file_path: str,
        language: str
    ) -> List[CodeChunk]:
        """Generic chunking for unknown file types."""
        chunks = []
        lines = content.split('\n')
        
        current_chunk_lines = []
        current_size = 0
        chunk_id = 0
        
        for i, line in enumerate(lines):
            current_chunk_lines.append(line)
            current_size += len(line) + 1  # +1 for newline
            
            # Check if we should create a chunk
            if (current_size >= self.max_chunk_size or 
                i == len(lines) - 1):
                
                chunk_content = '\n'.join(current_chunk_lines)
                
                chunks.append(CodeChunk(
                    id=f"{file_path}:chunk:{chunk_id}",
                    content=chunk_content,
                    chunk_type=ChunkType.MODULE,
                    language=language,
                    file_path=file_path,
                    start_line=i - len(current_chunk_lines) + 1,
                    end_line=i,
                    size=current_size,
                    complexity_score=self._calculate_complexity_score(chunk_content, "generic"),
                    dependencies=self._extract_dependencies_from_content(chunk_content),
                    metadata={"chunk_index": chunk_id}
                ))
                
                # Prepare for next chunk with overlap
                if i < len(lines) - 1:
                    overlap_lines = current_chunk_lines[-self.overlap_size//50:]  # Rough estimate
                    current_chunk_lines = overlap_lines
                    current_size = sum(len(line) + 1 for line in overlap_lines)
                else:
                    current_chunk_lines = []
                    current_size = 0
                
                chunk_id += 1
        
        return chunks
    
    def _optimize_chunks(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Optimize chunks for better processing."""
        optimized = []
        
        # Merge small chunks
        i = 0
        while i < len(chunks):
            current_chunk = chunks[i]
            
            # If chunk is too small, try to merge with next
            if (current_chunk.size < self.max_chunk_size // 4 and 
                i + 1 < len(chunks) and
                chunks[i + 1].file_path == current_chunk.file_path):
                
                next_chunk = chunks[i + 1]
                merged_chunk = self._merge_chunks(current_chunk, next_chunk)
                optimized.append(merged_chunk)
                i += 2  # Skip next chunk as it's merged
            else:
                optimized.append(current_chunk)
                i += 1
        
        return optimized
    
    def _merge_chunks(self, chunk1: CodeChunk, chunk2: CodeChunk) -> CodeChunk:
        """Merge two adjacent chunks."""
        merged_content = chunk1.content + '\n' + chunk2.content
        merged_dependencies = list(set(chunk1.dependencies + chunk2.dependencies))
        
        return CodeChunk(
            id=f"{chunk1.id}+{chunk2.id}",
            content=merged_content,
            chunk_type=chunk1.chunk_type,  # Use first chunk's type
            language=chunk1.language,
            file_path=chunk1.file_path,
            start_line=chunk1.start_line,
            end_line=chunk2.end_line,
            size=len(merged_content),
            complexity_score=(chunk1.complexity_score + chunk2.complexity_score) / 2,
            dependencies=merged_dependencies,
            metadata={
                "merged_from": [chunk1.id, chunk2.id],
                **chunk1.metadata,
                **chunk2.metadata
            }
        )
    
    def _find_node_end_line(self, node: ast.AST, lines: List[str]) -> int:
        """Find the end line of an AST node."""
        # Simple heuristic: find the last line with content at the same indentation level
        start_line = node.lineno - 1
        base_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
        
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if line.strip():  # Non-empty line
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= base_indent and not line.strip().startswith(('"""', "'''")):
                    return i - 1
        
        return len(lines) - 1
    
    def _find_java_class_end(self, content: str, start_pos: int) -> int:
        """Find the end of a Java class."""
        brace_count = 0
        in_class = False
        
        for i, char in enumerate(content[start_pos:], start_pos):
            if char == '{':
                brace_count += 1
                in_class = True
            elif char == '}':
                brace_count -= 1
                if in_class and brace_count == 0:
                    return content[:i].count('\n')
        
        return content.count('\n')
    
    def _find_js_function_end(self, content: str, start_pos: int) -> int:
        """Find the end of a JavaScript function."""
        brace_count = 0
        in_function = False
        
        for i, char in enumerate(content[start_pos:], start_pos):
            if char == '{':
                brace_count += 1
                in_function = True
            elif char == '}':
                brace_count -= 1
                if in_function and brace_count == 0:
                    return content[:i].count('\n')
        
        return content.count('\n')
    
    def _extract_java_package_imports(self, lines: List[str], file_path: str) -> Optional[CodeChunk]:
        """Extract Java package and import statements."""
        package_line = None
        import_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('package '):
                package_line = i
            elif stripped.startswith('import '):
                import_lines.append(i)
        
        if package_line is not None or import_lines:
            start_line = package_line if package_line is not None else min(import_lines)
            end_line = max(import_lines) if import_lines else package_line
            
            content = '\n'.join(lines[start_line:end_line + 1])
            
            return CodeChunk(
                id=f"{file_path}:package_imports",
                content=content,
                chunk_type=ChunkType.IMPORT,
                language="java",
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                size=len(content),
                complexity_score=1.0,
                dependencies=[],
                metadata={
                    "has_package": package_line is not None,
                    "import_count": len(import_lines)
                }
            )
        
        return None
    
    def _chunk_remaining_content(
        self,
        uncovered_lines: List[int],
        lines: List[str],
        file_path: str,
        language: str
    ) -> List[CodeChunk]:
        """Chunk remaining uncovered content."""
        if not uncovered_lines:
            return []
        
        chunks = []
        current_group = []
        
        # Group consecutive lines
        for line_num in uncovered_lines:
            if not current_group or line_num == current_group[-1] + 1:
                current_group.append(line_num)
            else:
                # Process current group
                if current_group:
                    chunk = self._create_remaining_chunk(current_group, lines, file_path, language)
                    chunks.append(chunk)
                current_group = [line_num]
        
        # Process last group
        if current_group:
            chunk = self._create_remaining_chunk(current_group, lines, file_path, language)
            chunks.append(chunk)
        
        return chunks
    
    def _create_remaining_chunk(
        self,
        line_numbers: List[int],
        lines: List[str],
        file_path: str,
        language: str
    ) -> CodeChunk:
        """Create a chunk from remaining lines."""
        start_line = min(line_numbers)
        end_line = max(line_numbers)
        content = '\n'.join(lines[start_line:end_line + 1])
        
        return CodeChunk(
            id=f"{file_path}:remaining:{start_line}",
            content=content,
            chunk_type=ChunkType.MODULE,
            language=language,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            size=len(content),
            complexity_score=self._calculate_complexity_score(content, "remaining"),
            dependencies=self._extract_dependencies_from_content(content),
            metadata={"line_count": len(line_numbers)}
        )
    
    def _extract_dependencies_from_content(self, content: str) -> List[str]:
        """Extract dependencies from content."""
        dependencies = []
        
        # Simple regex-based extraction
        import_patterns = [
            r'import\s+([^\s;]+)',
            r'from\s+([^\s]+)\s+import',
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'#include\s*[<"]([^>"]+)[>"]'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            dependencies.extend(matches)
        
        return list(set(dependencies))
    
    def _calculate_complexity_score(self, content: str, chunk_type: str) -> float:
        """Calculate complexity score for content."""
        base_score = 1.0
        
        # Count complexity indicators
        complexity_indicators = [
            r'if\s+',
            r'for\s+',
            r'while\s+',
            r'try\s*{',
            r'catch\s*\(',
            r'switch\s*\(',
            r'case\s+',
            r'else\s+',
            r'elif\s+'
        ]
        
        for pattern in complexity_indicators:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            base_score += matches * 0.1
        
        # Adjust based on chunk type
        type_multipliers = {
            "function": 1.0,
            "class": 1.2,
            "generic": 0.8,
            "remaining": 0.5
        }
        
        multiplier = type_multipliers.get(chunk_type, 1.0)
        return min(base_score * multiplier, 10.0)  # Cap at 10.0