"""
Centralized configuration for the GDScript LangGraph code generation pipeline.
"""

# General settings
MAX_ITERATIONS_PER_FILE = 5
GODOT_VERSION = "Godot 4.x"

# Claude API settings
CLAUDE_MODEL = "claude-3-7-sonnet-20250219"
CLAUDE_MAX_TOKENS = 8192

CORE_GAME_DESCRIPTION = """
### **Competitive Automation RTS : Game Concept**

This is a **competitive, 2-dimensional, real-time strategy and automation hybrid**, blending **Factorio-style factory building, Nexus Wars-style auto-battles, and RTS build-order optimization**. Players face off on a **symmetrical battlefield**, managing their economy, automating production, and deploying units to overwhelm their opponent's base. The game focuses exclusively on **PvP, macro-focused gameplay**, with **no single-player or AI-controlled opponents** beyond unit behavior logic.

### **Core Gameplay Loop**

1. **Resource Management** : Players gather **gold, wood, stone**, and other materials from **resource nodes** scattered around their starting area or randomly generated clusters.
2. **Base Construction** : Buildings can **harvest resources, craft materials, automate production, and generate combat units**.
3. **Tech Progression** : Through the **Drafting Table**, players unlock **advanced Tier 2 and Tier 3 buildings**, leading to stronger units and increased automation.
4. **Combat & Strategy** : Units are automatically deployed along a **spawn track located at the top of the screen** and march toward the enemy base. Defenses such as **walls and fortifications** require careful planning to counter incoming waves.
5. **Fog of War & Scouting** : Players cannot see the **opponent's full build**, relying on **attacks, defenses, and limited scouting mechanics** to infer strategies.
6. **Victory Conditions** : The game ends when a **player's base HP reaches zero**, but **alternative win conditions** (such as forcing a resource depletion stalemate) introduce **long-term strategic depth**.

### **Building System & Automation**

Each player has a **hotbar of buildings**, including:

- **Harvesters** (Lumber Mill, Quarry) : Collect raw resources.
- **Crafting Stations** (Workshop, Sawmill) : Refine materials into higher-tier components.
- **Automation Structures** (Conveyors, Depots) : Move resources without direct player interaction — otherwise units must be collected and moved by hand.
- **Military Factories** (Atelier, Foundry) : Produce and deploy offensive units like **Catapults, Ballistas, and Battering Rams**.
- **Defensive Structures** (Walls, Towers, Fortifications) : Shield the base at a higher cost to encourage aggressive play.

As the user triggers upgrades via the Drafting Table, they can unlock more buildings and build higher tech units.

Players must balance **automation efficiency vs. adaptability**, optimizing **resource flow** while remaining **reactive to enemy strategies**.

### **Strategic Depth & Playstyles**

The game supports **multiple strategic approaches**, rewarding adaptability:

- **Rush Aggression** : Deploy early units to overwhelm an opponent before defenses are established.
- **Tech Boom** : Focus on **researching advanced units** and production efficiency, sacrificing early aggression.
- **Economy Play** : Expand aggressively to **secure long-term resource control**, outpacing the opponent's economy.
- **Depletion Play** : Exploit **finite resources** to force the game into a **stalemate or war of attrition**.
- **Building Optimization -** Like Factorio, a key part of our game loop is the optimization of your local area.  Good play should see your base operating like a well oiled machine, whereas bad play should perform worse.

### **Advanced Mechanics & Meta Considerations**

- **Faction Diversity** : Players can choose from different factions (e.g., **Goblins favor aggression, Elves prioritize economy, Humans adapt easily**), similar to **StarCraft's asymmetric balance**.
- **Relics & Map Control** : Exploration is rewarded with **powerful relics**, granting **temporary buffs, passive bonuses, or strategic one-time effects**.
- **Fog of War & Intel Gathering** : Players can **scout** the opponent's unit compositions but **not exact build orders**, requiring strategic inference.

### **Final Vision**

This game offers a **high-skill, automation-driven strategy experience**, rewarding **efficiency, adaptation, and long-term planning**. Whether players favor **meticulous optimization, aggressive rush tactics, or economic dominance**, success will come from **balancing automation, adaptation, and strategic foresight** in a competitive, **PvP-focused** battlefield.
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
    "Leverage Resource objects for reusable data (e.g., unit stats, building costs) instead of hardcoding values in scripts.",
    "Use Object Pooling for frequently instantiated objects like units or projectiles to avoid expensive runtime allocations.",
    "Implement a complete gameplay loop with win/lose conditions",
    "Prefer Godot’s built-in signals over manually polling data.",
    "Game logic should reside in a GameManager singleton.", 
    "Units should be self-contained, with AI and state-handling within their script", 
    "Use inheritance and composition appropriately.", 
    "Use static typing for clarity: e.g., `var health: int = 100`",
    "Comment and document code with clear docstrings: e.g., `# Move the unit to the target position`",
    "Use Autoload (Singletons) only for global state management", 
    "Avoid singletons for things that should be scene-specific (e.g., units)", 
    "Use State Machines for unit AI (e.g., IDLE → ATTACKING → RETREATING)"
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
BASIC_GODOT_TYPES = [
    "Node", "Node2D", "Sprite2D", "Control", "Button", "Label", "LineEdit", 
    "TextureButton", "CanvasLayer", "Camera2D", "Area2D", "CollisionShape2D",
    "RigidBody2D", "StaticBody2D", "CharacterBody2D", "Timer", "AudioStreamPlayer",
    "AnimationPlayer", "AnimatedSprite2D", "Tween", "Resource", "Reference", 
    "String", "Array", "Dictionary", "Vector2", "Vector3", "Rect2", "Color",
    "Transform2D", "Callable", "Signal", "PackedScene", "SceneTree", "Viewport",
    "TextureRect", "Panel", "TileMap", "Navigation2D", "NavigationAgent2D", 
    "ShaderMaterial", "Shader", "HTTPRequest", "TCP_Server", "WebSocketClient",
    "OS", "DisplayServer", "Input", "Engine", "ProjectSettings", "ResourceLoader",
    "File", "Directory", "Mutex", "Thread", "Semaphore", "VideoStream",
    "VideoStreamPlayer", "PanelContainer", "HBoxContainer", "VBoxContainer",
    "GridContainer", "MarginContainer", "BoxContainer", "HSeparator", 
    "VSeparator", "ScrollContainer", "Tree", "ItemList", "Object", "RefCounted",
    "RayCast2D", "Path2D", "PathFollow2D", "EditorPlugin", "EditorScript",
    "MultiplayerAPI", "MultiplayerPeer", "NetworkedMultiplayerPeer", "Position2D",
    # Add more types if needed
]

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
{design_constraints}

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
{{
  "filename": "[ClassName].gd",
  "purpose": "Brief description of purpose",
  "extends": "Most appropriate Godot class",
  "details": {{
    "responsibilities": ["main responsibility"],
    "dependencies": []
  }}
}}

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
""",

    "code_review": """
You are an expert GDScript code reviewer.

Please evaluate this code and provide feedback if you find any issues that would prevent it from working properly.
Focus on critical issues like:
1. Syntax errors
2. Missing 'extends' statements
3. Incomplete implementations
4. Type errors or missing type hints
5. Placeholder text or TODOs left in the code

If the code looks good, just reply with "The code looks good and should work correctly."
Otherwise, provide specific feedback about what needs to be fixed.

Review the following code for a file named '{filename}' 
that serves the purpose: "{purpose}".

Here is the code:
```gdscript
{code}
```
"""
}
