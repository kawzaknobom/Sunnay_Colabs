import nest_asyncio,os
nest_asyncio.apply()

#########################################################

Bot_Token = os.getenv('TOKEN')

########################################################
from pyrogram import Client, filters,enums,StopTransmission,idle
from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply,Message
from pyrogram.errors import FloodWait
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from ultralytics import YOLO
from deepface import DeepFace
import torch
from transformers import CLIPProcessor, CLIPModel
import cv2,os,shutil,time,audioread
from math import ceil
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

model = YOLO('yolov8n.pt')
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
texts = ["a photo of a man", "a photo of a woman"]

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

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
Audio_Forms = (".mp3",".ogg",".m4a",".aac",".flac",".wav",".wma",".opus",".3gpp")

async def Create_Dir(Dir):
  if not os.path.isdir(Dir):
    os.makedirs(Dir, exist_ok=True)

async def Check_Dir(Dir):
  if os.path.isdir(Dir):
      shutil.rmtree(Dir)
  await Create_Dir(Dir)

async def Mp3_Conv(File):
  mainDir = '/'.join(File.split('/')[:-1]) + '/'
  Mp3_File = mainDir +  File.split('/')[-1].split('.')[0] + '_Conv.mp3'
  Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
  os.system(Mp3_Cmd)
  return Mp3_File

async def Media_Compress(file_path,Rate=None):
  mainDir = '/'.join(file_path.split('/')[:-1]) + '/'
  if file_path.lower().endswith(Audio_Forms) : 
   Res_File = mainDir + file_path.split('/')[-1].split('.')[0] + '_Comp.mp3'
   Comp_Cmd = f'ffmpeg -i "{file_path}" -b:a "{Rate}" "{Res_File}" -y '
  else :
    Res_File = mainDir + file_path.split('/')[-1].split('.')[0] + '_Comp.mp4'
    Comp_Cmd = f'ffmpeg -i "{file_path}" -c:v libx264 -crf 28 "{Res_File}" -y'
  os.system(Comp_Cmd)
  return Res_File

async def Vid_Mk(Vid,Aud):
  mainDir = '/'.join(Vid.split('/')[:-1]) + '/'
  Vid_Res = mainDir + Vid.split('/')[-1].split('.')[0] + '_Merged.mp4'
  Sub_Cmd = f'ffmpeg -i "{Vid}" -i "{Aud}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{Vid_Res}" -y'
  os.system(Sub_Cmd)
  return Vid_Res

def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  Session_file = Bot_Identifier+'_session_prm_bot'
  bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Bot_Token)
  return bot,Bot_Identifier

async def Get_Msg(bot,Chat_id,msg_id):
  try : 
     msg = await bot.get_messages(int(Chat_id),int(msg_id))
     return msg
  except FloodWait as e :
      time.sleep(e.value)
      return await Get_Msg(bot,Chat_id,msg_id)
  except Exception as err : 
      pass

   
async def detect_people_mediapipe(frame):
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
            
            
async def get_gender(frame):
    Women_Faces = []
    Men_Faces = []
    analysis = DeepFace.analyze(frame, actions=['gender'], detector_backend='retinaface',enforce_detection =False)
    for face in analysis :
       region = face['region']
       x, y, w, h = region['x'], region['y'], region['w'], region['h']
       if face['dominant_gender'] == 'Woman':
        Women_Faces.append((x,y,w,h))
       else : 
        Men_Faces.append((x,y,w,h))
    return Women_Faces,Men_Faces

async def get_persons(frame):
   last_known_people = []
   results = model.track(frame, persist=True, tracker="/content/Sunnay_Colabs/custom_tracker.yaml", classes=[0])
   for r in results:
         if r.boxes.id is not None:
            for box, track_id in zip(r.boxes.xyxy, r.boxes.id):
                track_id = int(track_id)
                x1, y1, x2, y2 = map(int, box)
                last_known_people.append((x1, y1, x2, y2))
   return last_known_people

async def is_body(facebbox,bodybboxlist):
            fx1, fy1, fx2, fy2 = facebbox
            for bodybbox in bodybboxlist :
               bx1, by1, bx2, by2 = bodybbox
               if (fx1 >= bx1 and fx2 <= bx2 and fy1 >= fy1 and fy2 <= by2) :
                  return bodybbox
            return False

async def get_bodies(facebboxlist,bodybboxlist):
  bodies = []
  for bodybbox in bodybboxlist :
      bx1, by1, bx2, by2 = bodybbox
      for facebbox in facebboxlist :
        fx1, fy1, fx2, fy2 = facebbox
        if (fx1 >= bx1 and fx2 <= bx2 and fy1 >= fy1 and fy2 <= by2) :
          bodies.append(bodybbox)
  return bodies


async def Blur_nonmale(file_path,method,replied):
  mainDir = '/'.join(file_path.split('/')[:-1]) + '/'
  P_Name = mainDir + file_path.split('/')[-1].split('.')[0]
  Ex = file_path.split('.')[-1]
  Res_File = f"{P_Name}_Blurred.{Ex}"
  file_path = await Media_Compress(file_path)
  cap = cv2.VideoCapture(file_path)
  if not cap.isOpened():
    raise ValueError("Error opening video file")
  fps = cap.get(cv2.CAP_PROP_FPS)
  totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
  durationInSeconds = totalNoFrames // fps
  Stream_Dur = int(durationInSeconds)
  width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
  height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
  fourcc = cv2.VideoWriter_fourcc(*'mp4v')
  out = cv2.VideoWriter(Res_File, fourcc, fps, (width, height))
  bodies_dict = {}
  last_update_time = 0
  start_point = False
  end_point = False
  ret_num = 0
  while(True):
    ret, frame = cap.read()
    if ret:
     ret_num += 1
     if ret_num == int(totalNoFrames) - int(fps) :
        end_point = True
     if (ret_num%(int(fps)*1) == 0) :
        text = f"{int(ret_num/fps)} seconds of {Stream_Dur} seconds"
        try :
          await replied.edit_text(text)
        except :
           pass
     if method == 'perframe' :
        last_known_people = await get_persons(frame)
        added_people = await detect_people_mediapipe(frame)
        for body in added_people : 
           last_known_people.append(body)
        Women_faces,Men_Faces = await get_gender(frame)
     elif method == 'persecond' :
      if (ret_num%(int(fps)*1) == 0) or start_point == False or end_point == True :
        last_known_people = await get_persons(frame)
        added_people = await detect_people_mediapipe(frame)
        for body in added_people : 
           last_known_people.append(body)
        Women_faces,Men_Faces = await get_gender(frame)
        start_point = True
     elif method == 'perhalfsecond' :
      if (ret_num%(int(int(fps)*0.5)) == 0) or start_point == False or end_point == True :
        last_known_people = await get_persons(frame)
        added_people = await detect_people_mediapipe(frame)
        for body in added_people : 
           last_known_people.append(body)
        Women_faces,Men_Faces = await get_gender(frame)
        start_point = True
     elif method == 'perqsecond' :
      if (ret_num%(int(int(fps)*0.3)) == 0) or start_point == False or end_point == True :
        last_known_people = await get_persons(frame)
        added_people = await detect_people_mediapipe(frame)
        for body in added_people : 
           last_known_people.append(body)
        Women_faces,Men_Faces = await get_gender(frame)
        start_point = True
    #  if ret_num == int(totalNoFrames) - int(fps)  :
    #     end_point = False
        # if len(Women_faces) == 0 :
        #   start_point = False      
        # else :
        #   start_point = True 
      
     if len(last_known_people) != 0 :
        men_bodies = await get_bodies(Men_Faces,last_known_people)
        lest_bodies = [item for item in last_known_people if item not in men_bodies]
        bodies_dict[ret_num] = lest_bodies
        last_known_people.clear()
        # for body in women_bodies :
        #    x1, y1, x2, y2 = body
        #    frame[y1:y2,x1:x2] = cv2.blur(frame[y1:y2, x1:x2], (499, 499))
     out.write(frame)
    else:
        break 
  cap.release()
  out.release()
  Res_File = await blurring(file_path,method,bodies_dict)
  return Res_File

async def get_gendernoface(frame,last_bodies):
          women = []
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
          return women

async def Blur_Female(file_path,method,replied):
  mainDir = '/'.join(file_path.split('/')[:-1]) + '/'
  P_Name = mainDir + file_path.split('/')[-1].split('.')[0]
  Ex = file_path.split('.')[-1]
  Res_File = f"{P_Name}_Blurred.{Ex}"
  file_path = await Media_Compress(file_path)
  cap = cv2.VideoCapture(file_path)
  if not cap.isOpened():
    raise ValueError("Error opening video file")
  fps = cap.get(cv2.CAP_PROP_FPS)
  totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
  durationInSeconds = totalNoFrames // fps
  Stream_Dur = int(durationInSeconds)
  width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
  height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
  fourcc = cv2.VideoWriter_fourcc(*'mp4v')
  out = cv2.VideoWriter(Res_File, fourcc, fps, (width, height))
  bodies_dict = {}
  last_update_time = 0
  start_point = False
  end_point = False
  ret_num = 0
  while(True):
    ret, frame = cap.read()
    if ret:
     ret_num += 1
     if ret_num == int(totalNoFrames) - int(fps) :
        end_point = True
     if (ret_num%(int(fps)*1) == 0) :
        text = f"{int(ret_num/fps)} seconds of {Stream_Dur} seconds"
        try :
          await replied.edit_text(text)
        except :
           pass
     if method == 'perframe' :
        last_known_people = await get_persons(frame)
        added_people = await detect_people_mediapipe(frame)
        for body in added_people : 
           last_known_people.append(body)
        Women_faces,Men_Faces = await get_gender(frame)
     elif method == 'persecond' :
      if (ret_num%(int(fps)*1) == 0) or start_point == False or end_point == True :
        last_known_people = await get_persons(frame)
        added_people = await detect_people_mediapipe(frame)
        for body in added_people : 
           last_known_people.append(body)
        Women_faces,Men_Faces = await get_gender(frame)
        start_point = True
     elif method == 'perhalfsecond' :
      if (ret_num%(int(int(fps)*0.5)) == 0) or start_point == False or end_point == True :
        last_known_people = await get_persons(frame)
        added_people = await detect_people_mediapipe(frame)
        for body in added_people : 
           last_known_people.append(body)
        Women_faces,Men_Faces = await get_gender(frame)
        start_point = True
     elif method == 'perqsecond' :
      if (ret_num%(int(int(fps)*0.3)) == 0) or start_point == False or end_point == True :
        last_known_people = await get_persons(frame)
        added_people = await detect_people_mediapipe(frame)
        for body in added_people : 
           last_known_people.append(body)
        Women_faces,Men_Faces = await get_gender(frame)
        start_point = True
    #  if ret_num == int(totalNoFrames) - int(fps)  :
    #     end_point = False
        # if len(Women_faces) == 0 :
        #   start_point = False      
        # else :
        #   start_point = True 
      
     if len(Women_faces) != 0 :
        women_bodies = await get_bodies(Women_faces,last_known_people)
        bodies_dict[ret_num] = women_bodies
        
        # for body in women_bodies :
        #    x1, y1, x2, y2 = body
        #    frame[y1:y2,x1:x2] = cv2.blur(frame[y1:y2, x1:x2], (499, 499))
     if len(last_known_people) != 0 :
        men_bodies = await get_bodies(Men_Faces,last_known_people)
        women_bodies = await get_bodies(Women_faces,last_known_people)
        lest_bodies = [item for item in last_known_people if item not in men_bodies]
        last_bodies = [item for item in lest_bodies if item not in women_bodies]
        if len(last_bodies) != 0 : 
          women = await get_gendernoface(frame,last_bodies)
          if len(women) != 0 :
              if ret_num in list(bodies_dict.keys()) :
                for bbx in women :  
                  bodies_dict[ret_num].append(bbx)
              else :   
                bodies_dict[ret_num] = women
        
     Women_faces.clear()
     last_known_people.clear()
     out.write(frame)
    else:
        break 
  cap.release()
  out.release()
  Res_File = await blurring(file_path,method,bodies_dict)
  return Res_File

async def blurring(file_path,method,bodies_dict):
  mainDir = '/'.join(file_path.split('/')[:-1]) + '/'
  P_Name = mainDir + file_path.split('/')[-1].split('.')[0]
  Ex = file_path.split('.')[-1]
  Res_File = f"{P_Name}_Blurred.{Ex}"
  Aud = await Mp3_Conv(file_path)
  cap = cv2.VideoCapture(file_path)
  if not cap.isOpened():
    raise ValueError("Error opening video file")
  fps = cap.get(cv2.CAP_PROP_FPS)
  totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
  durationInSeconds = totalNoFrames // fps
  Stream_Dur = int(durationInSeconds)
  width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
  height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
  fourcc = cv2.VideoWriter_fourcc(*'mp4v')
  out = cv2.VideoWriter(Res_File, fourcc, fps, (width, height))
  start_point = False 
  ret_num = 0
  while(True):
    ret, frame = cap.read()
    if ret:
     ret_num += 1
     frames = list(bodies_dict.keys())
     for ind in range(0,len(frames))  :
      if method in ['persecond','perhalfsecond','perqsecond'] :
        if method == 'persecond':
            
            if (ind == 0) :
               x = frames[ind] - int(fps)
            elif (frames[ind] - frames[ind-1] >= int(fps)*2) :
              x = frames[ind] - int(fps)
            elif frames[ind] - frames[ind-1] < int(fps)*2 :
               x = frames[ind] - int(fps)
              # x = frames[ind] - ceil((frames[ind] - frames[ind-1])/2)
            
            if (ind == len(frames)-1) :
              y = frames[ind] + int(fps)
            elif (frames[ind+1] - frames[ind] >= int(fps)*2) :
              y = frames[ind] + int(fps)
            elif frames[ind+1] - frames[ind] < int(fps)*2 :
                y = frames[ind] + int(fps)
               
              # y = frames[ind] + ceil((frames[ind+1] - frames[ind])/2)

        elif method == 'perhalfsecond':
            
            if (ind == 0) :
               x = frames[ind] - int(fps)
            elif (frames[ind] - frames[ind-1] >= int(fps)) :
              x = frames[ind] - int(fps)
            elif frames[ind] - frames[ind-1] < int(fps) :
               x = frames[ind] - int(fps)
              # x = frames[ind] - ceil((frames[ind] - frames[ind-1])/2)
            
            if (ind == len(frames)-1) :
               y = frames[ind] + int(fps)
            elif (frames[ind+1] - frames[ind] >= int(fps)) :
              y = frames[ind] + int(fps)
            elif frames[ind+1] - frames[ind] < int(fps) :
                y = frames[ind] + int(fps)
              # y = frames[ind] + ceil((frames[ind+1] - frames[ind])/2)

        elif method == 'perqsecond':
            
            if (ind == 0) :
               x = frames[ind] - int(fps)
            elif (frames[ind] - frames[ind-1] >= int(int(fps)*2/3)) :
              x = frames[ind] - int(fps)
            elif frames[ind] - frames[ind-1] < int(int(fps)*2/3) :
               x = frames[ind] - int(fps)
              # x = frames[ind] - ceil((frames[ind] - frames[ind-1])/2)
            
            if (ind == len(frames)-1) :
               y = frames[ind] + int(fps)
            elif (frames[ind+1] - frames[ind] >= int(int(fps)*2/3)) :
              y = frames[ind] + int(fps)
            elif frames[ind+1] - frames[ind] < int(int(fps)*2/3) :
                y = frames[ind] + int(fps)
              # y = frames[ind] + ceil((frames[ind+1] - frames[ind])/2)

        if ret_num in range(x,y):
            women_bodies = bodies_dict[frames[ind]]
            for body in women_bodies :
              x1, y1, x2, y2 = body
              frame[y1:y2,x1:x2] = cv2.blur(frame[y1:y2, x1:x2], (499, 499)) 
            break
        
      elif method == 'perframe':
           if ret_num == frames[ind] :
            women_bodies = bodies_dict[frames[ind]]
            for body in women_bodies :
              x1, y1, x2, y2 = body
              frame[y1:y2,x1:x2] = cv2.blur(frame[y1:y2, x1:x2], (499, 499)) 
            break
      
     out.write(frame)
    else:
        break 
  cap.release()
  out.release()  
  Res_File = await Vid_Mk(Res_File,Aud)
  Res_File = await Media_Compress(Res_File)
  return Res_File

bot,Bot_Identifier = Pyrogram_Client(Bot_Token)
Dl_Dir = f'./Blur_{Bot_Identifier}/'


@bot.on_message(filters.command('start') & filters.private)
async def command1(bot,message):
   await message.reply('لبقية البوتات \n\n @sunnaybots')

@bot.on_message(filters.private & filters.incoming & ( filters.video))
async def _telegram_file(client, message):
  if message.video :
  #  Reply = await message.reply('جار العمل ...')
  #  Vid_Path = await message.download(file_name=Dl_Dir)
  #  Blurred_Vid = await Blur_Female(Vid_Path)
   CHOOSE_UR_BUTTONS = [
      [InlineKeyboardButton("Blur Female",callback_data='blurfemale'+'_'+str(message.id))],
      [InlineKeyboardButton("Blur Non-Male",callback_data='blurnonmale'+'_'+str(message.id))] ]
   await message.reply(text = "اختر ما يناسب",reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))
  #  await Reply.edit_text('تمت ')
  #  await Check_Dir(Dl_Dir)


@bot.on_callback_query()
async def callback_query(CLIENT,CallbackQuery):
  User_Id = CallbackQuery.from_user.id
  Callback_List = CallbackQuery.data.split('_')
  Method = Callback_List[0]
  Msg_Id = Callback_List[-1]
  if Method in ['blurfemale','blurnonmale']:
    CHOOSE_UR_BUTTONS = [
      [InlineKeyboardButton("Per Second",callback_data='persecond' + '_'+ Method + '_' + Msg_Id)],
      [InlineKeyboardButton("Per Half Second",callback_data='perhalfsecond' + '_' + Method + '_' + Msg_Id)],
      [InlineKeyboardButton("Per Quarter Second",callback_data='perqsecond' + '_'+ Method + '_' + Msg_Id)],
      [InlineKeyboardButton("Per Frame",callback_data='perframe'+'_'+ Msg_Id)]
        ]
    await CallbackQuery.edit_message_text(text = 'اختر',reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))

     
  elif Method in ['persecond','perhalfsecond','perqsecond','perframe'] :
    Method2 = Callback_List[1]
    file_msg = await Get_Msg(bot,User_Id,Msg_Id)
    replied = await CallbackQuery.edit_message_text('جار العمل ...')
    Vid_Path = await file_msg.download(file_name=Dl_Dir)
    if Method2 == 'blurfemale' :
      Blurred_Vid = await Blur_Female(Vid_Path,Method,replied)
    elif Method2 == 'blurnonmale':
       Blurred_Vid = await Blur_nonmale(Vid_Path,Method,replied)
    await replied.edit_text('تمت')
    await file_msg.reply_video(Blurred_Vid)
    await Check_Dir(Dl_Dir)


def main():
    if not os.path.exists(Dl_Dir): os.makedirs(Dl_Dir)
    try:
        bot.start()
        print("✅ Blur Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()