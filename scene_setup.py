import logging
import re
from typing import Dict, Any, List, Set, Tuple, Literal
from langgraph.graph import StateGraph, START
from langgraph.types import Command
from claude_api import call_claude
from config import PROMPTS

from state import GodotState

logger = logging.getLogger(__name__)

class SceneSetupNode:
    """
    Creates scene setup instructions based on the generated code.
    """
    def __init__(self, name: str):
        self.name = name
        logger.info(f"SceneSetupNode initialized: {name}")
        
    def __call__(self, state: GodotState):
        """Make node callable for LangGraph"""
        return self.invoke(state)

    def invoke(self, state: GodotState) -> Command[Literal["final_report"]]:
        instructions = state.get("instructions", {})
        generated_code = state.get("generated_code", {})
        
        if not generated_code:
            logger.warning("No generated code available for scene setup")
            return Command(
                goto="final_report",
                update={"scene_guide": "No code was generated to create scenes from."}
            )
            
        # Create a prompt for scene setup based on the generated code
        file_list = "\n".join([f"- {filename}" for filename in generated_code.keys()])
        
        prompt = PROMPTS.get("scene_setup", "").format(
            file_list=file_list,
            game_premise=instructions.get("game_premise", ""),
            code_samples="\n\n".join([f"// {filename}:\n{code[:300]}..." for filename, code in generated_code.items()])
        )
        
        # If no scene setup prompt template exists, create a basic one
        if not prompt:
            prompt = f"""
You are a Godot engine expert helping to set up scenes for a new game.
Based on these generated GDScript files, provide step-by-step instructions for creating scenes.

Game Premise: {instructions.get("game_premise", "")}

Files:
{file_list}

Code samples:
{"\n\n".join([f"// {filename}:\n{code[:300]}..." for filename, code in generated_code.items()])}

Please provide clear, numbered steps for setting up the main scenes needed for this game prototype.
Include node hierarchy, script attachments, and any necessary configurations.
"""
        
        # Call Claude to generate scene setup instructions
        scene_guide = call_claude(prompt)
        
        logger.info(f"Generated scene setup guide ({len(scene_guide)} chars)")
        
        return Command(
            goto="final_report",
            update={"scene_guide": scene_guide}
        )
