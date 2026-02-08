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
seg_per_sec = 1200
Loop_Status = False
Token = str(Bot_Token)
Token_Identifier = Token.split(':')[0]
Music_Rmv_Path = f'./Music_Rmv_{Token_Identifier}/'
Session_file = Token_Identifier +'_session_bot'

################

async def Create_Dir(Dir):
  if not os.path.isdir(Dir):
    os.makedirs(Dir, exist_ok=True)

async def Check_Dir(Dir):
  if os.path.isdir(Dir):
      shutil.rmtree(Dir)
  await Create_Dir(Dir)

async def Check_File(File):
  if os.path.isfile(File):
      os.remove(File)

async def Sub_Aud(Vid,Aud):
  mainDir = '/'.join(Vid.split('/')[:-1]) + '/'
  Sub_Vid = mainDir +  Vid.split('/')[-1].split('.')[0] + '_Subed.mp4'
  SubAud_Cmd = f'ffmpeg -i "{Vid}" -i "{Aud}" -c:v copy -map 0:v:0 -map 1:a:0 "{Sub_Vid}"'
  os.system(SubAud_Cmd)
  return Sub_Vid

async def Aud_Merge(Txt_File):
    mainDir = '/'.join(Txt_File.split('/')[:-1]) + '/'
    Mp3_File = mainDir + Txt_File.split('/')[-1].split('.')[0] + '_Merged.mp3'
    Aud_Merge_Cmd = f'ffmpeg -f concat -safe 0 -i "{Txt_File}" "{Mp3_File}" -y'
    os.system(Aud_Merge_Cmd)
    os.remove(Txt_File)
    return Mp3_File

async def Encode_Vid(File):
    mainDir = '/'.join(File.split('/')[:-1]) + '/'
    Mp4_File = mainDir + File.split('/')[-1].split('.')[0] + '_encoded.mp4'
    Vid_Encode = f'ffmpeg -i "{File}" -c:a aac -codec:v h264 -b:v 1000k "{Mp4_File}" -y'
    os.system(Vid_Encode)
    return Mp4_File

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
  
async def Upld_File(file,Msg):
  try:
    if file != None:
      if file.lower().endswith(Audio_Forms):
          RMsg = await Msg.reply_audio(file)
      elif file.lower().endswith(Video_Forms):
        Dur = await Get_Stream_Dur(file)
        Thumb = await Thumbnail_Get(file)
        RMsg = await Msg.reply_video(file,caption=os.path.basename(file),duration=Dur,thumb=Thumb)
      elif file.lower().endswith(Image_forms):
          RMsg = await Msg.reply_photo(file)
      else :
          RMsg = await Msg.reply_document(file)
      return RMsg.id
  except FloodWait as e:
    time.sleep(e.value)
    return await Upld_File(file,Msg)
  except Exception as err :
        Err = f'حدث خطأ ما 😞 \n\n {err}'
        raise Exception(Err)


async def Get_File(Dl_Dir,File_Ex):
  for file in os.listdir(Dl_Dir):
    if file.lower().endswith(File_Ex):
      return os.path.abspath(Dl_Dir + file)
  return None

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

async def Vid_Mk(Vid,Aud):
  mainDir = '/'.join(Vid.split('/')[:-1]) + '/'
  Vid_Res = mainDir + Vid.split('/')[-1].split('.')[0] + '_Merged.mp4'
  Sub_Cmd = f'ffmpeg -i "{Vid}" -i "{Aud}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{Vid_Res}" -y'
  os.system(Sub_Cmd)
  return Vid_Res

async def Mp3_Conv(File):
  mainDir = '/'.join(File.split('/')[:-1]) + '/'
  Mp3_File = mainDir +  File.split('/')[-1].split('.')[0] + '_Conv.mp3'
  Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
  os.system(Mp3_Cmd)
  return Mp3_File

async def Aud_Scatter(File,Seg_Per_Sec):
    mainDir = '/'.join(File.split('/')[:-1]) + '/'
    Parts_Dir = mainDir + File.split('/')[-1].split('.')[0] + '_Parts/'
    await Check_Dir(Parts_Dir)
    File = await Mp3_Conv(File)
    Scatter_Cmd = f'ffmpeg -i "{File}" -f segment -segment_time {Seg_Per_Sec} -c copy "{Parts_Dir}rmvd%09d.wav" -y'
    os.system(Scatter_Cmd)
    os.remove(File)
    return Parts_Dir

#### Token #####

bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Token)

######## Music Funcs

async def random_name():
    current_time = datetime.datetime.now()
    timestamp = current_time.strftime("%Y%m%d%H%M%S%f")
    file_name = f"file_{timestamp}"
    return file_name

async def demucs_func(file_path):
  file_path = await Mp3_Conv(file_path)
  File_Dir = '/'.join(file_path.split('/')[:-1]) + '/'
  
  #### rename ####
  New_Name = await random_name()
  New_File = f'{File_Dir}{New_Name}.mp3'
  os.rename(file_path,New_File)
  file_path = New_File
  ########
  demucs_model = 'mdx_extra'
  demucs_Cmd = f"demucs -n '{demucs_model}' '{file_path}'"
  os.system(demucs_Cmd)
  demucs_Dir = f'/content/separated/{demucs_model}'
  vocal_path = f'{demucs_Dir}/{New_Name}/vocals.wav'
  vocal_path = await Mp3_Conv(vocal_path)
  return vocal_path

##############

async def Music_Rmv(rmvmessage,rmvpath,streamdur):
  streamdur = int(streamdur)
  if streamdur == 0 :
    streamdur = await Get_Stream_Dur(rmvpath)
  mainDir = '/'.join(rmvpath.split('/')[:-1]) + '/'
  copymp4 = mainDir +  rmvpath.split('/')[-1].split('.')[0] + '_Copy.mp4'
  cp_Cmd = f'cp "{rmvpath}" "{copymp4}"'
  os.system(cp_Cmd)
  if streamdur <= seg_per_sec :
    vocal_path = await demucs_func(rmvpath)
  else :
    musicrmvlist =  mainDir + rmvpath.split('/')[-1].split('.')[0] + '_Mlist.txt'
    Parts_Dir = await Aud_Scatter(rmvpath,seg_per_sec)
    with open(musicrmvlist,'a') as f :
      for x in range(0,len(os.listdir(Parts_Dir))):
        seg_path=f"{Parts_Dir}rmvd{str(x).zfill(9)}.wav"
        vocal_path = await demucs_func(seg_path)
        f.write(f'file {vocal_path} \n')

    vocal_path = await Aud_Merge(musicrmvlist)
  if rmvpath.lower().endswith(Video_Forms):
    vocal_path = await Vid_Mk(copymp4,vocal_path)
  await Upld_File(vocal_path,rmvmessage)

######## Bot Cmds ####

@bot.on_message(filters.command('start') & filters.private)
async def command1(bot,message):
   await message.reply('لبقية البوتات \n\n @sunnaybots')


@bot.on_message(filters.private & filters.incoming & (filters.audio | filters.video | filters.voice))
async def _telegram_file(client, message):
      replied = await message.reply(f"جاري إزالة الموسيقا ☕️ ")
      Vid_File = await message.download(file_name=Music_Rmv_Path)
      if ' ' in Vid_File:
        os.rename(Vid_File,Vid_File.replace(' ','_'))
        Vid_File = Vid_File.replace(' ','_')
      await Music_Rmv(message,Vid_File,await Msg_Dur(message))
      await replied.edit_text('تمت الإزالة')


def main():
    if not os.path.exists(Music_Rmv_Path): os.makedirs(Music_Rmv_Path)
    try:
        bot.start()
        print("✅ Music Removal Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()
