import nest_asyncio
import os
nest_asyncio.apply()

#########################################################

Bot_Token = os.environ['Bot_Token']
Api_Id = os.environ['Api_Id']
Api_Hash = os.environ['Api_Hash']

########################################################

from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , ReplyKeyboardMarkup , CallbackQuery , ForceReply,Message
from pyrogram import Client, filters,enums,StopTransmission,idle
from pyrogram.errors import FloodWait

from PIL import Image
import shutil,cv2,time,random

######### Constants

Token_Identifier = Bot_Token.split(':')[0]
Trim_Path = f'./mediaencode_{Token_Identifier}/'
Session_file = Token_Identifier +'_session_bot'
bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Bot_Token)

################

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
      Ex =  Splitted[-1]
    custom_name = os.path.join(dl_path,f"{Name}_{random.randint(1,1000)}.{Ex}")
    File = File_Msg.download(file_name=custom_name)
  else :
    File = File_Msg.download(file_name=dl_path)
  return File 

def Encode_Vid(File):
    Ext = '.' + File.split('.')[-1]
    Mp4_File = File.replace(Ext,'_Encoded.mp4')
    Vid_Encode = f'ffmpeg -i "{File}" -c:a aac -codec:v h264 -b:v 1000k "{Mp4_File}" -y'
    os.system(Vid_Encode)
    return Mp4_File


def get_name(message):
    file_name = getattr(getattr(message, message.media.value, None), "file_name", None) if message.media else None
    if file_name == None :
      file_name = 'None'
    if message.voice :
      file_name = message.voice.file_unique_id + '.ogg'
    elif message.video_note : 
      file_name = message.video_note.file_unique_id + '.mp4'
    return file_name


def generate_thumbnail(video_path):
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video file: {video_path}")

    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps > 0 and total_frames > 0:
        total_duration_sec = total_frames / fps
        middle_sec = total_duration_sec / 2.0
    else:
        middle_sec = 0.0  

    cap.set(cv2.CAP_PROP_POS_MSEC, middle_sec * 1000)

    success, frame = cap.read()
    cap.release()

    if not success or frame is None:
        raise RuntimeError("Failed to extract frame from video.")

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)
    pil_image.thumbnail((320, 180))

    Ext = '.' + video_path.split('.')[-1]
    output_path = video_path.replace(Ext,'.jpeg"')
    pil_image.save(output_path,format="JPEG", quality=85,optimize=True)
    return output_path

def Upld_File(file,Msg,cap=' ',isRenm=False):
  try:
    if file != None:
        if cap == " " : 
            cap = "@Multi_Usage_Sunnay_Bot"
        else : 
            cap += ("\n\n" + "@Multi_Usage_Sunnay_Bot")
        Name = get_name(Msg)
        if Name == 'None' or isRenm : 
            Name = file.split("/")[-1]
        Name = Name.split('.')[0].replace('_',' ')
        cap = Name + "\n\n" + cap
        Thumb = generate_thumbnail(file)
        RMsg = Msg.reply_video(file,caption="🎥 "+cap,thumb=Thumb,reply_to_message_id = Msg.id)
        return RMsg.id
  except FloodWait as e:
    time.sleep(e.value)
    return Upld_File(file,Msg,cap)
  except Exception as err : 
        pass

   
def Create_Dir(Dir):
  if not os.path.isdir(Dir):
    Mkdir_Cmd = f'mkdir -p "{Dir}"'
    os.system(Mkdir_Cmd)
      
def Check_Dir(Dir):
  if os.path.isdir(Dir):
      shutil.rmtree(Dir)
  Create_Dir(Dir)

######## Bot Cmds ####

@bot.on_message(filters.command('start') & filters.private)
def command1(bot,message):
  message.reply('لبقية البوتات \n\n @sunnaybots',reply_to_message_id = message.id)


@bot.on_message(filters.private & filters.incoming & filters.video)
def _telegram_file(client, message):
    message.reply('جار الضغط',reply_to_message_id = message.id)
    File = File_Dl(message,Trim_Path)
    Res = Encode_Vid(File)
    message.reply_video(Res,reply_to_message_id = message.id)
    Check_Dir(Trim_Path)

def main():
    if not os.path.exists(Trim_Path): os.makedirs(Trim_Path)
    try:
        bot.start()
        print("✅ Media Trim Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()