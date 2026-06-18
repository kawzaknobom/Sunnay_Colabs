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
from blur_models import Yolo_Detect,MediaPipe_Detect,DF_GDetect,Clip_GDetect

import cv2,os,shutil,time,audioread
from math import ceil
from dataclasses import dataclass

Rangers = {}
Raangers = {}

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

     
#########

async def get_seconds(clock_time) :
    splitted = clock_time.split(':')
    if len(splitted) == 3 : 
      hours, minutes, seconds = map(int, clock_time.split(':'))
    elif len(splitted) == 2 : 
      minutes = int(splitted[0])
      seconds = int(splitted[-1])
      hours = 0
    total_seconds = (hours * 3600) + (minutes * 60) + seconds
    return total_seconds

async def Raw_Blur(file_path,replied,Detect_Range):
  mainDir = '/'.join(file_path.split('/')[:-1]) + '/'
  P_Name = mainDir + file_path.split('/')[-1].split('.')[0]
  Ex = file_path.split('.')[-1]
  Res_File = f"{P_Name}_Blurred.{Ex}"
  Aud = await Mp3_Conv(file_path)
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
  if not Detect_Range == 'Dfull' :
    Ranges = Detect_Range.split('|')
    ranges = []
    for Range in Ranges : 
      splitted = Range.split('-') 
      start = await get_seconds(splitted[0])
      end  = await get_seconds(splitted[1])
      ranges.append([int(start*fps),int((end+1)*fps)])


  while(True):
    ret, frame = cap.read()
    if ret:
     ret_num += 1
     if Detect_Range == 'Dfull' :
       ispermit = True
     else :
        ispermit = False
        for x in ranges :
         if ret_num in range(x[0],x[1]):
           ispermit = True
           break   
     if ispermit : 
       frame = cv2.blur(frame, (499, 499))
     out.write(frame)
    else:
        break 
  cap.release()
  out.release()
  Res_File = await Vid_Mk(Res_File,Aud)
  Res_File = await Media_Compress(Res_File)
  return Res_File

async def Blur_Female(file_path,replied,Detect_Model,BlurObject,Gender_Model,Detect_Interval,Detect_Range):
  if Detect_Model == 'Yolo' :
     PPL_Detect = Yolo_Detect
  elif Detect_Model == 'MediaPipe': 
     PPL_Detect = MediaPipe_Detect
  if BlurObject == 'blurfml' :
    gender_class = True
    if Gender_Model == 'DeepFace' :
      Gender_Detect = DF_GDetect
    elif Gender_Model == 'Clip' :
      Gender_Detect = Clip_GDetect
  else : 
     gender_class = False
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
  Women,Men = [] , []
  if not Detect_Range == 'Dfull' :
    Ranges = Detect_Range.split('|')
    ranges = []
    for Range in Ranges : 
      splitted = Range.split('-') 
      start = await get_seconds(splitted[0])
      end  = await get_seconds(splitted[1])
      ranges.append([int(start*fps),int((end+1)*fps)])


  while(True):
    ret, frame = cap.read()
    if ret:
     ret_num += 1
     if Detect_Range == 'Dfull' :
       ispermit = True
     else :
        ispermit = False
        for x in ranges :
         if ret_num in range(x[0],x[1]):
           ispermit = True
           break   
  
     if (ret_num == int(totalNoFrames) - int(fps)) and ispermit :
        end_point = True
     if (ret_num%(int(fps)*1) == 0) and ispermit :
        text = f"{int(ret_num/fps)} seconds of {Stream_Dur} seconds"
        try :
          await replied.edit_text(text)
        except :
           pass
     if (Detect_Interval == 'perframe') and ispermit :
        last_known_people = await PPL_Detect(frame)
        if gender_class :
          Women,Men = await Gender_Detect(frame,last_known_people)
     elif (Detect_Interval == 'persecond') and ispermit :
      if (ret_num%(int(fps)*1) == 0) or start_point == False or end_point == True :
        last_known_people = await PPL_Detect(frame)
        if gender_class :
          Women,Men = await Gender_Detect(frame,last_known_people)
        start_point = True
     elif (Detect_Interval == 'perhalfsecond') and ispermit :
      if (ret_num%(int(int(fps)*0.5)) == 0) or start_point == False or end_point == True :
        last_known_people = await PPL_Detect(frame)
        if gender_class :
          Women,Men = await Gender_Detect(frame,last_known_people)
        start_point = True
     elif (Detect_Interval == 'perqsecond') and ispermit :
      if (ret_num%(int(int(fps)*0.3)) == 0) or start_point == False or end_point == True :
        last_known_people = await PPL_Detect(frame)
        if gender_class :
          Women,Men = await Gender_Detect(frame,last_known_people)
        start_point = True
  
     if (BlurObject == 'blurfml') and ispermit :
      if len(Women) != 0 :
        bodies_dict[ret_num] = Women.copy()
     elif (BlurObject == 'blurppl') and ispermit :
       if len(last_known_people) != 0 :
        bodies_dict[ret_num] = last_known_people.copy()
       
     
        # for body in women_bodies :
        #    x1, y1, x2, y2 = body
        #    frame[y1:y2,x1:x2] = cv2.blur(frame[y1:y2, x1:x2], (499, 499))
     if ispermit  :
      if gender_class :
        Women.clear()
        Men.clear()
      last_known_people.clear()
     out.write(frame)
    else:
        break 
  cap.release()
  out.release()
  Res_File = await blurring(file_path,Detect_Interval,bodies_dict)
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
        x = frames[ind] - int(fps)
        y = frames[ind] + int(fps)

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
   Text = 'اختر ما يناسب '
   CHOOSE_UR_BUTTONS = [
      [InlineKeyboardButton("Detect & Blur",callback_data=f'DB_{message.id}')],
      [InlineKeyboardButton("Blur Only",callback_data=f'BO_{message.id}')]]
   
   await message.reply(text = Text ,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))
  #  await Reply.edit_text('تمت ')
  #  await Check_Dir(Dl_Dir)

callback_dict = {}

@bot.on_callback_query()
async def callback_query(CLIENT,CallbackQuery):
  User_Id = CallbackQuery.from_user.id
  Callback_List = CallbackQuery.data.split('_')
  Msg_Id = Callback_List[-1]
  if not User_Id in list(callback_dict.keys()) :
    callback_dict[User_Id] = [Msg_Id,]
  
  if any(word in CallbackQuery.data for word in ['DB','BO']):
   Blur_Mode = Callback_List[0]
   callback_dict[User_Id].append(Blur_Mode)
   if Blur_Mode == 'DB' : 
    Text = 'اختر نموذج التعرف'
    CHOOSE_UR_BUTTONS = [
      [InlineKeyboardButton("Yolo",callback_data=f'Yolo_{Msg_Id}')],
      [InlineKeyboardButton("MediaPipe",callback_data=f'MediaPipe_{Msg_Id}')]]
    await CallbackQuery.edit_message_text(text = Text,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))   
   
   else :
     Text = 'اختر نمط البلور'
     CHOOSE_UR_BUTTONS = [
      [InlineKeyboardButton("Blur Full Vid",callback_data=f'dfull_{Msg_Id}')],
        [InlineKeyboardButton("Blur Ranges",callback_data=f'dparts_{Msg_Id}')]
        ]
          
     await CallbackQuery.edit_message_text(text = Text,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))   


  elif any(word in CallbackQuery.data for word in ['dfull','dparts']):
      file_msg = await Get_Msg(bot,User_Id,Msg_Id)
      if Callback_List[1] == 'dfull' : 
        replied = await CallbackQuery.edit_message_text('جار العمل ...')
        Vid_Path = await file_msg.download(file_name=Dl_Dir)
        Blurred_Vid = await Raw_Blur(Vid_Path,replied,"Dfull")
        await replied.edit_text('تمت')
        await file_msg.reply_video(Blurred_Vid)
        await Check_Dir(Dl_Dir)
        callback_dict.pop(User_Id)
      else : 
       Text = '''الآن أرسل المدى بهذه الصورة
         hh:mm:ss-hh:mm:ss
         ويمكنك إرسال أكثر من مدى بهذه الصورة بترك مسافة بين كل مدى
         hh:mm:ss-hh:mm:ss hh:mm:ss-hh:mm:ss hh:mm:ss-hh:mm:ss
         '''
       await CallbackQuery.message.delete()
       await file_msg.reply_text(Text,reply_markup=ForceReply(True),reply_to_message_id=file_msg.id)
    
  elif any(word in CallbackQuery.data for word in ['Yolo','MediaPipe']):
      Detect_Model = Callback_List[0]
      callback_dict[User_Id].append(Detect_Model)
      Text = 'اختر غرض الحجب  '
      CHOOSE_UR_BUTTONS = [
        [InlineKeyboardButton("Blur All ppl",callback_data=f'blurppl_{Msg_Id}')],
        [InlineKeyboardButton("Blur Female",callback_data=f'blurfml_{Msg_Id}')]
          ]
      await CallbackQuery.edit_message_text(text = Text,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))   

  elif any(word in CallbackQuery.data for word in ['blurfml']):

      BlurObject = Callback_List[0]
      callback_dict[User_Id].append(BlurObject)
      if BlurObject == 'blurfml':

        Text = 'اختر نموذج تمييز الجنس'
        CHOOSE_UR_BUTTONS = [
          [InlineKeyboardButton("DeepFace",callback_data=f'DeepFace_{Msg_Id}')],
          [InlineKeyboardButton("Clip",callback_data=f'Clip_{Msg_Id}')]
            ]
        await CallbackQuery.edit_message_text(text = Text,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))   
      

  elif any(word in CallbackQuery.data for word in ['DeepFace','Clip','blurppl']):
    Gender_Model = Callback_List[0]
    callback_dict[User_Id].append(Gender_Model)
    Text = 'اختر مدة التعرف '
    CHOOSE_UR_BUTTONS = [
      [InlineKeyboardButton("Per Second",callback_data=f'persecond_{Msg_Id}')],
      [InlineKeyboardButton("Per Half Second",callback_data=f'perhalfsecond_{Msg_Id}')],
      [InlineKeyboardButton("Per Quarter Second",callback_data=f'perqsecond_{Msg_Id}')],
      [InlineKeyboardButton("Per Frame",callback_data=f'perframe_{Msg_Id}')]
         ]
    await CallbackQuery.edit_message_text(text = Text,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))   
  
  elif any(word in CallbackQuery.data for word in ['persecond','perhalfsecond','perqsecond','perframe']): 
    Detect_Interval = Callback_List[0]
    callback_dict[User_Id].append(Detect_Interval)
    Text = 'اختر نمط البلور'
    CHOOSE_UR_BUTTONS = [
    [InlineKeyboardButton("Detect Full Vid",callback_data=f'Dfull_{Msg_Id}')],
      [InlineKeyboardButton("Detect Ranges",callback_data=f'Dparts_{Msg_Id}')]
       ]
        
    await CallbackQuery.edit_message_text(text = Text,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))   

  
  elif any(word in CallbackQuery.data for word in ['Dfull','Dparts']): 
    Detect_Range = Callback_List[0]
    if len(callback_dict[User_Id]) == 6 :
        Blur_Mode = callback_dict[User_Id][1]
        Detect_Model = callback_dict[User_Id][2]
        BlurObject = callback_dict[User_Id][3]
        Gender_Model = callback_dict[User_Id][4]
        Detect_Interval = callback_dict[User_Id][5]
    elif len(callback_dict[User_Id]) == 5 :
        Blur_Mode = callback_dict[User_Id][1]
        Detect_Model = callback_dict[User_Id][2]
        BlurObject = 'blurppl'
        Gender_Model = 'Nomodel'
        Detect_Interval = callback_dict[User_Id][4]
    file_msg = await Get_Msg(bot,User_Id,Msg_Id)
    if Detect_Range == 'Dparts':
       Rangers[User_Id] = [Msg_Id,Detect_Model,BlurObject,Gender_Model,Detect_Interval]
       Text = '''الآن أرسل المدى بهذه الصورة
         hh:mm:ss-hh:mm:ss
         ويمكنك إرسال أكثر من مدى بهذه الصورة بترك مسافة بين كل مدى
         hh:mm:ss-hh:mm:ss hh:mm:ss-hh:mm:ss hh:mm:ss-hh:mm:ss
         '''
       await CallbackQuery.message.delete()
       await file_msg.reply_text(Text,reply_markup=ForceReply(True),reply_to_message_id=file_msg.id)
    else : 
      replied = await CallbackQuery.edit_message_text('جار العمل ...')
      Vid_Path = await file_msg.download(file_name=Dl_Dir)
      
      Blurred_Vid = await Blur_Female(Vid_Path,replied,Detect_Model,BlurObject,Gender_Model,Detect_Interval,Detect_Range)
      await replied.edit_text('تمت')
      await file_msg.reply_video(Blurred_Vid)
      await Check_Dir(Dl_Dir)
      callback_dict.pop(User_Id)


@bot.on_message(filters.private & filters.reply)
async def refunc(client,message):
   if (message.reply_to_message.reply_markup) and isinstance(message.reply_to_message.reply_markup, ForceReply)  :
    User_Id = message.from_user.id
    if User_Id in list(Rangers.keys()) : 
      Msg_Text = message.text
      reply_id = message.reply_to_message_id
      reply_msg = await Get_Msg(bot,User_Id,reply_id)
      await message.delete()
      await reply_msg.delete()
      Ranges = Msg_Text.replace(' ','|')
      file_msg = await Get_Msg(bot,User_Id,Rangers[User_Id][0])
      replied = await file_msg.reply('جار العمل ...')
      Vid_Path = await file_msg.download(file_name=Dl_Dir)
      Detect_Model = Rangers[User_Id][1]
      BlurObject = Rangers[User_Id][2]
      Gender_Model = Rangers[User_Id][3]
      Detect_Interval = Rangers[User_Id][4]
      Blurred_Vid = await Blur_Female(Vid_Path,replied,Detect_Model,BlurObject,Gender_Model,Detect_Interval,Ranges)
      await replied.edit_text('تمت')
      await file_msg.reply_video(Blurred_Vid)
      await Check_Dir(Dl_Dir)
      callback_dict.pop(User_Id)
    else : 
      User_Id = message.from_user.id
      Msg_Text = message.text
      reply_id = message.reply_to_message_id
      reply_msg = await Get_Msg(bot,User_Id,reply_id)
      file_id = reply_msg.reply_to_message_id
      file_msg = await Get_Msg(bot,User_Id,file_id)
      await message.delete()
      await reply_msg.delete()
      Ranges = Msg_Text.replace(' ','|')
      replied = await file_msg.reply('جار العمل ...')
      Vid_Path = await file_msg.download(file_name=Dl_Dir)
      Blurred_Vid = await Raw_Blur(Vid_Path,replied,Ranges)
      await replied.edit_text('تمت')
      await file_msg.reply_video(Blurred_Vid)
      await Check_Dir(Dl_Dir)
      callback_dict.pop(User_Id)

     


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