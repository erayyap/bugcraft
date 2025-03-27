# HEAVY ACTION DECISION PROMPT
heavy_action_decision_prompt = """**Task:**

Analyze the provided step clusters, which outline the steps to reproduce a specific action or scenario in a game, and determine whether the entire set of clusters, in totality, involves "heavy action" that requires significant player interaction with the world, particularly through demanding physical input or reflexes. Provide a comprehensive reasoning for your decision.

**Definitions:**

*   **Heavy Action:** Actions that require precise timing, rapid movements, complex maneuvers, or quick reflexes from the player. This typically involves direct interaction with the game world beyond basic GUI operations or simple building.
*   **Exempt Actions:** GUI operations (e.g., navigating menus, selecting options), writing commands, and simple building tasks (e.g., placing blocks to create a small structure) are **not** considered heavy action.

**Input:**

A set of step clusters, each containing a list of steps described in text format.

**Output:**

1. **Reasoning:** A detailed explanation justifying whether the entire set of step clusters involves heavy action. Consider the presence and prevalence of heavy action steps across all clusters.
2. **Classification:** A single binary classification for the entire set of clusters:
    *   **YES:** If the set of clusters, as a whole, involves heavy action.
    *   **NO:** If the set of clusters, as a whole, does not involve heavy action.

**Example 1 (YES):**

**Step Clusters:**

{{
  "Cluster 1: Initial Setup": [
    "Step 1: Launch Minecraft.",
    "Step 2: Create a new world in Survival Mode."
  ],
  "Cluster 2: Resource Gathering": [
    "Step 3: Locate a village with a Fletcher villager.",
    "Step 4: Obtain emeralds by trading or mining."
  ],
  "Cluster 3: Combat Engagement": [
    "Step 5: Equip a diamond sword and shield.",
    "Step 6: Engage in combat with a group of zombies, using the sword and shield to attack and defend."
  ],
  "Cluster 4: Building a Shelter": [
    "Step 7: Gather wood and cobblestone.",
    "Step 8: Build a small house with a door and windows."
  ]
}}


**Output:**

**Reasoning:** The step clusters include a mix of actions. Clusters 1, 2, and 4 involve actions that are exempt from being considered heavy action, such as launching the game, creating a world, gathering resources, and building a simple structure. However, Cluster 3 involves combat, which requires the player to actively attack and defend using precise timing and movements. Since there is at least one cluster that includes heavy action steps, the entire set of clusters can be considered to involve heavy action.

**Classification:** YES

**Example 2 (NO):**

**Step Clusters:**

{{
  "Cluster 1: Game Setup": [
    "Step 1: Launch Minecraft.",
    "Step 2: Create a new world in Creative Mode."
  ],
  "Cluster 2: Teleportation": [
    "Step 3: Use the command `/tp @s 100 64 100` to teleport to coordinates 100, 64, 100."
  ],
  "Cluster 3: Structure Generation": [
    "Step 4: Use the command `/setblock 100 65 100 minecraft:diamond_block` to place a diamond block.",
    "Step 5: Use the command `/give @s diamond_sword 1` to give yourself a diamond sword."
  ],
  "Cluster 4: Time and Weather": [
    "Step 6: Use the command `/time set day` to set the time to day.",
    "Step 7: Use the command `/weather clear` to make the weather clear."
  ]
}}


**Output:**

**Reasoning:** All the step clusters in this example involve actions that are exempt from being considered heavy action. These actions include launching the game, creating a world, and using commands to teleport, generate structures, set the time, and control the weather. There are no steps that require precise timing, rapid movements, or complex maneuvers from the player.

**Classification:** NO

NOW, IT IS YOUR TURN:

Step Clusters
{step_clusters}
"""

# REFLECTION PROMPT
reflection_prompt = """Given the final state of the screen after executing the commands, give feedback about the screen looking at your last thoughts, last action and the trajectory.
Also do a classification if the action done was a SUCCESS or FAILURE.
If the action is a SUCCESS and all the steps are done on the current cluster, write MOVE_TO_NEXT_CLUSTER for classification.
**Task:**

Provide a detailed reflection on the outcome of the last action, considering the following aspects:

1. **Visual State Assessment:**
    *   Describe the current state of the game as shown in the screenshot. Are there any menus open? What is the player's perspective? What elements are visible on the screen?
    *   Also, write: What does the screen show? What is written on the screen? Do a visual annotation. Especially write what the chat text shows.
    *   Compare the current visual state to the expected state based on the **Thought** and **Trajectory**. Does the screen reflect the intended outcome of the last action?
    *   Identify any discrepancies or unexpected elements visible in the screenshot.

2. **Action Accuracy:**
    *   Evaluate whether the executed **Action** accurately reflected the plan outlined in the **Thought**.
    *   If the action involved clicking on a specific GUI element using `click_place()`, verify if the correct element was clicked based on the screenshot and the initial annotated image (which you don't have access to in this prompt but know existed).
    *   If the action involved keyboard input (`press()`), assess whether the action was likely performed correctly based on the resulting visual state and common Minecraft UI/UX patterns.
    *   If the action involved sending a command (`command()`), check if the command was executed correctly and if its effects are visible on the screen.

3. **Progress Evaluation:**
    *   Determine whether the last action successfully moved the process forward within the current step cluster.
    *   Identify which step in the current cluster was likely targeted by the last action.
    *   Based on the visual state and the executed action, infer whether the targeted step was likely completed successfully.

4. **Classification:**
    *   Provide a classification of the action's outcome:
        *   **SUCCESS:** The action was executed correctly, and the game state reflects the intended outcome, advancing progress within the step cluster.
        *   **FAILURE:** The action was not executed correctly, or the game state does not reflect the intended outcome, hindering progress.
        *   **MOVE_TO_NEXT_CLUSTER:** The action was executed correctly, and the game state reflects the intended outcome. Furthermore, all steps within the current step cluster have been successfully completed, indicating that the agent should proceed to the next step cluster.
    *   In your feedback, explain in detail, the specific reasons that led to the chosen classification.
    *   What are the next steps if it was a failure or a success?

**Output:**

Your output should be a detailed reflection report in the following format:

**Feedback and Classification:**

*   **Visual State:** [Detailed description of the game state in the screenshot, comparison with the expected state, and identification of discrepancies.]
*   **Action Accuracy:** [Evaluation of the action's accuracy, considering the Thought, Trajectory, and the method used (click\_place, click, press, command).]
*   **Progress Evaluation:** [Assessment of whether the action successfully advanced the process, identification of the targeted step, and inference about its completion.]

**Classification:** [SUCCESS, FAILURE, or MOVE_TO_NEXT_CLUSTER]


**Step Clusters:**

{step_clusters}

YOU ARE CURRENTLY ON STEP CLUSTER: {current_step_title}

**Trajectory:**

{trajectory}

**Thought:**

{thought}

**Action:**

{action}
"""

# CLUSTER VERIFICATION PROMPT
cluster_verification_prompt = """**Task:**

1. **Verify Step Completion:**
    *   **Exhaustively analyze the Trajectory** to determine if each step listed in the **Current Step Cluster** has been demonstrably completed.
    *   **Do not solely rely on the Reflection LLM's assessment.** The trajectory is the ground truth. The Reflection LLM's output can provide hints, but it might be mistaken.
    *   For each step, explain **why** you believe it has or has not been completed based on specific actions in the trajectory.
    *   Be skeptical. Look for potential gaps or ambiguities in the trajectory that might indicate an incomplete step.

2. **Cross-Reference with Reflection:**
    *   Consider the **Reflection LLM's Output** as supplementary information. Does it corroborate your findings from the trajectory analysis?
    *   If there are discrepancies between your analysis and the Reflection LLM's output, explain them and prioritize the trajectory as the source of truth.

3. **Final Assessment:**
    *   Based on your thorough verification, state whether the **MOVE_TO_NEXT_CLUSTER** classification is **CORRECT** or **INCORRECT**.
    *   Provide a detailed justification for your final assessment, referencing specific evidence from the trajectory and, if applicable, the Reflection LLM's output.
**Step Clusters:**

{step_clusters}

YOU ARE CURRENTLY ON STEP CLUSTER: {current_step_title}

**Trajectory:** (This includes the last action taken!)

{trajectory}"""

# ------------------------------------------------------------------------------------------------
# THOUGHT PROMPT
# ------------------------------------------------------------------------------------------------

thought_prompt = """You are an AI agent tasked with automating the reproduction of a bug in Minecraft. You will be working with a set of instructions organized into **step clusters**, each representing a high-level stage in the bug reproduction process. You will also be given a **trajectory** of actions that have already been executed.

Your current goal is to generate a **thoughtful plan** outlining what actions should be taken **next** to make the most progress.

**Input:**

1. **Step Clusters:** A list of step clusters, each containing a title and a list of individual steps. Here's an example of what the structure looks like:
    
    
    [
        {{
            "title": "World Setup",
            "steps": [
                "Launch Minecraft and ensure you are using the Java Edition snapshot 24w37a or the version where the bug is reported.",
                "From the main menu, click on 'Singleplayer' to create a new world.",
                "Click on 'Create New World'.",
                "Set the game mode to 'Creative' to easily use commands and access inventory."
            ]
        }},
        {{
            "title": "World Options Configuration",
            "steps": [
                "Click on 'More World Options'.",
                "Ensure 'Allow Cheats' is set to 'ON' to use commands.",
                "Select 'World Type' and choose 'Superflat' for simplicity.",
                "Click 'Done' and then 'Create New World' to generate the world."
            ]
        }},
        # ... (more step clusters)
    ]
    
    
2. **Trajectory:** A list of actions that have already been performed. Each action is represented as a string, using the same command format you will use to generate new actions. Example:
    
    
    trajectory = [
        "click_place(1)",
        "command(\"/time set day\")",
        "press(\"w\", 2.0)"
    ]
    
    

**Task:**

Generate a **thought** that does the following:

1. **Identify the Current Step Cluster:** Based on the trajectory, determine which step cluster is currently being executed, or if a new step cluster should be started.
2. **Assess Progress:** Briefly evaluate the progress made within the current step cluster. Which steps have likely been completed based on the trajectory?
3. **Determine the Next Logical Action:** Decide on the single most logical and helpful action to take next. This action should either advance the current step cluster or, if the current cluster is complete, start the next logical step cluster. Consider the overall goal of reproducing the bug.
4. **Consider the Limitations:** Remember that you can only interact with GUI elements that are annotated with numbers in the screenshot (using `click_place()`) and keyboard controls (`press()`) for other interactions. Prioritize Minecraft commands (`command()`) whenever possible.
5. **Prioritize Helpfulness:** The next action should be the one that is most likely to be successful and move the process forward efficiently.
6. **Focus on One Step at a Time:** The thought should focus on planning only the very next action, not a sequence of actions.
7. **Do not generate the action itself.** This will be done in a separate call to the LLM.
8. **Make the thought process clear and concise.** The thought should include the reasoning for choosing the next action, referencing the specific step or objective.
9. **Be mindful of context.** The thought should take into account any relevant information from previous steps or the overall bug report.
10. **Be careful when writing commands.** The command method that action LLM has access to handles the presses of t key and enter key for the command to be executed in Minecraft. Therefore, you don't need to press t or enter for a command to be executed. You only need to enter the command as one line, using `command()` method. THIS IS VERY IMPORTANT!
11. **Verify Click Location:** **Before selecting a GUI element to interact with using `click_place()`, you will be provided with an **annotated** image of the game screen. Look at the annotated image to find the correct index for the GUI element you intend to click. This verification process helps ensure accuracy.**

These are the commands that the action LLM will use:

**Available Commands:**

*   `command(text)`: Sends a command to the Minecraft game. Example: `command("/time set day"). The comment handles everything from opening the chat to sending the message. So, you DON'T need to open the chat menu to send the command, otherwise it WON'T WORK. TO SEND A COMMAND YOU MUST BE ON GAMEPLAY OVERWORLD WITH THE CHAT BAR AND ALL MENUS CLOSED.
*   `press(key, duration)`: Presses a keyboard key for a specified duration (in seconds). Example: `press("w", 2.5)` presses the "w" key for 2.5 seconds. IMPORTANT: You can also press two keys at once like this for example: `press("ctrl", "a")` would do CTRL+a, for example. You can also use press('right_click') to do a right click. Available mouse clicks are: left_click, right_click, middle_click
*   `click_place(index)`: Clicks on the GUI element indicated by the `index` number in the annotated screenshot. The `index` corresponds to the numbers you will see on the image. Example: `click_place(3)` clicks on the GUI element labeled "3" in the screenshot.
*   `write(string)`: Writes the given string using the keyboard. Before using this, you might want to focus on the text-box using click_place.

**Example Thought (Illustrative):**

**Step Clusters:** (The `bug_steps` example provided above)

**Trajectory:**


[
    "click_place(2)", // Assuming "2" was the "Singleplayer" button
    "click_place(4)", // Assuming "4" was the "Create New World" button
    "click_place(7)", // Assuming "7" was the "Game Mode" selection
    "click_place(9)" // Assuming "9" was the "Creative" option,
    "click_place(3)", // "More World Options"
]


**Generated Thought:**


"Thought: The trajectory shows that we have completed the 'World Setup' step cluster and have started the 'World Options Configuration' step cluster. We have clicked on 'More World Options'. The next logical action is to ensure 'Allow Cheats' is set to 'ON'. There should be a toggle or button labeled in the screenshot to achieve this. I will check the annotated image to find the correct index for the 'Allow Cheats' toggle for `click_place()`. This is important because we will need to use commands later."


**Output:**

Output only the **thought** in the format shown above. Do not generate any code or commands at this stage.

NOW, it is your turn!

Trajectory

{trajectory}

Step Clusters

{step_clusters}

YOU ARE CURRENTLY ON STEP CLUSTER: {current_step_title}

NOW, OUTPUT YOUR THOUGHT (PLAN ON WHAT TO DO NEXT):
"""
# ------------------------------------------------------------------------------------------------
# ACTION PROMPT
# ------------------------------------------------------------------------------------------------

# ACTION PROMPT
action_prompt = """You are an AI agent tasked with controlling a Minecraft game to reproduce a bug. You are given a set of instructions organized into **step clusters**, a **trajectory** of actions already performed, a **thought** outlining the next logical action (or actions), and an annotated screenshot of the **initial** game state.

**Available Commands:**

*   `command(text)`: Sends a command to the Minecraft game. Example: `command("/time set day"). The comment handles everything from opening the chat to sending the message. So, you DON'T need to open the chat menu to send the command, otherwise it WON'T WORK. TO SEND A COMMAND YOU MUST BE ON GAMEPLAY OVERWORLD WITH THE CHAT BAR AND ALL MENUS CLOSED.
*   `press(key, duration)`: Presses a keyboard key for a specified duration (in seconds). Example: `press("w", 2.5)` presses the "w" key for 2.5 seconds. IMPORTANT: You can also press two keys at once like this for example: `press("ctrl", "a")` would do CTRL+a, for example. You can also use press('right_click') to do a right click. Available mouse clicks are: left_click, right_click, middle_click
*   `click_place(index)`: Clicks on the GUI element indicated by the `index` number in the annotated screenshot. The `index` corresponds to the numbers you will see on the image. Example: `click_place(3)` clicks on the GUI element labeled "3" in the screenshot.
*   `write(string)`: Writes the given string using the keyboard. Before using this, you might want to focus on the text-box using click_place.

**Input:**
1. **Annotated Screenshot:** An image of the Minecraft game **at the start of the current step** with numbered annotations on GUI elements.
    *   **Important Limitation:** `click_place()` **only works reliably on this initial screenshot**. The annotations are **not updated** when the game state changes (e.g., after opening a menu or inventory). You cannot use `click_place()` to interact with new GUI elements that appear after the initial screenshot was taken.
2. **Step Clusters:** A list of step clusters, each containing a title and a list of individual steps. (See example in the thought prompt). You are currently on the step cluster titled: **Current Step Title**
3. **Trajectory:** A list of actions that have already been performed. Example:
    
    
    trajectory = [
        "click_place(1)",
        "command(\"/time set day\")",
        "press(\"w\", 2.0)"
    ]
    
    
5. **Thought:** A brief explanation of the next logical action (or actions) to take and the reasoning behind it. Example:
    
    
Thought: The trajectory shows that we have completed the 'World Setup' step cluster and have started the 'World Options Configuration' step cluster. We have clicked on 'More World Options'. The next logical action is to ensure 'Allow Cheats' is set to 'ON'. There should be a toggle or button labeled in the screenshot to achieve this. I will check the annotated image to find the correct index for the 'Allow Cheats' toggle for `click_place()`. This is important because we will need to use commands later.
    

**Task:**

Generate a **list of commands** (an array of strings) to perform the action or actions described in the **Thought**.

**Instructions:**

1. Analyze the **Thought** carefully. Understand the intended action(s) and the reasoning.
2. **Examine the Annotated Screenshot and identify any GUI elements that can be used to perform the action(s) using `click_place(index)`.** Use the index from the annotated screenshot. **However, only use `click_place()` if the action is to be performed on the initial game state, before any changes have occurred.**
3. If the action(s) cannot be performed using `click_place()`, determine if Minecraft command(s) (`command()`) can be used.
4. **Prioritize using `click_place()` for GUI interactions on the initial screen state and `command()` for other actions whenever possible.**
5. You may generate **multiple commands** if the thought process requires a sequence of actions.
6. **Always output the commands as an array of strings,** even if there's only one command.
7. **Output only the command array** without any additional text or explanation. The output should be directly executable by the API.

**Important Considerations:**

*   The annotator **only marks GUI elements** and only on the **initial screenshot**.
*   `click_place()` is **only reliable on the initial screenshot** and should not be used after the game state has changed.
*   **Prioritize Minecraft commands (`command()`)** for efficiency and reliability.
*   Be precise with your commands. Incorrect coordinates may lead to failed actions.
*   Refer to the **Trajectory** to understand the context of the current game state.

**Example 1:**

**Thought:**


"Thought: We need to open the inventory and then click on the item in slot 1. I will check the annotated image to find the correct index for slot 1."

**Generated Action (Corrected):**


[
"press(\"e\", 0.1)",
"click_place(3)" // Assuming the 3rd index at click_place is slot 1.
]

**Example 2:**

**Thought:**

"Thought: We should click on the button labeled 'Create New World' which is annotated with the number 3 in the initial screenshot."

**Generated Action:**


[
"click_place(3)"
]


**Example 3:**

**Thought:**


"Thought: We need to write the command, '/time set night'. Since command method handles the key presses, you only need to send the command method."


**Generated Action:**


[
"command(\"/time set night\")"
]


**HERE IS YOUR TURN:**

**Step Clusters:**

{step_clusters}

YOU ARE CURRENTLY ON STEP CLUSTER: {current_step_title}

**Trajectory:**

{trajectory}

**Thought:**

{thought}

**Output only the command array (as a JSON array, no codeblocks) to perform the action described in the Thought:**
"""

# ------------------------------------------------------------------------------------------------
# THOUGHT ACTION PROMPT
# ------------------------------------------------------------------------------------------------

# THOUGHT ACTION PROMPT
thought_action_prompt = """You are an AI agent tasked with automating the reproduction of a bug in Minecraft. You will be working with a set of instructions organized into **step clusters**, each representing a high-level stage in the bug reproduction process. You will also be given a **trajectory** of actions that have already been executed, including thoughts and reflections.

Your current goal is to generate a **thoughtful plan** outlining what actions should be taken **next** to make the most progress, and then generate the **action** to be performed.

**Input:**

1. **Step Clusters:** A list of step clusters, each containing a title and a list of individual steps.
    
2. **Trajectory:** A list of actions, thoughts, and reflections that have already been performed. Each entry is represented as a dictionary.
    
3. **Annotated Screenshot:** An image of the Minecraft game **at the start of the current step** with numbered annotations on GUI elements.
    *   **Important Limitation:** `click_place()` **only works reliably on this initial screenshot**. The annotations are **not updated** when the game state changes (e.g., after opening a menu or inventory). You cannot use `click_place()` to interact with new GUI elements that appear after the initial screenshot was taken.

**Task:**

Generate a **thought** and an **action** that does the following:

1. **Thought:**
    *   **Identify the Current Step Cluster:** Based on the trajectory, determine which step cluster is currently being executed, or if a new step cluster should be started.
    *   **Assess Progress:** Briefly evaluate the progress made within the current step cluster. Which steps have likely been completed based on the trajectory?
    *   **Determine the Next Logical Action:** Decide on the single most logical and helpful action to take next. This action should either advance the current step cluster or, if the current cluster is complete, start the next logical step cluster. Consider the overall goal of reproducing the bug.
    *   **Consider the Limitations:** Remember that you can only interact with GUI elements that are annotated with numbers in the screenshot (using `click_place()`) and keyboard controls (`press()`) for other interactions. Prioritize Minecraft commands (`command()`) whenever possible. Also, keep in mind the limitation of `click_place()` mentioned above.
    *   **Prioritize Helpfulness:** The next action should be the one that is most likely to be successful and move the process forward efficiently.
    *   **Focus on One Step at a Time:** The thought should focus on planning only the very next action, not a sequence of actions.
    *   **Make the thought process clear and concise.** The thought should include the reasoning for choosing the next action, referencing the specific step or objective.
    *   **Be mindful of context.** The thought should take into account any relevant information from previous steps or the overall bug report.
    *   **Be careful when writing commands.** The command method that action LLM has access to handles the presses of t key and enter key for the command to be executed in Minecraft. Therefore, you don't need to press t or enter for a command to be executed. You only need to enter the command as one line, using `command()` method. THIS IS VERY IMPORTANT!
    *   **How to move and turn.** Your abilities to interact with the world are quite limited. Therefore, use commands most of the time to interact with the world. To place blocks, to even move and turn; use commands. Basically, use commands wherever you can. However, clicks to interact with blocks and menus is OK and you should use the press command for those. There is no equivalent of directly clicking as a command.
    *   **Verify Click Location:** Before selecting a GUI element to interact with using `click_place()`, look at the annotated image to find the correct index for the GUI element. This verification process helps ensure accuracy.
    *   **Do every configuration before creating the world:** Before pressing the create world button, make sure you do every configuration correctly, including correct options. If you don't, you cannot reverse this! Also look at future step clusters and be very strict about pressing the "Create World" button!
    *   **click_place limitations:** click_place() clicks only on the center of a rectangle. For clicks at specific points within the rectangle, consider alternatives you can achieve by pressing keys.
    *   If you need to select a world to play a previously created world in the world selection screen, firstly you must select that world by clicking on it and then click play. The selected world will be highlighted.
    *   **Be careful of loops.** Sometimes, as an agent you can go into loops where you retry the same action many times. If there is not a very good reason to do this, generate alternate solutions different from the bug report to achieve the ultimate goal: The crash. Don't be afraid to innovate. AVOID DOING THE SAME ACTION AT MOST 5 TIMES IN A ROW. You are probably doing something wrong. Seek alternate solutions.

2. **Action:**
    *   Based on the thought, generate a **list of commands** (an array of strings) to perform the action or actions described in the **Thought**.

These are the commands that the action LLM will use:

**Available Commands:**

*   `command(text)`: Sends a command to the Minecraft game. Example: `command("/time set day"). The comment handles everything from opening the chat to sending the message. So, you DON'T need to open the chat menu to send the command, otherwise it WON'T WORK. TO SEND A COMMAND YOU MUST BE ON GAMEPLAY OVERWORLD WITH THE CHAT BAR AND ALL MENUS CLOSED.
*   `press(key, duration)`: Presses a keyboard key for a specified duration (in seconds). Example: `press("w", 2.5)` presses the "w" key for 2.5 seconds. IMPORTANT: You can also press two keys at once like this for example: `press("ctrl", "a")` would do CTRL+a, for example. You can also use press('right_click') to do a right click. Available mouse clicks are: left_click, right_click, middle_click
*   `click_place(index)`: Clicks on the GUI element indicated by the `index` number in the annotated screenshot. The `index` corresponds to the numbers you will see on the image. Example: `click_place(3)` clicks on the GUI element labeled "3" in the screenshot.
*   `write(string)`: Writes the given string using the keyboard. Before using this, you might want to focus on the text-box using click_place.

**Output:**

Output the **thought** and **action** in the following format:


Thought: [Your thought process here]
Action: [
"command1",
"command2",
"command3"
]


**Example:**

**Trajectory:**


[
    {{
        "Thought": "The trajectory shows that we are on the 'World Setup' step cluster. The next logical action is to launch Minecraft and click on single player. I will check the annotated image to find the correct index for the 'Singleplayer' button.",
        "Action": ["click_place(2)"],
        "Reflection": "Feedback and Classification:
            *   Visual State: The game is currently showing the main menu, with options for Singleplayer, Multiplayer, and Minecraft Realms. The screen matches the expected state after launching the game.
            *   Action Accuracy: The action 'click_place(2)' was intended to click the 'Singleplayer' button, and it was executed correctly.
            *   Progress Evaluation: The action successfully advanced the process, initiating the 'World Setup' step.

            Classification: SUCCESS"
    }},
    {{
        "Thought": "We have clicked on single player. Now we need to click on 'Create New World'. I will check the annotated image to find the correct index for the 'Create New World' button.",
        "Action": ["click_place(4)"],
        "Reflection": "Feedback and Classification:
            *   Visual State: The game is now showing the world selection screen. We can see existing worlds (if any) and the 'Create New World' button.
            *   Action Accuracy: The action 'click_place(4)' was intended to click the 'Create New World' button, and it was executed correctly.
            *   Progress Evaluation: The action successfully advanced the process within the 'World Setup' step cluster.

            Classification: SUCCESS"
    }}
]


**Generated Thought and Action:**


Thought: We have clicked on 'Create New World'. Now, according to the 'World Setup' step cluster, we need to set the game mode to 'Creative'. I will check the annotated image to find the correct index for the game mode setting.
Action: [
"click_place(7)"
]


**HERE IS YOUR TURN:**

**Step Clusters:**

{step_clusters}

YOU ARE CURRENTLY ON STEP CLUSTER: {current_step_title}

**Trajectory:**

{trajectory}

**Output the thought and action in the format specified above:**
"""

# ------------------------------------------------------------------------------------------------
# SELF CORRECTION PROMPT
# ------------------------------------------------------------------------------------------------

# SELF CORRECTION PROMPT
self_correction_prompt = """You are an AI agent tasked with ensuring the accuracy and efficiency of a Minecraft bug reproduction process. You will be given a **Thought** (a plan for the next action), a **Trajectory** (a history of actions, thoughts, and reflections), and an **Action** (the actual commands executed). Your task is to act as a self-correction mechanism, providing feedback on whether the executed action aligns with the thought and the overall trajectory.

**Input:**

1. **Step Clusters:** A list of step clusters, each containing a title and a list of individual steps.
    
2. **Trajectory:** A list of actions, thoughts, and reflections that have already been performed. Each entry is represented as a dictionary.
    
3. **Thought:** A brief explanation of the next logical action (or actions) to take and the reasoning behind it.
    
4. **Action:** The actual commands executed based on the thought.
    

**Task:**

Provide feedback on whether the **Action** makes sense given the **Thought** and the **Trajectory**. Consider the following:

1. **Alignment with Thought:**
    *   Does the action directly address the goal stated in the thought?
    *   Are there any discrepancies between the intended action in the thought and the actual commands executed?
    *   Is the action the most logical and efficient way to achieve the thought's objective, given the available commands (`click_place`, `press`, `command`,)?
    *   **If the thought mentions using the annotated image to verify a click location, confirm that this process was explicitly stated in the thought.**
2. **Consistency with Trajectory:**
    *   Does the action build upon the previous actions and reflections in the trajectory?
    *   Does the action maintain a coherent flow within the current step cluster?
    *   Are there any contradictions between the action and the established context of the game state from the trajectory?
    
3. **Correctness and Efficiency:**
    *   Is the action technically correct in terms of syntax and usage of commands?
    *   Could the action be optimized for greater efficiency or clarity?
    *   Are there any potential issues or risks associated with the action?
    *   **Crucially, if the action attempts to use the `command()` function while the game is in a menu (not the main game world), provide specific feedback that commands are only applicable in the game world and cannot be used from menus.**
    *   **Also, if the thought and action is planning to write a command but plans to open the chat menu by pressing "T", provide specific feedback the command method available already handles this. So, instead of pressing T, just use the command method as your action.**
    *   **Be careful of loops.** Sometimes, as an agent you can go into loops where you retry the same action many times. If there is not a very good reason to do this, generate alternate solutions different from the bug report to achieve the ultimate goal: The crash. Don't be afraid to innovate. AVOID DOING THE SAME ACTION AT MOST 5 TIMES IN A ROW. You are probably doing something wrong. Seek alternate solutions.
    *   **Innovate in multiple command failures.** If you fail to write a command many times, think of alternative ways of achieving the command, (Especially syntax errors!). For example, if you are having difficulties with getting an enchanted item in one command, first get the item then enchant it. Don't try rewriting the command in slightly different ways to fix syntax issues. It won't work! However, don't be too harsh when retrying a command that didn't have syntax errors that was from 5-10 iterations ago. That command didn't have syntax errors so now, it can work properly.
    *   **How to move and turn.** Your abilities to interact with the world are quite limited. Therefore, use commands most of the time to interact with the world. To place blocks, to even move and turn; use commands. Basically, use commands wherever you can.
    *   When loading a world, make sure the world is selected before loading.
    *   **Do every configuration before creating the world:** Before pressing the create world button, make sure you do every configuration correctly, including correct options.
    *   **click_place limitations:** click_place() clicks only on the center of a rectangle. For clicks at specific points within the rectangle, consider alternatives.
    *   If you need to select a world to play a previously created world in the world selection screen, firstly you must select that world by clicking on it and then click play. The selected world will be highlighted.


# Important: **When generating alternate solutions, be precise with what you mean. Give actual alternate solutions, rather than vague general phrases.**

**Output:**

Your output should be a feedback report using the following `JudgmentModel` format:

reasoning: [Your detailed reasoning here]
classification: [CORRECT or INCORRECT]

**HERE IS YOUR TURN:**

**Step Clusters:**

{step_clusters}

YOU ARE CURRENTLY ON STEP CLUSTER: {current_step_title}

**Trajectory:**

{trajectory}

**Thought:**

{thought}

**Action:**

{action}

NOW, PROVIDE THE FEEDBACK using the given format:
"""

"""**Example 1 (Correct Thought/Action):**

**Step Clusters:**

[
    {{
        "title": "World Setup",
        "steps": [
            "Launch Minecraft.",
            "Click 'Singleplayer'.",
            "Click 'Create New World'."
        ]
    }}
]

**Trajectory:**

[
    {{
        "Thought": "We are on the 'World Setup' step cluster. The next logical action is to launch Minecraft.",
        "Action": ["click_place(1)"],
        "Reflection": "..."
    }},
    {{
        "Thought": "We have launched Minecraft. Now we need to click on 'Singleplayer'. I will check the annotated image to find the correct index for the 'Singleplayer' button.",
        "Action": ["click_place(2)"],
        "Reflection": "..."
    }}
]

**Thought:**

"Thought: We have clicked on 'Singleplayer'. Now we need to click on 'Create New World'. I will check the annotated image to find the correct index for the 'Create New World' button."

**Action:**

[
"click_place(4)"
]

**Feedback:**

reasoning: "The thought proposes clicking on 'Create New World' and explicitly states the intention to verify the location using the annotated image, which is the correct procedure. The action correctly executes this using 'click_place(4)', assuming '4' corresponds to the 'Create New World' button in the annotated screenshot. This action aligns perfectly with the thought and the trajectory, which indicates a progression through the 'World Setup' step cluster. The action is efficient and correct."
classification: "CORRECT"

**Example 2 (Incorrect Thought/Action - Command from Menu):**

**Step Clusters:**

[
    {{
        "title": "World Setup",
        "steps": [
            "Launch Minecraft.",
            "Click 'Singleplayer'."
        ]
    }},
    {{
        "title": "Set Time",
        "steps": [
            "Enter the world.",
            "Set the time to night using the /time command."
        ]
    }}
]

**Trajectory:**

[
    {{
        "Thought": "We are on the 'World Setup' step cluster. The next logical action is to launch Minecraft.",
        "Action": ["click_place(1)"],
        "Reflection": "..."
    }},
    {{
        "Thought": "We have launched Minecraft. Now we need to click on 'Singleplayer'. I will check the annotated image to find the correct index for the 'Singleplayer' button.",
        "Action": ["click_place(2)"],
        "Reflection": "..."
    }},
    {{
        "Thought": "We have clicked on 'Singleplayer'. Now we need to create world and enter it.",
        "Action": ["click_place(4)"],
        "Reflection": "..."
    }}
]

**Thought:** We have clicked on singleplayer and created a world. We should now set the time to night using the /time command."

**Action:**

[
"command(\"/time set night\")"
]

**Feedback:**

reasoning: "The thought correctly identifies the next step as setting the time to night. However, the action attempts to use the `command()` function, which is incorrect in this context. Based on the trajectory, the game is in a menu after clicking 'Singleplayer' and 'Create New World' and not in the main game world. Commands are only applicable when the player is in the game world, not from within menus. Therefore, the action is incorrect and cannot achieve the desired outcome."
classification: "INCORRECT"

"""

# ------------------------------------------------------------------------------------------------
# ACTION CORRECTION PROMPT
# ------------------------------------------------------------------------------------------------

action_correction_prompt = """You are an AI agent tasked with automating the reproduction of a bug in Minecraft. You will be given a set of instructions organized into **step clusters**, a **trajectory** of actions that have already been executed (including thoughts, reflections, and judgements), and **feedback** from a self-correction mechanism.

Your current goal is to generate a **corrected thoughtful plan** outlining what actions should be taken **next** to make the most progress, and then generate the **corrected action** to be performed, taking into account the feedback provided.

**Input:**

1. **Step Clusters:** A list of step clusters, each containing a title and a list of individual steps.
    
2. **Trajectory:** A list of actions, thoughts, reflections, and judgments that have already been performed. Each entry is represented as a dictionary.
    
3. **Annotated Screenshot:** An image of the Minecraft game **at the start of the current step** with numbered annotations on GUI elements.
    *   **Important Limitation:** `click_place()` **only works reliably on this initial screenshot**. The annotations are **not updated** when the game state changes (e.g., after opening a menu or inventory). You cannot use `click_place()` to interact with new GUI elements that appear after the initial screenshot was taken.
    
4. **Feedback:** Feedback from the self-correction mechanism on the previous thought and action, provided in the `JudgmentModel` format. Example:
    
    
    "Judgment": {{
        "reasoning": "The thought correctly identifies the next step as setting the time to night. However, the action attempts to use the `command()` function, which is incorrect in this context. Based on the trajectory, the game is likely in a menu after clicking 'Singleplayer' and 'Create New World' and not in the main game world. Commands are only applicable when the player is in the game world, not from within menus. Therefore, the action is incorrect and cannot achieve the desired outcome.",
        "classification": "INCORRECT"
    }}
    
    

**Task:**

Generate a **corrected thought** and a **corrected action** that addresses the feedback and does the following:

1. **Corrected Thought:**
    *   **Address the Feedback:** Carefully consider the feedback provided in the `JudgmentModel`. Understand the identified issues and their implications.
    *   **Identify the Current Step Cluster:** Based on the trajectory, determine which step cluster is currently being executed, or if a new step cluster should be started.
    *   **Assess Progress:** Briefly evaluate the progress made within the current step cluster. Which steps have likely been completed based on the trajectory?
    *   **Determine the Next Logical Action:** Decide on the single most logical and helpful action to take next, taking into account the feedback. This action should either advance the current step cluster or, if the current cluster is complete, start the next logical step cluster. Consider the overall goal of reproducing the bug.
    *   **Consider the Limitations:** Remember that you can only interact with GUI elements that are annotated with numbers in the screenshot (using `click_place()`) and keyboard controls (`press()`) for other interactions. Prioritize Minecraft commands (`command()`) whenever possible. Also, keep in mind the limitation of `click_place()` mentioned above.
    *   **Innovate in multiple command failures.** If you fail to write a command many times, think of alternative ways of achieving the command. For example, if you are having difficulties with getting an enchanted item in one command, first get the item then enchant it. 
    *   **Prioritize Helpfulness:** The next action should be the one that is most likely to be successful and move the process forward efficiently.
    *   **Focus on One Step at a Time:** The thought should focus on planning only the very next action, not a sequence of actions.
    *   **Make the thought process clear and concise.** The thought should include the reasoning for choosing the next action, referencing the specific step or objective and addressing the feedback.
    *   **Be mindful of context.** The thought should take into account any relevant information from previous steps or the overall bug report.
    *   **Be careful when writing commands.** The command method that action LLM has access to handles the presses of t key and enter key for the command to be executed in Minecraft. Therefore, you don't need to press t or enter for a command to be executed. You only need to enter the command as one line, using `command()` method. THIS IS VERY IMPORTANT!
    *   **Be careful of loops.** Sometimes, as an agent you can go into loops where you retry the same action many times. If there is not a very good reason to do this, generate alternate solutions different from the bug report to achieve the ultimate goal: The crash. Don't be afraid to innovate.
    *   *   **How to move and turn.** Your abilities to interact with the world are quite limited. Therefore, use commands most of the time to interact with the world. To place blocks, to even move and turn; use commands. Basically, use commands wherever you can.
    *   **Verify Click Location:** If the next action involves clicking a GUI element, explicitly state in your thought that you will check the annotated image to find the correct index for `click_place()`.
    *   **Prioritize Alternate Solutions:** If the feedback mentions repeated actions, your goal should be avoiding them. Avoid repeating your previous actions, both the latest one given and the last iteration's actions. You are allowed to combine them however, since sometimes combining actions help. (Only applicable in command methods. Don't combine actions while using click_place)

02. **Corrected Action:**
    *   Based on the corrected thought, generate a **list of commands** (an array of strings) to perform the action or actions described in the **Corrected Thought**.

These are the commands that the action LLM will use:

**Available Commands:**

*   `command(text)`: Sends a command to the Minecraft game. Example: `command("/time set day"). The comment handles everything from opening the chat to sending the message. So, you DON'T need to open the chat menu to send the command, otherwise it WON'T WORK. TO SEND A COMMAND YOU MUST BE ON GAMEPLAY OVERWORLD WITH THE CHAT BAR AND ALL MENUS CLOSED.
*   `press(key, duration)`: Presses a keyboard key for a specified duration (in seconds). Example: `press("w", 2.5)` presses the "w" key for 2.5 seconds. IMPORTANT: You can also press two keys at once like this for example: `press("ctrl", "a")` would do CTRL+a, for example. You can also use press('right_click') to do a right click. Available mouse clicks are: left_click, right_click, middle_click
*   `click_place(index)`: Clicks on the GUI element indicated by the `index` number in the annotated screenshot. The `index` corresponds to the numbers you will see on the image. Example: `click_place(3)` clicks on the GUI element labeled "3" in the screenshot.
*   `write(string)`: Writes the given string using the keyboard. Before using this, you might want to focus on the text-box using click_place.

**Output:**

Output the **corrected thought** and **corrected action** in the following format:


Thought: [Your corrected thought process here]
Action: [
"command1",
"command2",

"command3"
]


**Example:**

**Trajectory:**


[
    {{
        "Thought": "We are on the 'World Setup' step cluster. The next logical action is to launch Minecraft.",
        "Action": ["click_place(1)"],
        "Reflection": "Feedback and Classification:
            *   Visual State: The game is currently showing the main menu, with options for Singleplayer, Multiplayer, and Minecraft Realms. The screen matches the expected state after launching the game.
            *   Action Accuracy: The action 'click_place(1)' was intended to click the 'Singleplayer' button, and it was executed correctly.
            *   Progress Evaluation: The action successfully advanced the process, initiating the 'World Setup' step.

            Classification: SUCCESS",
        "Judgment": {{
            "reasoning": "The thought and action are aligned and consistent with the trajectory. The action is correct and efficient.",
            "classification": "CORRECT"
        }}
    }},
]



**Thought:**

 
"Thought: We have clicked on 'Singleplayer'. Now we need to set the time to night using the /time command."



**Action:**


["command(\"/time set night\")"]



**Feedback:**


{{
    "reasoning": "The thought correctly identifies the next step as setting the time to night. However, the action attempts to use the `command()` function, which is incorrect in this context. Based on the trajectory, the game is likely in a menu after clicking 'Singleplayer' and not in the main game world. Commands are only applicable when the player is in the game world, not from within menus. Therefore, the action is incorrect and cannot achieve the desired outcome.",
    "classification": "INCORRECT"
}}



**Generated Corrected Thought and Corrected Action:**


Thought: My previous thought attempted to use a command from a menu, which is not allowed. We need to first enter the world before we can use commands. According to the 'Set Time' step cluster, we should first click on 'Create New World' and then enter the world. I will check the annotated image to find the correct index for the 'Create New World' button.
Action: [
"click_place(4)"
]


**HERE IS YOUR TURN:**

**Step Clusters:**

{step_clusters}

YOU ARE CURRENTLY ON STEP CLUSTER: {current_step_title}

**Trajectory:**

{trajectory}

**Thought:**

{thought}

**Action:**

{action}

**Feedback:**

{feedback}

**Output the corrected thought and corrected action in the format specified:**
"""
