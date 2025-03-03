import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START
from langgraph.types import Command

from state import GodotState
from config import (
    CODING_BEST_PRACTICES,
    PROJECT_STRUCTURE,
    DESIGN_CONSTRAINTS,
    KEY_MECHANICS
)

logger = logging.getLogger(__name__)

class InstructionNode:
    """
    Node responsible for holding the initial instructions,
    game premise, coding guidelines, etc.
    """
    def __init__(self, name: str):
        self.name = name
        logger.info(f"InstructionNode initialized: {name}")

    def __call__(self, state: GodotState):
        """Make node callable for LangGraph"""
        return self.invoke(state)

    def invoke(self, state: GodotState) -> Command[Literal["supervisor"]]:
        # Get the game premise from the input context
        game_premise = state.get("instructions", {}).get("game_premise", "")
        
        instructions = {
            "game_premise": game_premise,
            "coding_best_practices": CODING_BEST_PRACTICES,
            "project_structure": PROJECT_STRUCTURE,
            "design_constraints": DESIGN_CONSTRAINTS,
            "key_mechanics": KEY_MECHANICS
        }
        
        logger.info(f"Processed game premise: {game_premise[:50]}...")
        # Return updated state with the instructions
        return Command(
            update={"instructions": instructions},
            goto="supervisor"
        )
