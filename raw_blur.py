import nest_asyncio,os
nest_asyncio.apply()

#########################################################

Bot_Token = os.getenv('TOKEN')

########################################################

from pyrogram import Client, filters,enums,StopTransmission,idle
from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply,Message,ReplyKeyboardMarkup, KeyboardButton
from pyrogram.errors import FloodWait
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
import shutil,os,time,cv2,random
from math import ceil

Blur_Dict = {}

#######


def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  Session_file = Bot_Identifier+'_session_prm_bot'
  bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Bot_Token)
  return bot,Bot_Identifier


Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'

bot,Bot_Identifier = Pyrogram_Client(Bot_Token)

#####


def Create_Dir(Dir):
  if not os.path.isdir(Dir):
    os.makedirs(Dir, exist_ok=True)

def Check_Dir(Dir):
  if os.path.isdir(Dir):
      shutil.rmtree(Dir)
  Create_Dir(Dir)

def Mp3_Conv(File):
  mainDir = '/'.join(File.split('/')[:-1]) + '/'
  Mp3_File = mainDir +  File.split('/')[-1].split('.')[0] + '_Conv.mp3'
  Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
  os.system(Mp3_Cmd)
  return Mp3_File

def Media_Compress(file_path,Rate=None):
  mainDir = '/'.join(file_path.split('/')[:-1]) + '/'
  Res_File = mainDir + file_path.split('/')[-1].split('.')[0] + '_Comp.mp4'
  Comp_Cmd = f'ffmpeg -i "{file_path}" -c:v libx264 -crf 28 "{Res_File}" -y'
  os.system(Comp_Cmd)
  return Res_File

def Vid_Mk(Vid,Aud):
  mainDir = '/'.join(Vid.split('/')[:-1]) + '/'
  Vid_Res = mainDir + Vid.split('/')[-1].split('.')[0] + '_Merged.mp4'
  Sub_Cmd = f'ffmpeg -i "{Vid}" -i "{Aud}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{Vid_Res}" -y'
  os.system(Sub_Cmd)
  return Vid_Res

def Get_Msg(bot,Chat_id,msg_id):
  try : 
     msg = bot.get_messages(int(Chat_id),int(msg_id))
     return msg
  except FloodWait as e :
      time.sleep(e.value)
      return Get_Msg(bot,Chat_id,msg_id)
  except Exception as err : 
      pass


def File_Dl(File_Msg,dl_path):
  if File_Msg.audio or File_Msg.video or File_Msg.document  :
    if File_Msg.audio :
      file_name = File_Msg.audio.file_name
    elif File_Msg.video :
      file_name = File_Msg.video.file_name
    elif File_Msg.document :
      file_name = File_Msg.document.file_name
    if file_name == None :
      Name = File_Msg.id
      if File_Msg.audio : 
        Ex = 'mp3'
      elif File_Msg.video : 
        Ex = 'mp4'
    else :
      Splitted = file_name.split('.')
      Name = Splitted[0]
      Ex =  Splitted[1]
    custom_name = os.path.join(dl_path,f"{Name}_{random.randint(1,1000)}.{Ex}")
    File = File_Msg.download(file_name=custom_name)
  else :
    File = File_Msg.download(file_name=dl_path)
  return File 

def Upld_File(file,Msg,cap=' ',isogg=False):
  try:
    if file != None:
        RMsg = Msg.reply_video(file,caption=cap)
  except FloodWait as e:
    time.sleep(e.value)
    return Upld_File(file,Msg,cap)
  except Exception as err : 
        Err = f'حدث خطأ ما 😞 \n\n {err}'
        raise Exception(Err) 
  
#### Blur bot 

def get_seconds(clock_time) :
    splitted = clock_time.split(':')
    if len(splitted) == 3 : 
      hours, minutes, seconds = map(float, clock_time.split(':'))
    elif len(splitted) == 2 : 
      minutes = float(splitted[0])
      seconds = float(splitted[-1])
      hours = 0.0
    if '.' in str(seconds) :
       seconds += 0.03
    total_seconds = (hours * 3600) + (minutes * 60) + seconds
    return total_seconds

def Ranges_ref(Ranges,fps) :
    ranges = []
    if len(Ranges) != 0 :
      for Range in Ranges.split(' ') : 
        splitted = Range.split('-') 
        start = get_seconds(splitted[0])
        end  = get_seconds(splitted[1])
        ranges.append([ceil(start*fps),ceil((end)*fps)])
    return ranges

def isinrange(ret_num,Ranges):
        for x in Ranges :
         if ret_num in range(x[0],x[1]):
           return True
        return False
        

def Raw_Blur(file_path,Blur_File):
  Rate = int(Blur_File['BlurRate'])
  BlurMode = Blur_File['MainBlur'] 
  mainDir = '/'.join(file_path.split('/')[:-1]) + '/'
  P_Name = mainDir + file_path.split('/')[-1].split('.')[0]
  Ex = file_path.split('.')[-1]
  Res_File = f"{P_Name}_Blurred.{Ex}"
  Aud = Mp3_Conv(file_path)
  file_path = Media_Compress(file_path)
  cap = cv2.VideoCapture(file_path)
  if not cap.isOpened():
    raise ValueError("Error opening video file")
  fps = cap.get(cv2.CAP_PROP_FPS)

  FullFrame = Ranges_ref(Blur_File['FullFrame'],fps)
  RightHalf = Ranges_ref(Blur_File['RightHalf'],fps)
  LeftHalf = Ranges_ref(Blur_File['LeftHalf'],fps)
  UpperHalf = Ranges_ref(Blur_File['UpperHalf'],fps)
  LowerHalf = Ranges_ref(Blur_File['LowerHalf'],fps)
  RightThird = Ranges_ref(Blur_File['RightThird'],fps)
  LeftThird = Ranges_ref(Blur_File['LeftThird'],fps)
  UpperThird = Ranges_ref(Blur_File['UpperThird'],fps)
  LowerThird = Ranges_ref(Blur_File['LowerThird'],fps)
  RightThirdLeft = Ranges_ref(Blur_File['RightThirdLeft'],fps)
  LeftThirdLeft = Ranges_ref(Blur_File['LeftThirdLeft'],fps)
  UpperThirdLeft = Ranges_ref(Blur_File['UpperThirdLeft'],fps)
  LowerThirdLeft = Ranges_ref(Blur_File['LowerThirdLeft'],fps)

  totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
  durationInSeconds = totalNoFrames // fps
  Stream_Dur = int(durationInSeconds)
  width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
  height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
  fourcc = cv2.VideoWriter_fourcc(*'mp4v')
  out = cv2.VideoWriter(Res_File, fourcc, fps, (width, height))
  ret_num = 0

  while(True):
    ret, frame = cap.read()
    if ret:
        ret_num += 1

        if BlurMode == 'FullFrame' or isinrange(ret_num,FullFrame ) : 
          frame = cv2.blur(frame, (Rate, Rate))
        if BlurMode == 'RightHalf' or isinrange(ret_num,RightHalf ) : 
          midpoint = width // 2
          frame[0:height, midpoint:width] = cv2.blur(frame[0:height, midpoint:width], (Rate, Rate))
        if BlurMode == 'LeftHalf' or isinrange(ret_num,LeftHalf ) : 
          midpoint = width // 2
          frame[0:height, 0:midpoint] = cv2.blur(frame[0:height, 0:midpoint], (Rate, Rate))
        if BlurMode == 'UpperHalf' or isinrange(ret_num,UpperHalf ) : 
          midpoint = height // 2
          frame[0:midpoint, 0:width] = cv2.blur(frame[0:midpoint, 0:width], (Rate, Rate))
        if BlurMode == 'LowerHalf' or isinrange(ret_num,LowerHalf ) : 
          midpoint = height // 2
          frame[midpoint:height, 0:width] = cv2.blur(frame[midpoint:height, 0:width], (Rate, Rate))
        
        if BlurMode == 'RightThird' or isinrange(ret_num,RightThird ) : 
          midpoint = 2 * width // 3
          frame[0:height, midpoint:width]  = cv2.blur(frame[0:height, midpoint:width] , (Rate, Rate))
        if BlurMode == 'LeftThird' or isinrange(ret_num,LeftThird ) : 
          midpoint = width // 3
          frame[0:height, 0:midpoint] = cv2.blur(frame[0:height, 0:midpoint], (Rate, Rate))
        if BlurMode == 'UpperThird' or isinrange(ret_num,UpperThird ) : 
          midpoint = height // 3
          frame[0:midpoint, 0:width] = cv2.blur(frame[0:midpoint, 0:width], (Rate, Rate))
        if BlurMode == 'LowerThird' or isinrange(ret_num,LowerThird ) : 
          midpoint = 2 * height // 3
          frame[midpoint:height, 0:width] = cv2.blur(frame[midpoint:height, 0:width], (Rate, Rate))
        
        if BlurMode == 'RightThirdLeft' or isinrange(ret_num,RightThirdLeft ) : 
          midpoint = 2 * width // 3
          frame[0:height, 0:midpoint]  = cv2.blur(frame[0:height, 0:midpoint] , (Rate, Rate))
        if BlurMode == 'LeftThirdLeft' or isinrange(ret_num,LeftThirdLeft ) : 
          midpoint = width // 3
          frame[0:height, midpoint:width] = cv2.blur(frame[0:height, midpoint:width], (Rate, Rate))
        if BlurMode == 'UpperThirdLeft' or isinrange(ret_num,UpperThirdLeft ) : 
          midpoint = height // 3
          frame[midpoint:height, 0:width] = cv2.blur(frame[midpoint:height, 0:width], (Rate, Rate))
        if BlurMode == 'LowerThirdLeft' or isinrange(ret_num,LowerThirdLeft ) : 
          midpoint = 2 * height // 3
          frame[0:midpoint, 0:width] = cv2.blur(frame[0:midpoint, 0:width], (Rate, Rate))
      
        out.write(frame)
    else:
        break 

  cap.release()
  out.release()
  Res_File =  Vid_Mk(Res_File,Aud)
  Res_File =  Media_Compress(Res_File)
  return Res_File

#######

Photo_Blur_buttons = [['11','11'],['31','31'],['109 ','109 '],['185 ','185 '],['261 ','261 '],['491 ','491 ']]


@bot.on_message(filters.private & filters.incoming & ( filters.video))
def _telegram_file(client, message):
  User_Id = message.from_user.id
  key = f'{User_Id}_{message.id}'
  if key not in list(Blur_Dict.keys()) :
    Blur_Dict[key] = {'isfull':True,'BlurRate':'','MainBlur':'','RightHalf':'','LeftHalf':'','UpperHalf':'','LowerHalf':'','RightThird':'','LeftThird':'','UpperThird':'','LowerThird':'','RightThirdLeft':'','LeftThirdLeft':'','UpperThirdLeft':'','LowerThirdLeft':'','FullFrame':'','RightHalfK':False,"LeftHalfK":False,"UpperHalfK":False,"LowerHalfK":False,"RightThirdK":False,"LeftThirdK":False,"UpperThirdK":False,"LowerThirdK":False,"RightThirdLeftK":False,"LeftThirdLeftK":False,"UpperThirdLeftK":False,"LowerThirdLeftK":False,"FullFrameK":False,"BlurRateK":True}      
  Text = 'اختر درجة البلور'
  Buttons = []
  for op in Photo_Blur_buttons : 
    Buttons.append([KeyboardButton(op[0]), KeyboardButton(op[1])])
  replied = message.reply_text(text = Text,reply_markup = ReplyKeyboardMarkup(Buttons, resize_keyboard=True))  


@bot.on_message(filters.private & filters.incoming & filters.text)
def _telegram_file(client, message):
      User_Id = message.from_user.id
      Callback_Keys = list(Blur_Dict.keys())
      if any(str(User_Id) in key for key in Callback_Keys) :
        for Key in Callback_Keys :
         if str(User_Id) in Key :
            key = Key
        file_id = key.split('_')[-1]
        file_msg = Get_Msg(bot,User_Id,file_id)
    
      if Blur_Dict[key]['RightHalfK'] or Blur_Dict[key]['LeftHalfK'] or Blur_Dict[key]['UpperHalfK'] or Blur_Dict[key]['LowerHalfK'] or Blur_Dict[key]['RightThirdK'] or Blur_Dict[key]['LeftThirdK'] or Blur_Dict[key]['UpperThirdK'] or Blur_Dict[key]['LowerThirdK'] or Blur_Dict[key]['RightThirdLeftK'] or Blur_Dict[key]['LeftThirdLeftK'] or Blur_Dict[key]['UpperThirdLeftK'] or Blur_Dict[key]['LowerThirdLeftK'] or Blur_Dict[key]['FullFrameK'] or Blur_Dict[key]['BlurRateK'] :
        
        if Blur_Dict[key]['RightHalfK'] :
          Blur_Dict[key]['RightHalf'] = message.text
          Blur_Dict[key]['RightHalfK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LeftHalfK'] :
          Blur_Dict[key]['LeftHalf'] = message.text
          Blur_Dict[key]['LeftHalfK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['UpperHalfK'] :
          Blur_Dict[key]['UpperHalf'] = message.text
          Blur_Dict[key]['UpperHalfK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LowerHalfK'] :
          Blur_Dict[key]['LowerHalf'] = message.text
          Blur_Dict[key]['LowerHalfK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['RightThirdK'] :
          Blur_Dict[key]['RightThird'] = message.text
          Blur_Dict[key]['RightThirdK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LeftThirdK'] :
          Blur_Dict[key]['LeftThird'] = message.text
          Blur_Dict[key]['LeftThirdK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['UpperThirdK']:
          Blur_Dict[key]['UpperThird'] = message.text
          Blur_Dict[key]['UpperThirdK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LowerThirdK'] :
          Blur_Dict[key]['LowerThird'] = message.text
          Blur_Dict[key]['LowerThirdK'] = False
          message.reply('تم التلقيم')
        
        elif Blur_Dict[key]['RightThirdLeftK'] :
          Blur_Dict[key]['RightThirdLeft'] = message.text
          Blur_Dict[key]['RightThirdLeftK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LeftThirdLeftK'] :
          Blur_Dict[key]['LeftThirdLeft'] = message.text
          Blur_Dict[key]['LeftThirdLeftK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['UpperThirdLeftK']:
          Blur_Dict[key]['UpperThirdLeft'] = message.text
          Blur_Dict[key]['UpperThirdLeftK'] = False
          message.reply('تم التلقيم')
        elif Blur_Dict[key]['LowerThirdLeftK'] :
          Blur_Dict[key]['LowerThirdLeft'] = message.text
          Blur_Dict[key]['LowerThirdLeftK'] = False
          message.reply('تم التلقيم')
        
        elif Blur_Dict[key]['FullFrameK'] :
          Blur_Dict[key]['FullFrame'] = message.text
          Blur_Dict[key]['FullFrameK'] = False
          message.reply('تم التلقيم')

        elif Blur_Dict[key]['BlurRateK'] :
          Blur_Dict[key]['BlurRate'] = message.text
          Blur_Dict[key]['BlurRateK'] = False
          Text = 'اختر نمط البلور'
          Buttons = [
                      [KeyboardButton("Ranges"), KeyboardButton("Full Vid")]
                  ]
          message.reply(text = Text,reply_markup = ReplyKeyboardMarkup(Buttons, resize_keyboard=True))
            
          
      elif message.text in ['Full Vid','Ranges'] :
        if message.text == 'Full Vid' :
          Text = 'اختر نمط البلور'
        elif message.text == 'Ranges' :
          Blur_Dict[key]['isfull'] = False
          Text = 'اختر المدى مع ما يناسب '
        Buttons = [
          [KeyboardButton("FullFrame")],
          [KeyboardButton("RightHalf"), KeyboardButton("LeftHalf")],
          [KeyboardButton("UpperHalf"), KeyboardButton("LowerHalf")],
          [KeyboardButton("RightThird"), KeyboardButton("LeftThird")],
          [KeyboardButton("UpperThird"), KeyboardButton("LowerThird")],
          [KeyboardButton("RightThirdLeft"), KeyboardButton("LeftThirdLeft")],
          [KeyboardButton("UpperThirdLeft"), KeyboardButton("LowerThirdLeft")]
          ]
        if message.text == 'Ranges' :
          Buttons += [[KeyboardButton("✔️")]]
        message.reply(text = Text,reply_markup = ReplyKeyboardMarkup(Buttons,resize_keyboard=True))
        
      
      elif message.text in ['RightHalf','LeftHalf','UpperHalf','LowerHalf','RightThird','LeftThird','UpperThird','LowerThird','RightThirdLeft','LeftThirdLeft','UpperThirdLeft','LowerThirdLeft','FullFrame'] :
        if Blur_Dict[key]['isfull'] :
          Blur_Dict[key]['MainBlur'] = message.text
          Blur_File = Blur_Dict[key]
          dl_path = f'./downloads_{file_id}_{Bot_Identifier}/'
          replied = message.reply('جار العمل')
          File = File_Dl(file_msg,dl_path)
          Res_File = Raw_Blur(File,Blur_File)
          Upld_File(Res_File,message)
          Check_Dir(dl_path)
          Blur_Dict.pop(key)
          replied.edit_text('تم البلور')
        else : 
          Text = f'''الآن أرسل نطاقات الـ {message.text} بهذه الصورة
            hh:mm:ss-hh:mm:ss
            ويمكنك إرسال أكثر من مدى بهذه الصورة بترك مسافة بين كل مدى
            hh:mm:ss-hh:mm:ss hh:mm:ss-hh:mm:ss hh:mm:ss-hh:mm:ss
            '''
          Blur_Dict[key][message.text+'K'] = True
          message.reply(Text)
      
      elif message.text == '✔️' :
          
        Blur_File = Blur_Dict[key]
        dl_path = f'./downloads_{file_id}_{Bot_Identifier}/'
        replied = message.reply('جار العمل')
        File = File_Dl(file_msg,dl_path)
        Res_File = Raw_Blur(File,Blur_File)
        Upld_File(Res_File,message)
        Check_Dir(dl_path)
        Blur_Dict.pop(key)
        replied.edit_text('تم البلور')



def main():
    try:
        bot.start()
        print("✅ Blur Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()