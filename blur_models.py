import cv2

###### Yolo Detect Model ##### 

from ultralytics import YOLO

Yolo_Model = YOLO('yolov8n.pt')

async def Yolo_Detect(frame):
   last_known_people = []
   results = Yolo_Model.track(frame, persist=True, tracker="/content/Sunnay_Colabs/custom_tracker.yaml", classes=[0])
   for r in results:
         if r.boxes.id is not None:
            for box, track_id in zip(r.boxes.xyxy, r.boxes.id):
                track_id = int(track_id)
                x1, y1, x2, y2 = map(int, box)
                last_known_people.append((x1, y1, x2, y2))
   return last_known_people

##### MediaPipe Model ### 

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


model_path = 'efficientdet.tflite'
BaseOptions = mp.tasks.BaseOptions
ObjectDetector = mp.tasks.vision.ObjectDetector
ObjectDetectorOptions = mp.tasks.vision.ObjectDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = ObjectDetectorOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    score_threshold=0.5, # Minimum confidence
    running_mode=VisionRunningMode.IMAGE
)

mp_detector =  ObjectDetector.create_from_options(options)


async def MediaPipe_Detect(frame):
    people = []
    bgr_image = frame
    h, w, _ = bgr_image.shape
    
    # MediaPipe expects RGB format
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

    detection_result = mp_detector.detect(mp_image)

    for detection in detection_result.detections:
        category = detection.categories[0]
        if category.category_name == 'person':
            bbox = detection.bounding_box
            xmin = bbox.origin_x
            ymin = bbox.origin_y
            width = bbox.width
            height = bbox.height
            bbbox = (xmin, ymin , xmin + width, ymin + height)
            people.append(bbbox)
    return people

####### DeepFace Gender Model #####

from deepface import DeepFace

async def DF_GDetect(frame,last_bodies):
    Women_Faces = []
    Men_Faces = []
    for body in last_bodies : 
      x1, y1, x2, y2 = body
      full_body = frame[y1:y2,x1:x2]
      analysis = DeepFace.analyze(full_body, actions=['gender'], detector_backend='retinaface',enforce_detection =False)
      for face in analysis :
            region = face['region']
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            if face['dominant_gender'] == 'Woman':
                Women_Faces.append(body)
            else : 
                Men_Faces.append(body)
    return Women_Faces,Men_Faces

####### Clip Gender Model #### 

import torch
from transformers import CLIPProcessor, CLIPModel
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
texts = ["a photo of a man", "a photo of a woman"]

async def Clip_GDetect(frame,last_bodies):
          women = []
          Men = []
          for body in last_bodies:
            # pil_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            # pil_crop = Image.fromarray(pil_crop)
            x1, y1, x2, y2 = map(int, body)
            img_crop = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]
            img_rgb = cv2.cvtColor(img_crop, cv2.COLOR_BGR2RGB)
            inputs = clip_processor(
            text=texts, 
            images=img_rgb, 
            return_tensors="pt", 
            padding=True
        )
            with torch.no_grad():
                outputs = clip_model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1)[0]
            gender = "man" if probs[0] > probs[1] else "woman"
            if gender == 'woman' :
              women.append(body)
            elif gender == 'man' :
                Men.append(body)
          return women,Men
