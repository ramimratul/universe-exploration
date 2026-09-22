 > <--<Universe Exploration>-->

Universe Exploration is a single-player space exploration game built with Python and Pygame, designed as an AI project to demonstrate and visualize pathfinding algorithms in action. The game was originally conceived as an interactive way to observe how an AI agent makes decisions in an uncertain environment — exploring an unknown space with limited fuel, collecting resources, and optimizing for the highest score.

## The Concept:
The idea behind the game is simple but layered: you, as a player, and an AI agent are both explorers of the same galaxy. The galaxy is divided into known space — a small region your ship already has charts for — and vast unknown territory that must be explored one move at a time under a fog of war. Both you and the AI start with the same amount of fuel, so every move matters. What makes it interesting is the sequential structure. The AI explores first while you watch — you can observe every decision it makes, see where it goes, what it collects, and follow its decision process in real time through the HUD. Then the map resets, the fog returns, and it is your turn to explore the same space using your own intuition and what you observed from the AI.

## The AI:
The AI agent is powered by the A* pathfinding algorithm — one of the most well-known and widely used algorithms in computer science and game development. But implementing A* here goes beyond simple navigation. The agent has to make decisions under real constraints:-

* It can only see cells it has already visited or revealed; the rest of the galaxy is hidden.
* It has a fixed fuel budget and must plan paths it can actually afford.
* It must decide between collecting a nearby common resource or spending more fuel to reach a rare or exotic one.
* It must decide when to stop collecting in known space and push deeper into unknown territory.

The scoring formula at the heart of the AI's decision engine was designed to make the agent prefer resource quality rather than simply grabbing whatever is closest. The AI also commits to its chosen targets rather than constantly second-guessing itself. It will only change course mid-path if a significantly more valuable opportunity appears, using an improvement threshold before replanning. This gives the AI's movement a more purposeful and deliberate quality that is actually satisfying to watch (At least to me..).


## The Gameplay:
When it is the player's turn, the game becomes strategic. You remember where the AI went and what it found. You know roughly where the rare and exotic resources are clustered. But the map is dark again and you have to navigate there yourself. Decide when to scan, which direction to explore, and how to spend your fuel before it runs out.

Resources come in four tiers:
* Common 
* Rare 
* Exotic 
* Discovery 
Each with distinct visual indicators and increasing point values. Hazard cells scattered across the space and cost extra fuel to enter, forcing you to think about routing. 
The **SPACE** key lets you scan a wider area around your ship at the cost of additional fuel, which can be valuable when you are trying to locate a distant exotic before committing to the journey. 
The game ends when your fuel hits zero. The player's and AI's scores are then compared and a winner is declared. But more importantly, you can reflect on how differently you and the AI approached the same space.


## Why This Project: ()

This game started as a personal idea — a way to turn some of my thoughts and curiosity into something. I have always been curious about our universe, and that direction may become something much larger in the future.
For now, I wanted to make algorithms visual and tangible rather than leaving them as abstract concepts. A* is taught in textbooks and in our courses but watching it navigate a living, uncertain world — making tradeoffs, committing to targets, managing limited resources, and pushing into unknown space — makes the algorithm feel real in a way that a diagram on a whiteboard/paper never quite does.

This project is still in it's early stages. But it has grown significantly from where I started. It now includes a complete game loop with transition screens, independent fog-of-war systems for AI and player exploration, real-time AI decision information displayed through the HUD, pause functionality, an information overlay, resource tiers and hazards, and separate AI and player exploration phases.

## Near Future plan:
A **Mission Mode** with specific objectives and an *Alpha-Beta pruning agent*.

.... More to come in the future.

> **A project where the galaxy is the graph, fuel is the cost, and every move is a decision** (RR).