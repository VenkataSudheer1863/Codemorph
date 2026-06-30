"""Base Agent for CodeMorph Agentic System."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    data: Dict[str, Any]
    confidence: float
    reasoning: str
    errors: List[str]
    metadata: Dict[str, Any]


class CodeMorphCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for CodeMorph agents."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.steps = []

    def on_agent_action(self, action, **kwargs):
        logger.info(f"[{self.agent_name}] Action: {action.tool} - {action.tool_input}")
        self.steps.append({
            "type": "action",
            "tool": action.tool,
            "input": action.tool_input,
            "log": action.log
        })

    def on_agent_finish(self, finish, **kwargs):
        logger.info(f"[{self.agent_name}] Finished: {finish.return_values}")
        self.steps.append({
            "type": "finish",
            "output": finish.return_values
        })


class BaseCodeMorphAgent(ABC):
    """Base class for all CodeMorph agents."""

    def __init__(
        self,
        name: str,
        description: str,
        llm: Optional[ChatGroq] = None,
        tools: Optional[List[BaseTool]] = None,
        temperature: float = 0.1,
        max_iterations: int = 10
    ):
        self.name = name
        self.description = description
        self.temperature = temperature
        self.max_iterations = max_iterations

        if llm is None:
            raise ValueError(f"LLM must be provided for agent {name}")
        self.llm = llm

        self.tools = tools or []
        self.tools.extend(self._get_default_tools())

        self.callback_handler = CodeMorphCallbackHandler(self.name)

        # Bind tools to LLM if tools are available
        if self.tools:
            self._llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self._llm_with_tools = self.llm

        self._prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{input}"),
        ])

    @abstractmethod
    def _get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def _get_default_tools(self) -> List[BaseTool]:
        pass

    @abstractmethod
    def _format_input(self, input_data: Dict[str, Any]) -> str:
        pass

    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """Execute the agent with given input."""
        try:
            formatted_input = self._format_input(input_data)
            messages = self._prompt.format_messages(input=formatted_input)
            result = await self._llm_with_tools.ainvoke(messages)

            output = result.content if hasattr(result, "content") else str(result)
            return AgentResult(
                success=True,
                data={"output": output},
                confidence=0.8,
                reasoning=output if isinstance(output, str) else "Agent completed successfully",
                errors=[],
                metadata={"agent": self.name}
            )

        except Exception as e:
            logger.error(f"Agent {self.name} execution failed: {e}")
            return AgentResult(
                success=False,
                data={},
                confidence=0.0,
                reasoning=f"Agent execution failed: {str(e)}",
                errors=[str(e)],
                metadata={"agent": self.name}
            )

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "tools": [tool.name for tool in self.tools],
            "max_iterations": self.max_iterations,
            "temperature": self.temperature
        }
