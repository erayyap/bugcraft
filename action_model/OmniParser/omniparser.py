from action_model.OmniParser.utils import get_som_labeled_img, check_ocr_box, get_caption_model_processor, get_yolo_model
import torch
from PIL import Image
import importlib
import utils
import base64
import io
import time
import os

class OmniParser:
    def __init__(self, model_path, device='cuda'):
        """
        Initializes the OmniParser with necessary models and configurations.

        Args:
            model_path (str): Path to the YOLO model.
            device (str): Device to run the models on ('cuda' or 'cpu').
        """
        self.device = device
        self.model_path = model_path

        self.som_model = get_yolo_model(self.model_path)
        self.som_model.to(self.device)
        print(f'Model loaded to {self.device}')

        # Initialize caption model and processor (choose one)
        importlib.reload(utils)
        # self.caption_model_processor = get_caption_model_processor(model_name="blip2", model_name_or_path="weights/icon_caption_blip2", device=self.device)
        florence_path = os.getenv("FLORENCE_PATH") or "C:/Users/author_1/Documents/GitHub/bugcraft/action_model/OmniParser/weights/icon_caption_florence"
        self.caption_model_processor = get_caption_model_processor(model_name="florence2", model_name_or_path=florence_path, device=self.device)
        
        self.BOX_TRESHOLD = 0.05

    def __call__(self, image_path):
        """
        Processes an image and returns the annotated image with bounding boxes.

        Args:
            image_path (str): Path to the input image.

        Returns:
            Image: Annotated PIL Image object with bounding boxes drawn.
        """
        image = Image.open(image_path) # this is the fix

        box_overlay_ratio = max(image.size) / 3200
        draw_bbox_config = {
            'text_scale': 0.8 * box_overlay_ratio,
            'text_thickness': max(int(2 * box_overlay_ratio), 1),
            'text_padding': max(int(3 * box_overlay_ratio), 1),
            'thickness': max(int(3 * box_overlay_ratio), 1),
        }

        return self.process_image(image_path, draw_bbox_config, self.BOX_TRESHOLD)

    def process_image(self, image_path, draw_bbox_config, BOX_TRESHOLD=0.05):
        """
        Processes an image using OCR and a SOM model, generates a labeled image.

        Args:
            image_path (str): Path to the input image.
            draw_bbox_config (dict): Configuration for drawing bounding boxes.
            BOX_TRESHOLD (float): Confidence threshold for object detection.

        Returns:
            Image: Annotated PIL Image object.
        """
        image = Image.open(image_path) # added this here too
        image_rgb = image.convert('RGB')
        print('image size:', image.size)

        start = time.time()
        # OCR
        ocr_bbox_rslt, _ = check_ocr_box(image_path, display_img=False, output_bb_format='xyxy', goal_filtering=None, easyocr_args={'paragraph': False, 'text_threshold': 0.8}, use_paddleocr=False)
        text, ocr_bbox = ocr_bbox_rslt
        cur_time_ocr = time.time()

        # SOM Labeling
        dino_labled_img, _, parsed_content_list = get_som_labeled_img(image_path, self.som_model, BOX_TRESHOLD=BOX_TRESHOLD, output_coord_in_ratio=True, ocr_bbox=ocr_bbox, draw_bbox_config=draw_bbox_config, caption_model_processor=self.caption_model_processor, ocr_text=text, use_local_semantics=True, iou_threshold=0.7, scale_img=False, batch_size=128)
        cur_time_caption = time.time()

        # Convert base64 string back to PIL Image
        annotated_image = Image.open(io.BytesIO(base64.b64decode(dino_labled_img)))

        print(f"Time taken for OCR: {cur_time_ocr - start:.2f} seconds")
        print(f"Time taken for captioning and labeling: {cur_time_caption - cur_time_ocr:.2f} seconds")

        return annotated_image, parsed_content_list

if __name__ == "__main__":
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model_path = 'C:\\Users\\author_1\\Desktop\\kod\\research\\action_model\\OmniParser\\weights\\icon_detect_v1_5\\model_v1_5.pt'
    # Initialize the ImageAnnotator
    annotator = OmniParser(model_path, device=device)

    # Example usage:
    #image_path = 'imgs/word.png'
    image_path = 'imgs/omni3.jpg'

    # Process the image using the __call__ method
    annotated_image, content_list = annotator(image_path)  # Pass image path

    # Display or save the annotated image
    # annotated_image.show()
    annotated_image.save("annotated_image.jpg")
    print(content_list)