from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START
from langgraph.types import Command

from state import GodotState

class FinalReportNode:
    """
    Generates a final report with all generated code, setup instructions, and next steps.
    """
    def __init__(self, name: str):
        self.name = name
        
    def __call__(self, state: GodotState):
        """Make node callable for LangGraph"""
        return self.invoke(state)

    def invoke(self, state: GodotState) -> Command[Literal["__end__"]]:
        instructions = state.get("instructions", {})
        code_dict = state.get("generated_code", {})
        scene_guide = state.get("scene_guide", "")
        
        game_premise = instructions.get("game_premise", "Factorio-Nexus Wars hybrid game")
        
        # Generate a comprehensive report
        report = f"""
# Godot Prototype Generation Report

## Game Premise
{game_premise}

## Generated GDScript Files

"""
        
        # Add each generated script with proper markdown formatting
        for filename, code in code_dict.items():
            report += f"### {filename}\n```gdscript\n{code}\n```\n\n"
        
        # Add scene setup guide
        report += f"""
## Scene Setup Guide
{scene_guide}

## Next Steps

1. **Implement the scenes** according to the guide above
2. **Test core mechanics** such as:
   - Resource gathering mechanics
   - Unit movement and behavior
   - Factory production
   - Basic game loop
   
3. **Refactor and optimize**:
   - Check for performance bottlenecks
   - Improve code organization
   - Add comments where needed
   
4. **Add placeholder visuals**:
   - Create simple sprites for units, buildings, and resources
   - Implement basic UI elements
   - Add minimal sound effects and feedback

5. **Playtest and iterate**:
   - Test the core gameplay loop
   - Adjust parameters and balance
   - Get feedback from early testers

## Technical Notes

- This prototype uses Godot 4.x
- All scripts use static typing for better code quality
- Signals are used for component communication
- Code is organized to facilitate future expansion
"""
        
        return Command(goto="__end__", update={"final_report": report})
