"""Analysis Agent for Deep Code Analysis."""

import logging
from typing import Any, Dict, List

from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq

from .base_agent import BaseCodeMorphAgent, AgentResult
from .tools.code_analysis_tools import (
    ASTAnalysisTool,
    ComplexityAnalysisTool,
    DependencyGraphTool,
    PatternDetectionTool,
    SecurityAnalysisTool
)

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseCodeMorphAgent):
    """Agent for comprehensive code analysis."""
    
    def __init__(self, llm: ChatGroq = None):
        super().__init__(
            name="AnalysisAgent",
            description="Performs deep code analysis including AST parsing, complexity metrics, dependency graphs, pattern detection, and security analysis",
            llm=llm,
            temperature=0.1,
            max_iterations=15
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the analysis agent."""
        return """You are an expert code analysis agent specializing in comprehensive codebase analysis.

Your capabilities include:
1. AST (Abstract Syntax Tree) parsing and analysis
2. Code complexity metrics calculation
3. Dependency graph construction and analysis
4. Design pattern and anti-pattern detection
5. Security vulnerability assessment
6. Code quality scoring and recommendations

When analyzing code, you should:
- Use multiple analysis tools to get comprehensive insights
- Provide confidence scores for your findings
- Identify both strengths and weaknesses in the code
- Suggest specific improvements
- Consider the broader architectural context
- Flag security concerns and technical debt

Always structure your analysis with:
- Executive summary
- Detailed findings per analysis type
- Confidence scores and reasoning
- Prioritized recommendations
- Risk assessment

Be thorough but concise. Focus on actionable insights that will help with code modernization and improvement."""
    
    def _get_default_tools(self) -> List[BaseTool]:
        """Get default tools for the analysis agent."""
        return [
            ASTAnalysisTool(),
            ComplexityAnalysisTool(),
            DependencyGraphTool(),
            PatternDetectionTool(),
            SecurityAnalysisTool()
        ]
    
    def _format_input(self, input_data: Dict[str, Any]) -> str:
        """Format input data for the analysis agent."""
        files = input_data.get("files", [])
        project_context = input_data.get("project_context", {})
        analysis_type = input_data.get("analysis_type", "comprehensive")
        
        prompt = f"""Analyze the following codebase for comprehensive insights:

Analysis Type: {analysis_type}

Project Context:
- Name: {project_context.get('name', 'Unknown')}
- Language Distribution: {project_context.get('language_distribution', {})}
- Total Files: {len(files)}
- Total LOC: {project_context.get('total_loc', 0)}

Files to Analyze:
"""
        
        for i, file_info in enumerate(files[:10]):  # Limit to first 10 files for prompt
            prompt += f"""
File {i+1}: {file_info.get('path', 'unknown')}
- Language: {file_info.get('language', 'unknown')}
- Size: {file_info.get('size', 0)} bytes
- LOC: {file_info.get('loc', 0)}
"""
            
            # Include code content for smaller files
            content = file_info.get('content', '')
            if content and len(content) < 2000:
                prompt += f"Content:\n```{file_info.get('language', '')}\n{content[:1500]}...\n```\n"
        
        if len(files) > 10:
            prompt += f"\n... and {len(files) - 10} more files"
        
        prompt += """

Please perform a comprehensive analysis using your available tools. Focus on:
1. Code structure and organization
2. Complexity and maintainability metrics
3. Dependency relationships and architecture
4. Design patterns and code quality
5. Security vulnerabilities and risks
6. Recommendations for improvement and modernization

Provide detailed findings with confidence scores and actionable recommendations."""
        
        return prompt
    
    async def analyze_single_file(
        self,
        file_path: str,
        content: str,
        language: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Analyze a single file in detail."""
        input_data = {
            "files": [{
                "path": file_path,
                "content": content,
                "language": language,
                "size": len(content.encode('utf-8')),
                "loc": len(content.split('\n'))
            }],
            "project_context": context or {},
            "analysis_type": "single_file"
        }
        
        return await self.execute(input_data, context)
    
    async def analyze_architecture(
        self,
        files: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Analyze overall architecture and dependencies."""
        input_data = {
            "files": files,
            "project_context": context or {},
            "analysis_type": "architecture"
        }
        
        return await self.execute(input_data, context)
    
    async def analyze_security(
        self,
        files: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Focus on security analysis."""
        input_data = {
            "files": files,
            "project_context": context or {},
            "analysis_type": "security"
        }
        
        return await self.execute(input_data, context)
    
    async def analyze_quality(
        self,
        files: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Focus on code quality metrics."""
        input_data = {
            "files": files,
            "project_context": context or {},
            "analysis_type": "quality"
        }
        
        return await self.execute(input_data, context)
    
    def _extract_confidence(
        self,
        output: Dict[str, Any],
        intermediate_steps: List[Any]
    ) -> float:
        """Extract confidence score from analysis results."""
        # Calculate confidence based on successful tool executions
        successful_tools = 0
        total_tools = len(self.tools)
        
        for step in intermediate_steps:
            if hasattr(step, 'observation') and 'error' not in str(step.observation).lower():
                successful_tools += 1
        
        base_confidence = successful_tools / total_tools if total_tools > 0 else 0.5
        
        # Adjust based on output quality
        if isinstance(output, dict):
            if output.get('analysis_complete', False):
                base_confidence += 0.2
            if output.get('recommendations'):
                base_confidence += 0.1
            if output.get('security_issues'):
                base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _extract_reasoning(
        self,
        output: Dict[str, Any],
        intermediate_steps: List[Any]
    ) -> str:
        """Extract reasoning from analysis results."""
        reasoning_parts = []
        
        # Add tool execution summary
        tool_results = {}
        for step in intermediate_steps:
            if hasattr(step, 'action') and hasattr(step, 'observation'):
                tool_name = step.action.tool
                success = 'error' not in str(step.observation).lower()
                tool_results[tool_name] = success
        
        successful_tools = [name for name, success in tool_results.items() if success]
        failed_tools = [name for name, success in tool_results.items() if not success]
        
        if successful_tools:
            reasoning_parts.append(f"Successfully executed tools: {', '.join(successful_tools)}")
        if failed_tools:
            reasoning_parts.append(f"Failed tools: {', '.join(failed_tools)}")
        
        # Add analysis summary
        if isinstance(output, dict):
            if output.get('summary'):
                reasoning_parts.append(f"Analysis summary: {output['summary']}")
            if output.get('key_findings'):
                reasoning_parts.append(f"Key findings: {len(output['key_findings'])} items identified")
        
        return " | ".join(reasoning_parts) if reasoning_parts else "Analysis completed with available tools"