from utils import get_som_labeled_img, check_ocr_box, get_caption_model_processor, get_yolo_model
import torch
from ultralytics import YOLO
from PIL import Image
import importlib
import utils
import base64
import matplotlib.pyplot as plt
import io
import time
import os

def process_image_and_save_output(image_path, output_folder, som_model, caption_model_processor, draw_bbox_config, BOX_TRESHOLD=0.05):
    """
    Processes an image using OCR and a SOM model, generates a labeled image,
    displays parsed content with pixel coordinates, and saves the output image and data.

    Args:
        image_path (str): Path to the input image.
        output_folder (str): Path to the folder where output will be saved.
        som_model (YOLO): The YOLO model for object detection.
        caption_model_processor (tuple): Tuple containing the caption model and processor.
        draw_bbox_config (dict): Configuration for drawing bounding boxes.
        BOX_TRESHOLD (float): Confidence threshold for object detection.
    """

    image = Image.open(image_path)
    image_rgb = image.convert('RGB')
    image_width, image_height = image.size
    print('image size:', image.size)

    start = time.time()
    ocr_bbox_rslt, is_goal_filtered = check_ocr_box(image_path, display_img=False, output_bb_format='xyxy', goal_filtering=None, easyocr_args={'paragraph': False, 'text_threshold': 0.8}, use_paddleocr=False)
    text, ocr_bbox = ocr_bbox_rslt
    cur_time_ocr = time.time()

    dino_labled_img, label_coordinates, parsed_content_list = get_som_labeled_img(image_path, som_model, BOX_TRESHOLD=BOX_TRESHOLD, output_coord_in_ratio=True, ocr_bbox=ocr_bbox, draw_bbox_config=draw_bbox_config, caption_model_processor=caption_model_processor, ocr_text=text, use_local_semantics=True, iou_threshold=0.7, scale_img=False, batch_size=128)
    cur_time_caption = time.time()

    # Convert bounding box coordinates from ratio to pixels
    for item in parsed_content_list:
        x_min, y_min, x_max, y_max = item['bbox']
        item['bbox'] = [
            int(x_min * image_width),
            int(y_min * image_height),
            int(x_max * image_width),
            int(y_max * image_height),
        ]

    # Save the labeled image
    image = Image.open(io.BytesIO(base64.b64decode(dino_labled_img)))
    output_image_path = os.path.join(output_folder, os.path.basename(image_path).replace('.', '_labeled.'))
    image.save(output_image_path)
    print(f"Labeled image saved to: {output_image_path}")

    # Display and save parsed content with pixel coordinates
    display_parsed_content(parsed_content_list)
    output_data_path = os.path.join(output_folder, os.path.basename(image_path).replace('.', '_data.txt'))
    with open(output_data_path, 'w') as f:
        f.write("-" * 50 + "\n")
        f.write("{:<5} {:<10} {:<50} {:<15} {:<20}\n".format("ID", "Type", "Bbox", "Interactivity", "Content"))
        f.write("-" * 50 + "\n")
        for i, item in enumerate(parsed_content_list):
            f.write("{:<5} {:<10} {:<50} {:<15} {:<20}\n".format(i, item['type'], str(item['bbox']), str(item['interactivity']), item['content']))
        f.write("-" * 50 + "\n")
    print(f"Parsed content saved to: {output_data_path}")

    print(f"Time taken for OCR: {cur_time_ocr - start:.2f} seconds")
    print(f"Time taken for captioning and labeling: {cur_time_caption - cur_time_ocr:.2f} seconds")

def display_parsed_content(parsed_content_list):
    """Displays the parsed content list in a tabular format without using pandas."""
    print("-" * 50)
    print("{:<5} {:<10} {:<50} {:<15} {:<20}".format("ID", "Type", "Bbox", "Interactivity", "Content"))
    print("-" * 50)
    for i, item in enumerate(parsed_content_list):
        print("{:<5} {:<10} {:<50} {:<15} {:<20}".format(i, item['type'], str(item['bbox']), str(item['interactivity']), item['content']))
    print("-" * 50)

if __name__ == "__main__":
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model_path = './weights/icon_detect_v1_5/model_v1_5.pt'
    output_folder = 'output_images'  # Folder to save output images and data

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    som_model = get_yolo_model(model_path)
    som_model.to(device)
    print('model to {}'.format(device))

    # two choices for caption model: fine-tuned blip2 or florence2
    importlib.reload(utils)
    # caption_model_processor = get_caption_model_processor(model_name="blip2", model_name_or_path="weights/icon_caption_blip2", device=device)
    caption_model_processor = get_caption_model_processor(model_name="florence2", model_name_or_path="weights/icon_caption_florence", device=device)

    print(som_model.device, type(som_model))

    # reload utils
    importlib.reload(utils)

    #image_path = 'imgs/word.png'
    image_path = 'imgs/omni3.jpg' # you can test with another image

    image = Image.open(image_path)
    box_overlay_ratio = max(image.size) / 3200
    draw_bbox_config = {
        'text_scale': 0.8 * box_overlay_ratio,
        'text_thickness': max(int(2 * box_overlay_ratio), 1),
        'text_padding': max(int(3 * box_overlay_ratio), 1),
        'thickness': max(int(3 * box_overlay_ratio), 1),
    }
    BOX_TRESHOLD = 0.05

    process_image_and_save_output(image_path, output_folder, som_model, caption_model_processor, draw_bbox_config, BOX_TRESHOLD)