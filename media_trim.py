import nest_asyncio
import os
nest_asyncio.apply()
#########################################################

Bot_Token = os.getenv('TOKEN')

########################################################

from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , ReplyKeyboardMarkup , CallbackQuery , ForceReply,Message
from pyrogram import Client, filters,enums,StopTransmission,idle
from pyrogram.errors import FloodWait

from pathlib import Path
from PIL import Image
import shutil,datetime,time,audioread,cv2

######### Constants

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
Audio_Forms = (".mp3",".ogg",".m4a",".aac",".flac",".wav",".wma",".opus",".3gpp")
Video_Forms = (".mp4",".mkv",".mov",".avi",".wmv",".avchd",".webm",".flv")
Image_forms = (".jpg",".png",'.tif','webp')

Token = str(Bot_Token)
Token_Identifier = Token.split(':')[0]
Trim_Path = f'./mediatrim_{Token_Identifier}/'
Session_file = Token_Identifier +'_session_bot'
Media_Trim_Msg = "الآن أرسل نقطة البداية والنهاية بهذه الصورة \n\n hh:mm:ss-hh:mm:ss"

################

async def is_int(val):
    try:
        int(val)
        return True
    except Exception as err :
      return False
    
async def Get_Msg(bot,Chat_id,msg_id):
  try : 
     msg = await bot.get_messages(int(Chat_id) if await is_int(Chat_id) else str(Chat_id).replace('=','_'),int(msg_id))
     return msg
  except FloodWait as e :
      time.sleep(e.value)
      return await Get_Msg(bot,Chat_id,msg_id)
  except Exception as err : 
      pass
  
async def Mp3_Conv(File):
  mainDir = '/'.join(File.split('/')[:-1]) + '/'
  Mp3_File = mainDir +  File.split('/')[-1].split('.')[0] + '_Conv.mp3'
  Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
  os.system(Mp3_Cmd)
  return Mp3_File

async def Encode_Vid(File):
    mainDir = '/'.join(File.split('/')[:-1]) + '/'
    Mp4_File = mainDir + File.split('/')[-1].split('.')[0] + '_encoded.mp4'
    Vid_Encode = f'ffmpeg -i "{File}" -c:a aac -codec:v h264 -b:v 1000k "{Mp4_File}" -y'
    os.system(Vid_Encode)
    return Mp4_File

async def Msg_Dur(Msg):
  if Msg.audio :
    dur = Msg.audio.duration
  elif Msg.video :
    dur = Msg.video.duration
  elif Msg.voice :
    dur = Msg.voice.duration
  else :
    dur = 0
  return int(dur)

async def Dur_Get(Msg,File):
  Dur = await Msg_Dur(Msg)
  if Dur == 0 :
    Dur = await Get_Stream_Dur(File)
  return Dur

async def Get_Stream_Dur(File):
  if os.path.basename(File).endswith(Video_Forms):
    File = await Mp3_Conv(File)
  Stream_Dur = int(audioread.audio_open(File).duration)
  return Stream_Dur

async def Cv2_PicCap(Media_Path):
  mainDir = '/'.join(Media_Path.split('/')[:-1]) + '/'
  Thumb_Nail = mainDir + Media_Path.split('/')[-1].split('.')[0] + '_Thumb.jpg'
  try:
     cam = cv2.VideoCapture(Media_Path)
     ret, frame = cam.read()
     cv2.imwrite(Thumb_Nail, frame)
     cam.release()
     return Thumb_Nail
  except :
    Media_Path = await Encode_Vid(Media_Path)
    return await Cv2_PicCap(Media_Path) 
    
async def Thumbnail_Get(Media_Path):
    if Media_Path.lower().endswith(Video_Forms) :
       Thumb_Nail = await Cv2_PicCap(Media_Path)
    else : 
     Thumb_Nail = 'Sunnay_Logo.jpg'
     if not os.path.isfile(Thumb_Nail):
      Thumb_Link = 'https://img1.teletype.in/files/81/52/81521984-f683-4a99-88ff-0c5c8896fd8b.jpeg'
      os.system(f"wget -O '{Thumb_Nail}' '{Thumb_Link}' ")
      Thumb_Nail = '/content/' + Thumb_Nail
    return Thumb_Nail

async def Upld_File(file,Msg,cap):
  try:
    if file != None:
      if file.lower().endswith(Audio_Forms):
          RMsg = await Msg.reply_audio(file,caption=cap)
      elif file.lower().endswith(Video_Forms):
        Dur = await Get_Stream_Dur(file)
        Thumb = await Thumbnail_Get(file)
        RMsg = await Msg.reply_video(file,caption=cap,duration=Dur,thumb=Thumb)
      elif file.lower().endswith(Image_forms):
          RMsg = await Msg.reply_photo(file)
      else :
          RMsg = await Msg.reply_document(file,caption=cap)
      return RMsg.id
  except FloodWait as e:
    time.sleep(e.value)
    return await Upld_File(file,Msg,cap)
  except Exception as err :
        Err = f'حدث خطأ ما 😞 \n\n {err}'
        raise Exception(Err)
  
async def Media_Trim(file_path,Rate):
  point_list = Rate.split('-') 
  strt_point = point_list[0]
  end_point = point_list[1]
  mainDir = '/'.join(file_path.split('/')[:-1]) + '/'
  Res_Name = mainDir +  file_path.split('/')[-1].split('.')[0] + '_Trim.mp3'
  Type = True if file_path.lower().endswith(Audio_Forms) else False
  if Type :
    Res_File = Res_Name + '_Trim.mp3'
    Trim_Cmd = f'ffmpeg -i "{file_path}" -ss {strt_point} -to {end_point} "{Res_File}" -y'
  else :
    Res_File = Res_Name + '_Trim.mp4'
    Trim_Cmd = f'ffmpeg -i "{file_path}" -ss {strt_point} -strict -2 -to {end_point} -c:a aac -codec:v h264 -b:v 1000k "{Res_File}" -y '
  os.system(Trim_Cmd)
  return Res_File if Type else Encode_Vid(Res_File)

#### Token #####

bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Token)

######## Bot Cmds ####

@bot.on_message(filters.command('start') & filters.private)
async def command1(bot,message):
   await message.reply('لبقية البوتات \n\n @sunnaybots')


@bot.on_message(filters.private & filters.incoming & (filters.audio | filters.video | filters.voice))
async def _telegram_file(client, message):
      
    await message.reply_text(Media_Trim_Msg,reply_markup=ForceReply(True),reply_to_message_id=message.id)

@bot.on_message(filters.private & filters.reply)
async def refunc(client,message):
   if (message.reply_to_message.reply_markup) and isinstance(message.reply_to_message.reply_markup, ForceReply)  :
    User_Id = message.from_user.id
    Msg_Text = message.text
    reply_id = message.reply_to_message_id
    reply_msg = await Get_Msg(bot,User_Id,reply_id)
    file_id = reply_msg.reply_to_message_id
    file_msg = await Get_Msg(bot,User_Id,file_id)
    await message.delete()

    replied = await file_msg.reply(f"جاري القص  ☕️ ")
    Media_File = await file_msg.download(file_name=Trim_Path)
    if ' ' in Media_File:
        os.rename(Media_File,Media_File.replace(' ','_'))
        Media_File = Media_File.replace(' ','_')
    
    P_List = Msg_Text.strip().split(' ')
    if len(P_List) != 0 :
        for per in P_List : 
            start = per.split('-')[0]
            End = per.split('-')[1]
            cap =  ( f"`{start}` to `{End}`")
            file = Media_Trim(Media_File,per)
            await Upld_File(file,file_msg,cap)
    await replied.edit_text('تم القص ')




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

