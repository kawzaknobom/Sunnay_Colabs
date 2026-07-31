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
import shutil,os,time,random

Montaj_Dict = {}

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


def Get_Msg(Chat_id,msg_id):
  try : 
     msg = bot.get_messages(int(Chat_id),int(msg_id))
     return msg
  except FloodWait as e :
      time.sleep(e.value)
      return Get_Msg(bot,Chat_id,msg_id)
  except Exception as err : 
      pass


def Mp3_Conv(File):
  mainDir = '/'.join(File.split('/')[:-1]) + '/'
  Mp3_File = mainDir +  File.split('/')[-1].split('.')[0] + '_Conv.mp3'
  Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
  os.system(Mp3_Cmd)
  return Mp3_File


def Vid_Mon(img_path,aud_path):
      Img_ex = '.' + img_path.split('.')[-1]
      vid_path = img_path.replace(Img_ex,'_Montaj.mp4')
      Montaj_Cmd = f'ffmpeg -r 1 -loop 1 -y -i "{img_path}" -i "{aud_path}" -c:v libx264 -tune stillimage -c:a copy -shortest -vf scale=1920:1080 "{vid_path}"'
      os.system(Montaj_Cmd)
      return vid_path

def Upld_File(file,Msg,cap=' ',isogg=False):
  try:
    if file != None:
        RMsg = Msg.reply_video(file,caption=cap,reply_to_message_id = Msg.id)
  except FloodWait as e:
    time.sleep(e.value)
    return Upld_File(file,Msg,cap)
  except Exception as err : 
        Err = f'حدث خطأ ما 😞 \n\n {err}'
        raise Exception(Err) 

  
@bot.on_message(filters.private & filters.incoming)
def _telegram_file(client, message):
  User_Id = message.from_user.id
  dl_path = f'./downloads_{User_Id}_{Bot_Identifier}/'
  if User_Id not in list(Montaj_Dict.keys()) : 
     Montaj_Dict[User_Id] = {"Files" : [],'Image_Id':'','Audio_Id':''}
  
  if message.text :
        if message.text == '/start' : 
            Text = 'أهلا بك هذا بوت المنتجة'
            Buttons = [[KeyboardButton("Generate"), KeyboardButton("Empty Quee")]]
            replied = message.reply_text(text = Text,reply_markup = ReplyKeyboardMarkup(Buttons, resize_keyboard=True))  

        elif message.text == 'Empty Quee' : 
            Montaj_Dict[User_Id]['Files'].clear()
            message.reply('تم الإفراغ')

        elif message.text == 'Generate' : 
            replied = message.reply('جار العمل ')
            Media_Ids = Montaj_Dict[User_Id]['Files']
            for pair in Media_Ids :
                image_id = pair[0]
                audio_id =  pair[1]
                image_msg = Get_Msg(User_Id,image_id)
                audio_msg = Get_Msg(User_Id,audio_id)
                image = File_Dl(image_msg,dl_path)
                audio = File_Dl(audio_msg,dl_path)
                Mp3_Path = Mp3_Conv(audio)
                Res_File = Vid_Mon(image,Mp3_Path)
                Upld_File(Res_File,image_msg)
                Check_Dir(dl_path)
            replied.edit_text('تم')

  elif message.photo : 
     if len(Montaj_Dict[User_Id]['Audio_Id']) !=0 : 
        Montaj_Dict[User_Id]['Files'].append([message.id,Montaj_Dict[User_Id]['Audio_Id']])
        Montaj_Dict[User_Id]['Audio_Id'] = ''
        message.reply(f'عدد التلقيمات {len(Montaj_Dict[User_Id]['Files'])} تلقيماً')
     else : 
        Montaj_Dict[User_Id]['Image_Id'] = str(message.id)
        message.reply('الآن أرسل الصوتية')

  elif message.audio  or message.voice :
    if len(Montaj_Dict[User_Id]['Image_Id']) !=0 : 
            Montaj_Dict[User_Id]['Files'].append([Montaj_Dict[User_Id]['Image_Id'],message.id])
            Montaj_Dict[User_Id]['Image_Id'] = ''
            message.reply(f'عدد التلقيمات {len(Montaj_Dict[User_Id]['Files'])} تلقيماً')
    else : 
            Montaj_Dict[User_Id]['Audio_Id'] = str(message.id)
            message.reply('الآن أرسل الصورة')
      

def main():
    try:
        bot.start()
        print("✅ Montaj Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()