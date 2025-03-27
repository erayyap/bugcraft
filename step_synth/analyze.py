from step_synth.chains import *
from step_synth.utils import *
from step_synth.environment import *
from step_synth.logger import logger
import asyncio


def process_wiki(bug_report, version, filenames):
        nodes = node_extract_chain.invoke({"bug_report": bug_report}).nodes
        logger.log(f"NER (Named Entity Recognition) is done. Extracted Entities: {nodes}")

        pages = find_matches(filenames, str(nodes))
        logger.log(f"Fuzzy matching has been done with Minecraft wiki pages. Matched title names are: {pages}")

        distilled_nodes = node_distill_chain.invoke({"bug_report": bug_report, "node_list": str(pages)}).nodes
        if version:
            distilled_nodes.append("Java Edition " + version.replace('.', '_'))
        distilled_nodes.append("Game mode")
        distilled_nodes.append("Commands")
        distilled_nodes.append("Game rule")
        distilled_nodes.append("Experiments")
        logger.log(f"Node names have been reselected with LLM assistance. Final titles are: {distilled_nodes}")

        wiki_content = read_files(WIKI_DIRECTORY, distilled_nodes)
        for content in wiki_content:
            logger.log(content, "wiki_page")

        if USE_REASONING_TRAJECTORY:
            wiki_content = generate_reasoning_trajectories(bug_report, wiki_content)

        return wiki_content

def generate_reasoning_trajectories(bug_report, content_list):
        trajectories = []
        for content in content_list:
            trajectory = reasoning_trajectory_chain.invoke({"bug_report": bug_report, "content": content})
            logger.log({"title": content["title"], "text": trajectory}, "wiki_page_reasoning")
            if trajectory.strip() != "IRRELEVANT":
                trajectories.append(trajectory)
        return trajectories

def search_iterations(bug_report, all_results):
    iter = 0
    search_results = []
    while iter < SOURCE_MAX_ITERATION:
        logger.log(f"Search tool is being used. Iteration:{iter + 1}")
        queries = eval(query_chain.invoke({"bug_report": prepare_br(bug_report, all_results)}))
        logger.log(f"Generated queries: {queries}")

        for query in queries:
            results = search_tool.invoke(query)
            for result in results:
                content = result.get("content") or ""
                if content:
                    if USE_REASONING_TRAJECTORY:
                        content = reasoning_trajectory_chain.invoke({"bug_report": bug_report, "content": content}) 
                        print("Reasoning Generated: ", content)
                    if content.strip() != 'IRRELEVANT':
                        logger.log({"title": query, "text": content}, "search_tool_query")
                        search_results.append(content)
        
        judgment_model = judge_chain.invoke({"bug_report": prepare_br(bug_report, all_results + search_results)})
        judge_score = judgment_model.point
        logger.log(f"Judge Score: {judge_score}")
        
        if judge_score >= JUDGE_THRESHOLD:
            logger.log("Judge score threshold met. Exiting iterations.")
            break
        
        iter += 1
    return search_results

def generate_s2r(bug_report, all_results, datapack_names):
    logger.log("Initial steps to reproduce (S2R) is being generated.")
    if datapack_names and len(datapack_names) > 0:
        new_datapack_name = []
        for datapack_name in datapack_names:
            new_datapack_name.append(datapack_name.split("\\")[-1].split("/")[-1])
        datapack_names_str = ", ".join(new_datapack_name)
        new_br = bug_report + "\nProvided Datapack Name(s):\n" + datapack_names_str
        print(new_br)
        s2r = s2r_chain.invoke({"bug_report": prepare_br(new_br, all_results)})
    else:
        s2r = s2r_chain.invoke({"bug_report": prepare_br(bug_report, all_results)})
    logger.log("Initial steps to reproduce (S2R) has been generated.")
    logger.log(s2r,"steps_to_reproduce")
    return s2r

def enhance_s2r(s2r, all_results, initial_bug_report):
    logger.log("Enhancing S2R by generating alternate suggestions.")
    if USE_ALTERNATE_SOLUTIONS:
        alternate_soln_str = alternate_soln_chain.invoke({"bug_report": prepare_br(s2r, all_results)})
        logger.log(f"Generated suggestions: {alternate_soln_str}")
        
        # Check alternate solutions with crash checker
        crash_decision_alternate = crash_checker_chain.invoke({"s2r": str(s2r), "suggestions": alternate_soln_str})
        if crash_decision_alternate.decision == "NO":
          enhanced_s2r = enhance_s2r_chain.invoke({
              "initial_bug_report": initial_bug_report,
              "s2r": s2r,
              "suggestions": alternate_soln_str
          })
          logger.log("Enhanced S2R with the alternate suggestions.")
          logger.log(enhanced_s2r,"steps_to_reproduce")
        else:
          logger.log("Alternate solution suggestions didn't pass crash checker.")
          enhanced_s2r = s2r # Keep original s2r if alternate solutions fail crash check
    else:
        enhanced_s2r = s2r
    logger.log("Looking at mob interactions to enhance the S2R.")
    mob_checker_str = mob_checker_chain.invoke({"bug_report": prepare_br(enhanced_s2r, all_results)})
    logger.log(f"Generated suggestions for mob interactions: {mob_checker_str}")
    crash_decision = crash_checker_chain.invoke({"s2r": str(enhanced_s2r), "suggestions": mob_checker_str})
    if crash_decision.decision == "NO":
        enhanced_s2r = enhance_s2r_chain.invoke({
            "initial_bug_report": initial_bug_report,
            "s2r": enhanced_s2r,
            "suggestions": mob_checker_str
        })
        logger.log("Enhanced S2R with the mob interaction suggestions.")
        logger.log(enhanced_s2r,"steps_to_reproduce")
    else:
        logger.log("Mob checker suggestions didn't pass crash checker.")
    
    return enhanced_s2r

def process_clusters(enhanced_s2r):
    logger.log("Clustering the S2R steps.")
    clusters = step_cluster_chain.invoke({"bug_report": enhanced_s2r}).step_clusters
    clusters = array_to_dict([{"title": cluster.title, "steps": cluster.steps} for cluster in clusters])
    logger.log(clusters, "step_clusters")
    return clusters

def refine_clusters(clusters):
    logger.log("Refining the step clusters by checking if the steps are correctly placed.")
    cluster_feedback = cluster_check_chain.invoke({"step_clusters": clusters})
    logger.log(f"Cluster Feedback: {cluster_feedback}")
    clusters = cluster_rewrite_chain.invoke({"step_clusters": clusters, "feedback": cluster_feedback}).step_clusters
    clusters = array_to_dict([{"title": cluster.title, "steps": cluster.steps} for cluster in clusters])
    logger.log(clusters, "step_clusters")
    return clusters

def evaluate_images(clusters, all_results, image_codes, staged_files):  # Add staged_files parameter
    image_datas = {}
    logger.log("Image evaluation started")
    for image_code in image_codes:
        image_path = staged_files[image_code]  # Access from the passed dictionary
        with open(image_path, 'rb') as image_file:
            logger.log(f"Processing Image: {image_code}")
            image_byte = image_file.read()
            base64_encoded_data = base64.b64encode(image_byte)
            base64_string = base64_encoded_data.decode('utf-8')
            selected_step = step_selection_chain.invoke({
                "bug_report": prepare_br(clusters, all_results),
                "image_data": base64_string
            })
            image_datas[image_code] = selected_step  # Store result with the code
            logger.log({"file": image_code, "selection": selection_to_dict(selected_step)}, "image_step")
    return image_datas

def evaluate_videos(clusters, all_results, video_codes, staged_files):  # Add staged_files parameter
    video_datas = {}
    logger.log("Video evaluation started")
    for video_code in video_codes:
        video_path = staged_files[video_code]  # Access from the passed dictionary
        frames = get_first_frames_each_second_as_base64(video_path)
        frame_results = []
        running_summary = ""
        previous_frame_base64 = None  # Initialize previous frame variable
        selected_step = None  # Initialize selected_step variable

        for i, frame in enumerate(frames):
            if i == 0 or frame["base64"] != previous_frame_base64:  # Analyze only if it's the first frame or different from the previous one
                if i == 0:
                    selected_step = step_selection_chain.invoke({
                        "bug_report": prepare_br(clusters, all_results),
                        "image_data": frame["base64"]
                    })
                else:
                    selected_step = video_step_chain.invoke({
                        "bug_report": prepare_br(clusters, all_results),
                        "image_data": frame["base64"],
                        "summary": running_summary,
                        "conclusion": last_conclusion
                    })

                last_conclusion = selected_step.conclusion
                running_summary = running_summary_chain.invoke({
                    "previous_summary": running_summary,
                    "current_frame": selected_step.annotation
                })
                logger.log({"file": video_code, "selection": selection_to_dict(selected_step), "summary": running_summary, "timestamp": frame["timestamp"]}, "video_step")
                frame_results.append(selected_step)
                previous_frame_base64 = frame["base64"]  # Update previous frame
            else:
                # Log as skipped if the frame is the same as the previous
                logger.log({"file": video_code, "message": "Frame skipped (same as previous)", "timestamp": frame["timestamp"], "selection": selection_to_dict(frame_results[-1])}, "video_step")
                frame_results.append(frame_results[-1]) # Append the last result to maintain the list length

        video_datas[video_code] = frame_results  # Store results with the code
    return video_datas

def final_clustering(step_clusters, image_annotations, video_annotations):
    logger.log("Final clustering done based on image and video annotations.")
    relevant_images = {}
    for key in image_annotations:
        if image_annotations[key].conclusion != "NOT RELEVANT":
            relevant_images[key] = image_annotations[key]
    print(image_annotations)
    print(video_annotations)
    clusters =  final_cluster_chain.invoke({"bug_report": step_clusters, "image_annotations": image_annotations, "video_annotations": video_annotations}).step_clusters
    clusters = array_to_dict([{"title": cluster.title, "steps": cluster.steps} for cluster in clusters])
    logger.log(clusters, "step_clusters")
    return clusters
