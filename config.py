"""
Centralized configuration for the GDScript LangGraph code generation pipeline.
"""

# General settings
MAX_ITERATIONS_PER_FILE = 5
GODOT_VERSION = "Godot 4.x"

# Claude API settings
CLAUDE_MODEL = "claude-3-7-sonnet-20250219"
CLAUDE_MAX_TOKENS = 6000

CORE_GAME_DESCRIPTION = """
Your game is a real-time strategy and automation hybrid that combines elements of Factorio-style factory building, Nexus Wars-style auto-battles, and RTS build-order strategy. Players start with a small build area and a limited amount of gold, which is gradually generated at their starting camp and must be collected manually by their avatar. Resources such as wood, stone, and gold spawn around the map, creating opportunities for economic expansion and strategic resource control.

Each player has access to a hotbar with unlocked buildings, allowing them to construct harvesters, crafting stations, automation tools, and combat units. Some buildings focus on resource generation, like the Lumber Mill and Quarry, while others specialize in crafting advanced materials, such as the Workshop, which combines wood into frames. Players must balance automation with efficiency, as gathering and production require optimization over time to ensure a steady supply chain.

Tech progression is handled through a Drafting Table, where players unlock Tier 2 and Tier 3 buildings that enable more powerful units and automation. Combat plays out through a spawn track system, where units like Catapults, Ballistas, and Battering Rams are constructed at specific buildings and automatically march toward the enemy base. Defenses, such as walls and fortifications, can be built at a higher cost to shield against incoming attacks.

Players cannot see their opponent's full build, but they can infer strategies based on incoming attacks, defenses, and scouting mechanics. The game encourages different playstyles, such as rushing aggressive units early, focusing on economy and expansion, or investing in late-game tech dominance. Since resources are finite, the game includes strategic decision-making around expansion and depletion, where controlling resource-rich areas can determine long-term success.

Victory is achieved when an opponent's HP reaches zero, but the game also allows for tiebreaker mechanics where depleting all resources can force a stalemate. To ensure variety, the game could feature different faction playstyles (e.g., aggressive Goblins, economic Elves, or versatile Humans), inspired by StarCraft's asymmetric balance or Dominion's card pool drafting. A potential relic system incentivizes early exploration by offering bonuses like faster production, instant research, or enemy sabotage.

The game's visual and sound design could take inspiration from Hero's Hour, Loop Hero, and The King is Watching, with an aesthetic that blends whimsical medieval automation with tactical warfare. Additionally, mechanics such as limited fog of war, randomized terrain, and asynchronous play could enhance replayability and strategic depth. To prevent cheesy rush tactics, a "build phase" grace period could delay early aggression, allowing players to develop a baseline economy before engaging in combat.

At its core, this game offers a highly replayable, strategy-driven experience, rewarding efficiency, adaptation, and macro-level decision-making. Whether players prefer meticulous optimization of automated systems, rapid tactical aggression, or long-term economic scaling, they will need to constantly adapt their build order and strategy to counter their opponent's evolving tactics.
"""

# Folder structure for generated code
FOLDER_STRUCTURE = {
    "scripts": "res://scripts/",
    "scenes": "res://scenes/",
    "resources": "res://resources/",
    "autoload": "res://autoload/"
}

# Default coding best practices
CODING_BEST_PRACTICES = {
    "static_typing": True,
    "use_folders": FOLDER_STRUCTURE,
    "godot_version": GODOT_VERSION
}

# Project structure guidelines
PROJECT_STRUCTURE = [
    "scripts",
    "scenes",
    "resources",
    "autoload (for singletons)"
]

# Design constraints for game development
DESIGN_CONSTRAINTS = [
    "Use placeholder art (colored shapes/boxes) for rapid prototyping",
    "Focus on core gameplay mechanics over visuals",
    "Implement a complete gameplay loop with win/lose conditions",
    "Use signals for communication between nodes",
    "Implement proper resource management systems"
]

# Key mechanics for Factorio-Nexus Wars hybrid
KEY_MECHANICS = [
    "Resource gathering and management",
    "Automated unit production",
    "Base building and expansion",
    "Strategic control of map areas"
]

# Default output directory for generated code
OUTPUT_DIRECTORY = "generated_code"

# Code validation rules
CODE_VALIDATION_RULES = {
    "require_extends": True,
    "enforce_static_typing": True,
    "require_class_name_for_reusable": True,
    "min_comments_ratio": 3,  # Minimum number of comments for scripts > 10 lines
    "require_signals_for_complex": True,  # For scripts > 15 lines
    "check_indentation": True,
    "no_todos": True,
    "require_ready_function": ["Unit", "Factory", "Tower", "ResourceNode"],
    "require_error_handling": True
}

# Basic Godot types that shouldn't be treated as dependencies
BASIC_GODOT_TYPES = {
    "Node", "Node2D", "Sprite2D", "Control", "Area2D", "Label", "Button", 
    "StaticBody2D", "RigidBody2D", "CharacterBody2D", "Camera2D", "Timer",
    "int", "float", "bool", "String", "Array", "Dictionary", "Vector2", "Vector3",
    "Rect2", "Transform2D", "Color", "Object", "Resource"
}

# Prompts for Claude
PROMPTS = {
    # Code Writer prompts
    "code_writer_initial": """
You are an expert GDScript programmer. I'm building a Godot 4 game that blends Factorio and Nexus Wars mechanics.
Game premise: {game_premise}

Please write a GDScript file named '{filename}' that serves the purpose of: {purpose}

{details_section}

Follow these coding guidelines:
- Use {godot_version} syntax
- Use static typing for all variables and function parameters
- Include helpful comments and docstrings for functions
- Follow a clean, organized structure with proper indentation
- Implement signals where appropriate for communication between nodes
- Use "_" prefix for private functions
- Include class_name if appropriate
- Handle potential errors gracefully

Please provide ONLY the GDScript code with no additional explanation. The code should be valid GDScript that can be used directly in Godot 4.
""",

    "code_writer_revision": """
You are an expert GDScript programmer. I'm building a Godot 4 game that blends Factorio and Nexus Wars mechanics.

You previously wrote this GDScript file named '{filename}' for the purpose: {purpose}

Here is your previous code:
```gdscript
{previous_code}
```

I need you to revise this code based on the following feedback:
{feedback}

Please provide ONLY the improved GDScript code with no additional explanation. The code should be valid GDScript that can be used directly in Godot 4.
""",

    # File Processor prompts
    "dependency_analysis": """
The following classes/scripts were referenced but don't exist yet: {dependencies}
Based on these names and the context from {source_file}, create JSON definitions for these missing files.

Here's the source code that referenced them:
```gdscript
{code}... (truncated)
```

For each missing dependency, define:
{
  "filename": "[ClassName].gd",
  "purpose": "Brief description of purpose",
  "extends": "Most appropriate Godot class",
  "details": {
    "responsibilities": ["main responsibility"],
    "dependencies": []
  }
}

Return valid JSON array only, no explanations.
""",

    # Supervisor prompts
    "file_planning": """
You are an expert Godot game developer creating a plan for a new game.

Game concept: {game_premise}

I need you to analyze this game concept and list all necessary GDScript files that should be created.
For each file, provide:
1. Filename (with .gd extension)
2. Purpose of the file
3. Key responsibilities or features
4. Class that this script extends (Node, Node2D, Control, etc.)
5. Whether it should be a singleton (autoload)
6. Likely dependencies on other scripts

Focus on creating a complete architecture that covers:
- Core game systems (main scene, game state management)
- Resource management
- Units and factories
- UI elements
- Helper utilities

Format your response as a JSON array with objects having these fields:
[
  {{
    "filename": "example.gd", 
    "purpose": "what this file does",
    "extends": "Node2D",
    "singleton": true/false,
    "dependencies": ["other_file.gd"],
    "details": {{
      "responsibilities": ["feature1", "feature2"],
      "key_methods": ["method1", "method2"]
    }}
  }}
]

Provide only the JSON array, no explanations or markdown.
"""
}
