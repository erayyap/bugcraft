query_gen_prompt = """Given a Minecraft bug report, generate an array of technical search queries to help someone better understand, reproduce, or investigate the bug. Focus on the following aspects:  

- Game mechanics and related features  
- Relevant game versions and changelogs  
- Specific terms, status effects, and interactions  
- Known issues, bug reports, or experimental features  

Ensure the output is an array containing only the search queries, without any additional text or explanations.  

**Bug Report Example:**  
*Version:* 24w38a  
*Description:* Trying to open the "Survival Inventory" UI screen in a world with the new Experimental Bundle Pack enabled whilst having both the Invisibility and Glowing status effects active crashes the game.  

All Gamemodes are susceptible to this, and the crash works both in Singleplayer and on Multiplayer. When opening the Creative Inventory all UI works normally, but when the Survival Inventory tab is selected the game will crash immediately.  

Attached are screenshots of when I created a new world, confirmed only the Experimental Bundle Pack was in the world, gave myself the invisibility and glowing status effects and then attempted to open the Survival Inventory screen.  

**Expected Output:**  
[  
"Minecraft Experimental Bundle Pack features",  
"How to enable Experimental Bundle Pack in Minecraft",  
"Minecraft Survival Inventory vs Creative Inventory",  
"How to get Glowing Status Effect in Minecraft",  
"How to get Invisibility Status Effect in Minecraft",  
]  

Use this structure for any given Minecraft bug report. Return at maximum 10 queries."""

judge_prompt = """**Evaluate the bug report and the information gathered from the search results to determine if there is sufficient detail to create detailed steps to reproduce the bug. Assess the following categories:**

1. **Clarity of Description**: How clearly is the bug described?  
2. **Specific Conditions Provided**: Are all the specific conditions and prerequisites mentioned (game version, game mode, status effects, settings, etc.)?  
3. **Reproducibility**: Is the information sufficient to reliably reproduce the bug?  
4. **Completeness of Information**: Are any critical details missing that are necessary for reproduction?  

**Based on your assessment, provide:**

1. **Reasoning**: A brief explanation for your assessment, covering the strengths and weaknesses of the report in each category.  
2. **Overall Score**: An overall score out of 10, where 10 indicates complete sufficiency and 0 indicates insufficient information.  

Important Consideration: Specific information on the bug may not available on the sources and this is very natural, don't judge on these points. Rely on the context provided by the search results to gauge the likelihood of accurate reproduction. Avoid assuming that exhaustive technical details exist.
**Expected Output:**  

- **Reasoning**: [Your explanation]  
- **Overall Score**: [Score out of 10]"""

judge_source_prompt = """**Evaluate the sources provided and the information gathered from the search results to determine if they contain sufficient detail to create detailed steps to reproduce the bug described in the bug report. Assess the following categories:**

1. **Clarity of Description**: How clearly do the sources describe the bug?  
2. **Specific Conditions Provided**: Do the sources mention all the specific conditions and prerequisites (game version, game mode, status effects, settings, etc.)?  
3. **Reproducibility**: Is the information from the sources sufficient to reliably reproduce the bug?  
4. **Completeness of Information**: Are any critical details missing in the sources that are necessary for reproduction?  

**Based on your assessment, provide:**

1. **Reasoning**: A brief explanation for your assessment, focusing on the quality, detail, and relevance of the sources.  
2. **Overall Score**: An overall score out of 10, where 10 indicates the sources provide complete sufficiency and 0 indicates they are insufficient.  

**Expected Output:**  

- **Reasoning**: [Your explanation]  
- **Overall Score**: [Score out of 10]"""


initial_s2r_prompt = """Using the following bug report and any additional sources provided (which may or may not be helpful), generate a detailed, end-to-end set of steps to reproduce the issue in Minecraft. Your instructions should:
You should make use of commands wherever possible. You must deeply think and consider how gameplay is affected by player actions to write one natural flow.
While writing the commands, if the bug report has commands, you should carry over them exactly as how they were written. YOU SHOULDN'T CHANGE THE COMMANDS IN THE BUG REPORT. PRESERVE THEM.
To make for easier debugging (IF APPLICABLE): Be on creative mode, use commands or alternatives that make the bug easier to reproduce.
If creating a world, make sure cheats are ON and the world is Flatworld (IF THE BUG REPORT DOESN'T SAY ANYTHING ABOUT EXISTING WORLD/CHEATS.).
Wherever applicable, use commands to execute even the most basic tasks.
The steps shouldn't include instructions on copying and pasting. It should only include writing commands.
Avoid using command blocks, unless the given commands in the bug report is too long, or it is explicitly needed. Otherwise, just use chat to use the commands.
Finally, if the player needs to interact with a block, consider that they cannot turn their head. Spawn the needed block at face height in front of the player one block away using commands! (Not on directly on top of the player since that wouldn't work.) Example: /setblock ~ ~1 ~1 minecraft:command_block
Very important: Do not include anything related to naming the world when creating a world in the generated steps, even if it is explicitly in the bug report!
Unless it is explicitly in the bug report, or in the web content, don't write about which keys to press and menus to click. Instead, you should try to abstractize the process. This is done because you may hallucinate details on the plan, especially on keys/menus and this can be detrimental.
- **Start from launching the game**, including all actions from the main menu until the crash occurs.
- **Clearly state** what each action does, any requirements, and any assumptions.
- **Organize the steps** with main points and substeps, listing all actions to take.
- **Ensure** that the instructions cover every detail needed to replicate the issue.
- **Return** the final steps as a JSON dictionary in the format:
- **Pay** attention to what the comments say about the description of the bug report, because the comments are usually newer and contain better info about the bug. Combine both description and comment info to form easily reproducable, and clear whole steps.
  ```json
  {{
    "step 1": "Description of step 1",
    "step 2": "Description of step 2",
    ...
  }}
  ```

**Note:** The provided web sources may be used to assist in creating the steps, but they may not always be relevant or helpful."""
"""Use /fill command to put blocks in the game. Use absolute coordinates when placing blocks, unless the commands are explicitly given in the bug report."""
contradiction_prompt = """**Task Description**:  
You are an advanced language model tasked with analyzing a sequence of step-by-step instructions (S2R) and identifying any contradictions, ambiguities, or inconsistencies within the instructions. The goal is to ensure clarity, logical flow, and alignment with expected outcomes based on provided contextual information (e.g., game mechanics, system behavior). For each identified issue, you must also provide a description explaining why it could cause a problem.

### Guidelines for Identifying Contradictions:

1. **Contextual Consistency**:  
   Compare the actions described in each step with the given context (e.g., game mechanics, system rules, or known behavior of entities). Ensure that:
   - The described steps align with expected game behavior.
   - There are no conflicting outcomes, such as performing an action that negates a previously required condition.

   **Description**: Identify contradictions that might arise when the step contradicts the known mechanics or the context provided.

2. **Temporal Dependencies and Timing Issues**:  
   Check if steps that rely on precise timing or sequence have clearly defined triggers or timeframes. Look for potential timing conflicts where:
   - One action may not feasibly occur before another action completes.
   - An instruction depends on an immediate outcome, but the described mechanism may introduce delays.

   **Description**: Analyze if timing or sequence issues could prevent the expected result from being achieved.

3. **Game Mode Inconsistencies**:  
   Ensure game mode transitions do not interfere with mob behavior or player expectations. Check whether:
   - Switching between game modes could cause unintended behavior.
   - Mob/player interactions behave as expected in the specified mode.

   **Description**: Evaluate how game mode changes could disrupt the flow or lead to unintended consequences in interactions.

4. **Command Dependencies**:  
   Ensure commands that rely on specific world states or conditions are consistent and do not conflict. Evaluate:
   - Whether earlier commands (e.g., time setting, mob summoning) are necessary and properly set up for later actions.
   - If any prerequisites are missing or contradicted by subsequent steps.

   **Description**: Look for dependency issues where commands may not align with prior setups or expected outcomes.

5. **Expected Outcomes vs. Described Outcomes**:  
   Verify that the expected result of following the instructions matches the described outcome. Identify mismatches where:
   - The expected game behavior does not align with the described crash or effect.
   - The outcome is speculative without clear backing from the context.

   **Description**: Ensure that described results align with the intended actions and outcomes without over-reliance on assumptions.

### Output Format:

For each contradiction found:
1. **Step Number**: Clearly indicate the step(s) involved.
2. **Contradiction Description**: Describe the contradiction in detail.
3. **Explanation**: Provide a logical analysis of why this contradiction could cause confusion or failure in reproducing the intended outcome.
4. **Recommendation**: Suggest improvements or clarifications to resolve the issue."""
suggestion_prompt = """Provide suggestions to fix the raised contradiction and enhance the steps to reproduce. Be concise.
{{contradiction}}"""

enhance_s2r_prompt = """```
Using the following bug report, initial set of Steps to Reproduce (S2R), and any additional sources provided, generate a detailed, end-to-end set of steps to reproduce the issue in Minecraft. Your instructions should:

- **Start from launching the game**, including all actions from the main menu until the crash occurs.
- **Clearly state** what each action does, any requirements, and any assumptions.
- **Organize the steps** with main points and substeps, listing all actions to take.
- **Ensure** that the instructions cover every detail needed to replicate the issue.
- **IMPORTANT**: Do not implement the suggestions that prevent the crash from happening. Your goal is to make the crash easier to reproduce by enhancing the S2R, not prevent the crash.
- **Mandatory Implementation of Suggestions:** You must consider each suggestion provided below and implement them **unless** they contradict commands present in the initial bug report.
- **Command Precedence:** If the initial bug report contains commands, those commands **take precedence** over any suggested commands. If a suggestion proposes a command that would change or override a command in the initial bug report, you should **ignore** that part of the suggestion.
- **Suggestion Integration:** If a suggestion does not involve commands, or if the suggested commands do not conflict with the initial bug report's commands, you must implement those suggestions as written.
- **Focus on Suggestions:** Your primary focus is to rewrite the S2R based on the provided suggestions. Only consider the suggestions when making changes. **Do not avoid making changes that are suggested, even if you believe they might be unnecessary. Your task is to implement the suggestions, not to judge their necessity.**
- **Return** the final steps as a JSON dictionary in the format:  
  {{
    "step 1": "Description of step 1",
    "step 2": "Description of step 2",
    ...
  }}

**Important Considerations and Examples:**

The provided suggestions aim to resolve contradictions, inconsistencies, or improve the clarity of the steps to reproduce. You must analyze these suggestions and integrate them thoughtfully into your generated steps, keeping in mind the command precedence rule. Here are some examples of the types of suggestions you might encounter and how to handle them:

**Example Suggestion 1: Addressing Game Mode Conflicts**

*   **Suggestion:** "If a step involves a mob interaction that is not possible in a specific game mode (e.g., creeper exploding in Creative), either change the game mode or use a command to simulate the desired behavior."
*   **Initial Bug Report:** Contains the command `/gamemode creative`

    *   **How to Implement:**
        *   Since the initial bug report specifies Creative mode with a command, you **cannot** change the game mode to Survival.
        *   You must use a command to simulate the creeper explosion in Creative mode, such as `/summon creeper ~ ~ ~ {{Fuse:0}}`.
        *   **Example Output:**
            {{
              "step 1": "Launch Minecraft and create a new world in Creative mode.",
              "step 2": "Use the command /gamemode creative",
              "step 3": "Use the command /summon creeper ~ ~ ~ {{Fuse:0}} to spawn a creeper that will immediately explode."
            }}

**Example Suggestion 2: Resolving Timing or Sequence Issues**

*   **Suggestion:** "If a step requires an action to be performed immediately after another, but there's a potential delay, clarify the timing or use commands to ensure the correct sequence."
*   **Initial Bug Report:** Contains the command `/teleport @s ~ ~ ~`

    *   **How to Implement:**
        *   The suggestion to use commands to ensure the correct sequence is valid, but the specific command might conflict.
        *   Since the initial bug report already uses a teleport command, you **cannot** introduce another teleport command that would override it.
        *   Instead, you must clarify the timing using in-game ticks or a visual cue, or adjust the existing teleport command's coordinates if appropriate.
        *   **Example Output:**
            {{
              "step 1": "Launch Minecraft and create a new world in Survival mode.",
              "step 2": "Use the command /teleport @s ~ ~ ~",
              "step 3": "Immediately after teleporting, and I mean immediately, place a redstone block."
            }}

**Example Suggestion 3: Handling Daylight-Sensitive Mobs**

*   **Suggestion:** "If a step involves a mob that burns in daylight (e.g., skeleton, zombie), ensure the time is set to night or provide the mob with a helmet."
*   **Initial Bug Report:** Contains the command `/time set day`

    *   **How to Implement:**
        *   The initial bug report specifies daytime with a command, so you **cannot** change the time to night.
        *   You must use a command to give the mob a helmet, such as `/summon skeleton ~ ~ ~ {{ArmorItems:[{{}},{{}},{{}},{{id:\\"minecraft:iron_helmet\\",Count:1b}}]}}`.
        *   **Example Output:**
            {{
              "step 1": "Launch Minecraft and create a new world.",
              "step 2": "Use the command /time set day",
              "step 3": "Use the command /summon skeleton ~ ~ ~ {{ArmorItems:[{{}},{{}},{{}},{{id:\\"minecraft:iron_helmet\\",Count:1b}}]}} to spawn a skeleton with an iron helmet."
            }}

**Example Suggestion 4: Clarifying Ambiguous Actions**

*   **Suggestion:** "If a step is vague or unclear, provide specific instructions or use commands to achieve the desired outcome directly."
*   **Initial Bug Report:**  States "Get some iron blocks."

    *   **How to Implement:**
        *   This suggestion is fully applicable as the initial bug report does not use commands for this step.
        *   You can either provide explicit instructions on how to mine and craft iron blocks in Survival mode or use the `/give` command in Creative mode: `/give @s iron_block 64`.
        *   **Example Output:**
            {{
              "step 1": "Launch Minecraft and create a new world in Creative mode.",
              "step 2": "Use the command /give @s iron_block 64 to give yourself 64 iron blocks."
            }}

**General Guidelines:**

1. **Analyze the Suggestion:** Understand the intent behind each suggestion. What problem is it trying to solve?
2. **Contextualize:** Consider the suggestion in the context of the bug report and the overall steps to reproduce.
3. **Prioritize Initial Commands:**  If the initial bug report has commands, those commands are set in stone. Adapt the suggestions around them.
4. **Implement Precisely:** Make specific changes to the steps, using commands (if they don't conflict) or detailed instructions where necessary.
5. **Maintain Logical Flow:** Ensure the modified steps are logically ordered and easy to follow.

By following these examples and guidelines, you should be able to effectively incorporate the provided suggestions while respecting the precedence of the initial bug report's commands, and generate a robust set of steps to reproduce the bug.

NOW IT IS YOUR TURN!
**Here is the initial bug report:**

{initial_bug_report}

**Here is the steps to reproduce that you should enhance:**

{s2r}

**Here are the suggestions provided:**

{suggestions}
"""


alternate_soln_prompt = """**Objective:**

Analyze the provided "Steps to Reproduce" from a Minecraft bug report in **extensive detail**. Your goal is to:

-   **Identify Specific Steps**  that are:
    -   Hard to execute due to complexity, precision, or ambiguity.
    -   Unreliable or inconsistent in producing the expected outcome.
    -   Contradictory or impossible within the game's mechanics,  **especially concerning mob interactions, creative mode discrepancies, day/night cycles, and mob AI targeting.**
-   **Provide Clear and Direct Alternative Solutions**  by:
    -   **Converting Survival Mode Segments**  into  **Creative Mode Alternatives**  or using  **Commands**  where appropriate.
    -   Suggesting specific, actionable modifications to the problematic steps.
    -   Utilizing appropriate game mechanics that enhance consistency and reliability.
    -   Ensuring your suggestions are precise, focused on gameplay, and immediately applicable.

- **DON'T GENERATE SOLUTIONS TO PREVENT OR DEBUG THE CRASH**
    -   The goal of the steps is to reproduce the crash, so don't generate suggestions to prevent the crash or debug it. The end step should generate the crash and that is EXPECTED. 

---

**Instructions:**

1. **Detailed Analysis of Each Step:**
    -   **Sequential Evaluation:**  Keep track of the entire plan as you analyze each step in order.
    -   **Feasibility Assessment:**  Determine if the step is practically executable within Minecraft's gameplay mechanics.
    -   **Gameplay Focus:**  Consider how the step interacts with in-game mechanics, player abilities, game rules,  **mob behavior, day/night impact, and creative/survival mode differences.**

2. **Identify Problematic Areas:**
    -   **Execution Challenges:**  Steps that are difficult due to complex mechanics, rare events, precise timing, or  **unexpected mob AI behavior.**
    -   **Reliability Issues:**  Actions that may not consistently produce the same result due to randomness, glitches, or  **inconsistencies in mob targeting or despawning.**
    -   **Contradictions:**  Steps that conflict with known game mechanics, are impossible to perform, or  **create paradoxes such as a survival mode action that requires creative mode capabilities or vice-versa.**

3. **Specific Step Referencing:**
    -   **Direct Quotation:**  Refer to the exact step number and content when identifying issues.
    -   **Clear Explanation:**  Provide a concise and direct explanation of why the step is problematic,  **especially highlighting issues related to mob interactions, game mode discrepancies, and timing.**
    -   **Provide Corrections:**  If a step is incorrect or impossible, supply the correct method or information without vague suggestions.

4. **Propose Clear Alternative Solutions:**
    -   **Convert to Creative Mode or Use Commands:**  Focus on transforming survival mode steps into creative mode alternatives or using commands to simplify execution and  **bypass limitations like mob griefing or resource gathering.**
    -   **Exact Modifications:**  Offer specific changes to make the step executable and reliable,  **addressing potential issues with mob AI, day/night cycles, and game mode transitions.**
    -   **Gameplay Mechanics Utilization:**  Use appropriate in-game methods to achieve the desired outcome efficiently,  **considering how different game modes or commands can control mob behavior and environmental factors.**
    -   **Actionable Suggestions:**  Ensure your recommendations can be directly applied by the player without additional clarification.

5. **Focus on Gameplay Mechanics:**
    -   **Gameplay-Centric Analysis:**  Base your analysis and suggestions on in-game actions, mechanics, player interactions,  **mob behavior, and the impact of game modes and timing.**
    -   **Exclude Non-Gameplay Elements:**  Do not focus on external factors like verifying item IDs or consulting documentation.

---

**Output Format:**

-   **Problematic Steps Identification:**
    -   **Step  [Number]:**  *"[Quote the step]"*
        -   **Issue:**  *"[Clear and direct description of the problem, with emphasis on mob interactions, game mode discrepancies, and timing issues]"*
        -   **Correction:**  *"[Provide the correct method or information, addressing the specific concerns raised]"*
-   **Alternative Solutions:**
    -   **For Step  [Number]:**
        -   **Suggestion:**  *"[Specific, actionable modification to the step, focusing on converting to Creative Mode or using commands, and resolving issues related to mob behavior, game modes, and timing]"*
        -   **Justification:**  *"[Explain why this alternative is better, focusing on gameplay mechanics and how it addresses the identified issues]"*

---

**Example Analysis:**

*Note: The following is an illustrative example. Replace with your detailed analysis based on the actual steps provided.*

---

**Problematic Steps Identification:**

-   **Step 3:**  *"Switch to Creative Mode."*
-   **Step 4:**  *"Wait for a Creeper to explode near you."*
    -   **Issue:**  Creepers do not target players in Creative Mode and therefore will not explode. This creates a contradiction between the intended action and the game's mob AI rules.
    -   **Correction:**  Remain in Survival Mode for the Creeper to explode, or use commands to force a Creeper explosion if necessary.

-   **Step 3:** *"Set the time to day using /time set day."*
-   **Step 4:** *"Spawn multiple Zombies using /summon zombie."*
-   **Step 5:** *"Get chased by the Zombies."*
    - **Issue:** Zombies burn in daylight. The spawned zombies will catch fire and likely die before they can effectively chase the player, making the step unreliable.
    - **Correction:** Spawn the Zombies at night or give them helmets to prevent them from burning. Alternatively, use a different mob not affected by daylight.

---

**Alternative Solutions:**

-   **For Steps 3 & 4 (Creeper Example):**
    -   **Suggestion:**  *"Stay in Survival Mode. Use  `/summon creeper ~ ~ ~ {{Fuse:0}}`  to spawn a Creeper that will explode instantly next to you."*
    -   **Justification:**  This ensures the Creeper will explode as intended by forcing the explosion with a command while remaining in the correct game mode for mob targeting.

-   **For Steps 3, 4 & 5 (Zombie Example):**
    -   **Suggestion:**  *"Use  `/time set night`  to set the time to night. Then use  `/summon zombie ~ ~ ~ {{IsBaby:0,ArmorItems:[{{}},{{}},{{}},{{id:"minecraft:iron_helmet",Count:1b}}]}}` to spawn adult Zombies with iron helmets. This will prevent them from burning in the daylight."*
    -   **Justification:**  This modification ensures the Zombies do not burn, allowing them to chase the player as intended. Using commands to control the time and equip the Zombies makes the step reliable and consistent.

---

**Final Notes:**

-   **Provide Correct Methods Directly:**  If a step is impractical, overly time-consuming, or relies on unpredictable mob behavior, offer a direct alternative using Creative Mode or commands.
-   **Focus on Converting to Creative Mode or Commands:**  Simplify survival mode tasks by suggesting more efficient methods available in Creative Mode or through commands, especially when dealing with mob interactions and environmental control.
-   **Ensure Clarity and Precision:**  Make sure all your recommendations are clear, specific, and actionable without needing further clarification.
-   **Enhance Reproducibility:**  Your analysis should improve the bug report's clarity, making it easier for developers to reproduce and address the issue efficiently, particularly by addressing potential issues with mob AI, game mode transitions, and timing."""

node_extract_prompt ="""You are an AI language model tasked with extracting nodes for a knowledge graph from the given text. The nodes should represent key entities and concepts. Basically, what you extract should be a page in the game's wiki or documentation."""
node_distill_prompt = """Given this list of nodes, distill the list into a few nodes which are the most relevant with the given bug report. Write only specific entity names that are integral to the bug report. Don't include general concept names.
IMPORTANT: YOU MUST NOT ADD NEW NODES TO THE LIST OR CHANGE THE NAMES. YOU CAN ONLY REMOVE NODES.
THE LIST: {node_list}"""
step_cluster_prompt = """Cluster these steps into 4 step clusters. Don't change the steps and write them as it is."""
step_selection_prompt = """Analyze the provided image and determine the most relevant step cluster from the given step clusters. For each decision, include a detailed reasoning trace explaining why a particular step cluster was selected, referencing the image's visual elements and their relationship to the steps provided. Provide annotations for the image, describing key features, context, and how they influence your decision-making.

If the image correlates with the end of the steps, output 'END' and explain why the visual elements indicate the conclusion of the sequence. If the image does not relate to any of the given steps, output 'NOT RELEVANT' and describe why no connection can be drawn. Your output must include:

1. **Reasoning Trace:** A step-by-step explanation of your analysis.
2. **Image Annotation:** A detailed description of the image's relevant elements and their significance.
3. **Conclusion:** The index of the selected step cluster, 'END,' or 'NOT RELEVANT.'"""
video_step_prompt = """Analyze the provided video segment, which includes the current frame and a summary of relevant features from previous frames, and determine the most relevant step cluster from the given step clusters. For each decision, include a detailed reasoning trace explaining why a particular step cluster was selected, referencing the current frame's visual elements, their relationship to the steps provided, and the context from previous frames.

Additionally, provide annotations for the current frame, describing key features, context, and how they influence your decision-making in combination with the summarized information from earlier frames.

If the video segment indicates the end of the sequence of steps, output 'END' and explain why the visual elements and context suggest the conclusion. If the video segment does not relate to any of the given steps, output 'NOT RELEVANT' and describe why no connection can be drawn. Your output must include:

1. **Reasoning Trace:** A step-by-step explanation of your analysis, incorporating context from previous frames and the current frame.
2. **Frame Annotation:** A detailed description of the current frame's relevant elements and their significance in light of the video context.
3. **Conclusion:** The index of the selected step cluster, 'END,' or 'NOT RELEVANT.'"""
running_summary_prompt = """You will be provided with the current frame's annotations and a summary of relevant features from previous frames in a video sequence. Your task is to integrate the current frame's annotations into the summary to produce an updated and coherent description of the video’s progression. Ensure the updated summary reflects the cumulative context and captures any new developments or shifts indicated by the current frame's annotations.

Specifically, follow these guidelines:

1. **Integration:**
   - Analyze the current frame’s annotations and identify how they relate to or extend the previous summary.
   - Add relevant details from the annotations to the summary, ensuring consistency and logical flow.

2. **Contextual Coherence:**
   - Maintain a coherent narrative that reflects the sequence of events or features observed across the frames.
   - Highlight any new actions, objects, or transitions introduced in the current frame while preserving key elements from the previous summary.

3. **Relevance and Focus:**
   - Focus on elements directly relevant to the video’s steps or context.
   - Omit redundant or irrelevant details unless they contribute to understanding the overall sequence.

Your output must include:
- **Updated Summary:** The revised and comprehensive summary of the video, incorporating the current frame’s annotations.

Input format:
- **Previous Summary:** [The provided summary of relevant features from earlier frames]
- **Current Frame Annotations:** [Detailed annotations of the current frame’s elements]

Output format:
- **Updated Summary:** [Your revised summary here]"""
reasoning_trajectory_prompt = """Analyze the provided external information (e.g., wiki page, datapack details) in relation to the initial Minecraft bug report.

Your task is to identify elements within the external information that are **not explicitly mentioned** in the initial bug report and suggest their potential relevance.

**Output Format:**

Provide concise, actionable suggestions or points of consideration, framed as:

*   "Consider enabling [feature/setting]."
*   "Be aware of [potential limitation/issue]."
*   "The wiki mentions [detail] which might be relevant."
*   "This datapack modifies [aspect], which could be a factor."
*   "The bug report doesn't specify [detail]; this might be important."
*   "Note that [external factor] could influence the behavior."
*   "[Command/setting] might need to be checked."

**Important Guidelines:**

*   **Focus on what the initial bug report *omits* or lacks detail on.**  Do not reiterate information already present in the bug report.
*   **Base your suggestions solely on the provided external information.** Do not introduce new information or speculate beyond what's given.
*   **Be concise and direct.**  Each suggestion should be a single, clear point.
*   **Frame suggestions neutrally.** Avoid language that assumes the bug report is incorrect or incomplete. The goal is to identify potential gaps, not to criticize.
*   **Prioritize technical details** mentioned in the external information that could directly influence the scenario described in the bug report (e.g., specific game rules, entity behaviors, command parameters, datapack modifications).
*   **If the external information offers nothing new or relevant that isn't already covered in the initial bug report, output: NOTHING TO ADD.**

**Focus Areas:**

*   **Identify commands, game rules, entities, items, or mechanics** mentioned in the external information but absent from the initial bug report.
*   **Note any warnings, limitations, specific configurations, or dependencies** described in the external information that could be relevant to the bug.
*   **If the external information is a datapack, consider suggesting its enablement or specific configurations within it.**
*   **If the external information is a wiki page, highlight key details or considerations that the bug report might have overlooked.**

Your goal is to **provide a concise list of potential areas the initial bug report might not fully address**, drawing directly from the provided external information and offering actionable points for further investigation or consideration."""

old_reasoning_trajectory_prompt = """# **Role**  
You are an expert analyst skilled in identifying and resolving issues by synthesizing information from multiple sources.  

# **Task**  
Generate a detailed reasoning trajectory relevant to the given bug report using the provided document under the "CONTENT" section. Your task is to thoroughly analyze and distill the provided information, linking it to the bug report and its context.

# **Process**  
1. **Relevance Assessment**  
   - First, assess the relevance of the document content to the bug report. Clearly state whether the document is relevant or irrelevant.
   - If the content is irrelevant, explain why and provide reasoning based on your assessment. Proceed with your internal knowledge if required.

2. **Reasoning Trajectory Construction**  
   - Develop a reasoning trajectory that specifically addresses the bug report by distilling and interpreting the provided document.
   - Reflect deeply on the concepts, technical details, and any underlying issues mentioned in the bug report.
   - Include technical details about command calls, items, entities, or mechanisms relevant to the issue described.

3. **Evidence and Citations**  
   - Where applicable, cite specific portions of the document using a clear citation format (e.g., [1]).
   - For each cited piece of evidence:
     - Summarize the content in the **cite_content** field.
     - Provide your interpretation and its relevance to the bug report in the **cite_reason** field.
   - Ensure findings are traceable to their sources by linking conclusions with document references.

4. **Answer Format**  
   - Provide your insights in a structured manner:
     - **Short Answer:** A brief response (no more than 10 words) summarizing the main finding.
     - **Analysis:** A detailed explanation of your reasoning, including all technical details and conceptual insights.
     - **Cite_List:** A compilation of cited evidence for traceability."""
cluster_check_prompt = """Look at the step clusters and their titles with the steps provided.
Do the titles and their relative titles match? Are there steps that need movement around?
Give your recommendations as a list where each point correlates to the respective step cluster."""
cluster_rewrite_prompt = """Based on the feedback, move the steps provided between the clusters.
DON'T CHANGE THE TITLES AND THE STEP CONTENTS. YOU CAN ONLY MOVE THEM.
FEEDBACK:
{feedback}"""

final_cluster_prompt = """Given the outputs of image and video analysis related to a Minecraft bug report, synthesize this information to refine and rewrite the step clusters initially generated for reproducing the bug. The analysis outputs will provide insights into the visual and sequential aspects of the bug as it was reproduced, including potential alternate solutions demonstrated in the videos. Your task is to integrate these insights into the step clusters, ensuring they accurately reflect the observed steps and conditions leading to the bug, and consider whether the alternate solutions observed in the videos are more effective than the existing solutions in the step clusters.

**Inputs:**

- **Initial Step Clusters:** The original set of step clusters created to reproduce the bug.
- **Image Analysis Output:** A summary of findings from analyzing images related to the bug, including relevant step indices, annotations, and reasoning traces.
- **Video Analysis Output:** A summary of findings from analyzing video segments related to the bug, including relevant step indices, frame annotations, running summaries, and reasoning traces. This includes observations of any alternate solutions used in the videos.

**Task:**

1. **Review and Integration:**
   - Carefully review the initial step clusters in light of the image and video analysis outputs.
   - Integrate the insights from the analysis, paying close attention to the identified step indices, annotations, reasoning traces, and any alternate solutions observed in the videos.
   - Determine how the visual and sequential information, including alternate solutions, aligns with or differs from the initial step clusters.

2. **Evaluate Alternate Solutions:**
   - Assess the effectiveness and efficiency of the alternate solutions observed in the videos compared to the solutions presented in the initial step clusters.
   - Consider factors such as ease of execution, reliability, and clarity when evaluating the alternate solutions.
   - Determine if the alternate solutions should replace or augment the existing solutions in the step clusters.

3. **Rewrite and Refinement:**
   - Rewrite the step clusters to incorporate the new information, including any validated alternate solutions.
   - Adjust the steps within each cluster as needed, adding, removing, or modifying steps based on the analysis outputs and the evaluation of alternate solutions.
   - Ensure that the rewritten step clusters are coherent, logically ordered, and provide a comprehensive guide to reproducing the bug, incorporating the best available solutions.

4. **Validation:**
   - Validate the rewritten step clusters against the image and video analysis outputs to confirm that they accurately capture the observed phenomena and the effectiveness of the chosen solutions.
   - Ensure that the final step clusters are consistent with the visual evidence, sequential context, and the evaluated alternate solutions.

**Output Format:**

- **Revised Step Clusters:** The updated set of step clusters, formatted as a JSON dictionary where each key represents a cluster title and the value is an array of steps within that cluster.
  ```json
  {{
    "Cluster 1 Title": [
      "Step 1: Description of step 1",
      "Step 2: Description of step 2",
      ...
    ],
    "Cluster 2 Title": [
      "Step 1: Description of step 1",
      "Step 2: Description of step 2",
      ...
    ],
    ...
  }}
  ```

**Example:**

Given the following inputs:

- **Initial Step Clusters:**
  ```json
  {{
    "Cluster A": [
      "Step 1: Launch Minecraft",
      "Step 2: Create a new world in Survival Mode"
    ],
    "Cluster B": [
      "Step 3: Mine for iron ore",
      "Step 4: Craft iron blocks"
    ]
  }}
  ```
- **Image Analysis Output:**
  - Shows iron blocks in the inventory.
- **Video Analysis Output:**
  - Demonstrates using the `/give` command to obtain iron blocks instead of mining and crafting.

The output might be:

- **Revised Step Clusters:**
  ```json
  {{
    "Cluster A": [
      "Step 1: Launch Minecraft",
      "Step 2: Create a new world in Survival Mode or Creative Mode"
    ],
    "Cluster B": [
      "Step 3: Obtain iron blocks",
      "Step 4: If in Survival, use `/give @s iron_block 64` (Alternative to mining and crafting)"
    ]
  }}
  ```
"""
mob_checker_prompt = """**Objective:**

Analyze the provided "Steps to Reproduce" (S2R) from a Minecraft bug report, focusing on mob interactions, their AI, and their states. Your goal is to MAKE THE CRASH EASIER TO REPRODUCE BY:

1. **Identify Inconsistencies and Impossibilities:**
    -   Examine each step involving mobs, considering their natural behavior, AI, and the game's rules.
    -   Detect any actions or states that are impossible or inconsistent with standard mob behavior, such as:
        -   Mobs attacking entities they wouldn't normally target.
        -   Mobs exhibiting behaviors outside their defined AI parameters.
        -   Mobs being present or active in conditions that should prevent their spawning or cause them to despawn/die (e.g., skeletons in daylight without protection).
    -   Identify any contradictions between the steps and the expected mob states (e.g., a creeper exploding in Creative mode).

2. **Analyze Unexplained Behavior for Mobs Mentioned:**
    -   Pay special attention to any mob specifically named in the steps.
    -   Determine if the steps describe any unusual or unexplained behavior for these specifically named mobs.
    -   Assess whether the described actions align with expected mob AI.

3. **Utilize Provided Web Content:**
    -   You will be provided with web content that likely contains information about Minecraft mobs, their AI, and game mechanics.
    -   Use this information to inform your analysis and identify inconsistencies or impossibilities.
    -   Base your solutions on the information extracted from the web content, ensuring they are grounded in established game mechanics.

4. **Generate Solutions, Not Suggestions:**
    -   For each identified issue, provide a **concrete solution** that directly addresses the problem.
    -   Do not offer vague suggestions or multiple options. Instead, present a single, definitive solution based on your analysis and the provided web content.
    -   Focus on solutions that involve altering the steps to align with expected mob behavior, using commands to manipulate the game state, or correcting impossible scenarios.

5. **DON'T GENERATE SOLUTIONS TO PREVENT THE CRASH**
    -   The goal of the steps is to reproduce the crash, so don't generate suggestions to prevent the crash or debug it. The end step should generate the crash and that is EXPECTED. 

6. **Only mob specific suggestions:**
    -   If the bug report doesn't include any mobs, it is not your job to output suggestions. Only look and consider mob interactions. If there is nothing about mobs in the bug report, just say it is fine and you have no suggestions.
---

**Instructions:**

1. **Thorough Step-by-Step Analysis:**
    -   Evaluate each step in the S2R sequentially, keeping track of the overall context and the state of the game world.
    -   Consider the implications of each step on subsequent mob interactions and states.

2. **Mob Behavior and AI Scrutiny:**
    -   For each step involving mobs, ask:
        -   Is this behavior possible for this type of mob?
        -   Does this action align with the mob's AI under these conditions?
        -   Are there any environmental factors (time of day, game mode, biome, etc.) that would affect this mob's behavior or state?
    -   Specifically analyze steps involving mobs for any deviations from standard mob AI.

3. **Web Content Integration:**
    -   Actively use the provided web content to verify mob behaviors, AI parameters, and game mechanics.
    -   Extract relevant information from the web content to support your analysis and solutions.

4. **Solution Generation:**
    -   For each identified inconsistency or impossibility:
        -   Provide a clear and direct solution that resolves the issue.
        -   Ensure the solution is actionable and can be directly implemented in the S2R.
        -   Base your solutions on established game mechanics and information from the web content.
    -   Examples of solutions:
        -   If a step requires a skeleton to attack an armor stand, change the step to involve a different mob or use commands to force the interaction.
        -   If a step spawns skeletons during the day, add a solution to set the time to night or provide the skeletons with helmets.
        -   If a step involves a creeper exploding in Creative mode, change the step to use flint and steel or commands to trigger the explosion.

---

**Output Format:**

For each identified issue:

-   **Step [Number]:**  *"[Quote the problematic step]"*
    -   **Issue:**  *"[Clearly describe the inconsistency, impossibility, or unexplained behavior, with a focus on mob interactions, AI, and states]"*
    -   **Solution:**  *"[Provide a direct and actionable solution based on your analysis and the provided web content]"*

---

**Example:**

**Provided Web Content (Partial):**

> **Skeletons**
>
> Skeletons are one of the most common hostile mobs in Minecraft. They are undead, meaning they are damaged by the Potion of Healing and healed by the Potion of Harming. They also burn in sunlight unless they are wearing a helmet.
>
> **Behavior**
>
> Skeletons will attack players and iron golems within a 16-block radius. They will strafe around their target and shoot arrows. They will not attack other mobs unless they are accidentally hit by another mob's attack.
>
> **Creeper**
>
> Creepers are a common hostile mob in Minecraft. They are known for their silent approach and their devastating explosion.
>
> **Behavior**
>
> Creepers will approach players within a 3-block radius and begin to hiss. After 1.5 seconds, they will explode, causing significant damage to the surrounding area and any entities within the blast radius. Creepers will not explode if the player is in Creative mode.

**S2R:**

-   **Step 1:**  "Set the time to day using /time set day."
-   **Step 2:**  "Spawn a skeleton using /summon skeleton."
-   **Step 3:**  "Observe the skeleton attacking a nearby armor stand."
-   **Step 4:** "Switch to Creative Mode using /gamemode creative."
-   **Step 5:** "Approach a creeper and wait for it to explode."

**Analysis:**

-   **Step 2:**  *"Spawn a skeleton using /summon skeleton."*
    -   **Issue:**  Skeletons burn in daylight. Spawning one during the day will cause it to catch fire and likely die before it can perform any actions.
    -   **Solution:**  Change the step to  `/time set night`  before summoning the skeleton, or use  `/summon skeleton ~ ~ ~ {{ArmorItems:[{{}},{{}},{{}},{{id:"minecraft:iron_helmet",Count:1b}}]}}`  to give it a helmet.

-   **Step 3:**  *"Observe the skeleton attacking a nearby armor stand."*
    -   **Issue:**  Skeletons do not attack armor stands under normal circumstances. Their AI is programmed to target players and iron golems.
    -   **Solution:**  Change the step to  `/summon iron_golem`  to spawn an iron golem, which the skeleton will naturally attack. Alternatively, use commands to manipulate the skeleton's AI and force it to target the armor stand, though this is more complex.

-   **Step 5:**  *"Approach a creeper and wait for it to explode."*
    -   **Issue:**  Creepers do not explode when the player is in Creative mode. This step creates a contradiction.
    -   **Solution:**  Change the step to remain in Survival mode. Alternatively, use  `/summon creeper ~ ~ ~ {{Fuse:0}}`  to spawn a creeper that will explode instantly. If you want specific control, use commands that set a creeper's NBT to {{Fuse:0}} through merge entity.

---

**Final Notes:**

-   **Prioritize Accuracy:**  Ensure your analysis and solutions are accurate and consistent with Minecraft's game mechanics.
-   **Web Content is Key:**  Use the provided web content as your primary source of information about mob behavior and game rules.
-   **Direct Solutions Only:**  Provide clear, actionable solutions without ambiguity or multiple options.
-   **Focus on Mobs:**  Pay special attention to mob interactions, AI, and states throughout your analysis.
-   **Your goal:** YOUR GOAL IS TO MAKE THE SPECIFIC CRASH EASIER TO HAPPEN, NOT PREVENT IT. DO NOT GIVE SUGGESTIONS THAT PREVENTS THE CRASH FROM HAPPENING.
FINALLY MOST IMPORTANT INSTRUCTION: YOU MUST NEVER GIVE SUGGESTIONS THAT PREVENT THE CRASH."""

crash_checker_prompt = """You are a crash analysis assistant. You are provided with a set of Steps to Reproduce (S2R) that describe a process leading to a software crash, and a set of user suggestions intended to address the issue.

**Your Task:**

Carefully analyze the provided suggestions in the context of the S2R. Determine if **any** of the suggestions, either **explicitly** or **implicitly**, attempt to:

1. **Prevent** the crash from occurring in the first place.
2. **Mitigate** the effects of the crash if it were to occur (e.g., preventing data loss, providing a workaround).
3. **Fix** the underlying cause of the crash.
4. **Change any of the steps** in the S2R in a way that could potentially avoid the crash.
5. **Introduce a check or condition** that could intercept the sequence of events leading to the crash.
6. **Suggest an alternative approach** or method that avoids the problematic steps described in the S2R.
7. **Change the state of the application or system** in a way that avoids the problematic steps described in the S2R.

**Output:**

*   If any of the suggestions, even subtly, attempt to achieve any of the above objectives related to preventing, mitigating, or fixing the crash, output: `YES`
*   If none of the suggestions have any bearing on preventing, mitigating, or fixing the crash, output: `NO`
*   If the suggestion doesn't have anything of substance (For example if the suggestion includes something like: "I have no problems with this S2R. I have nothing to add."), output: `NO`

**Input:**

The Steps to Reproduce (S2R):
{s2r}

The User Suggestions:
{suggestions}
"""
