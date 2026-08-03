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
import internetarchive as ia

Archive_Dict = {}

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
      Ex =  Splitted[-1]
    custom_name = os.path.join(dl_path,f"{Name}_{random.randint(1,1000)}.{Ex}")
    File = File_Msg.download(file_name=custom_name)
  else :
    File = File_Msg.download(file_name=dl_path)
  return File 


def upld2arch(upldarchpath,bucketname):
  ia.upload(
    itemname=bucketname,
    files=upldarchpath,
    verbose=True,
    retries=3
)
  file_name = os.path.basename(upldarchpath)
  Arch_Url = f"https://archive.org/download/{bucketname}/{file_name}"
  return Arch_Url


 
@bot.on_message(filters.private & filters.incoming)
def _telegram_file(client, message):
  User_Id = message.from_user.id
  dl_path = f'./downloads_{User_Id}_{Bot_Identifier}/'
  if User_Id not in list(Archive_Dict.keys()) : 
     Archive_Dict[User_Id] = {"Files" : [],'Bucket':'','access_key_id':'','secret_access_key':'','BucketK':False,'access_key_idK':False,'secret_access_keyK':False,'Done':False}
  if ( Archive_Dict[User_Id]['BucketK'] == Archive_Dict[User_Id]['access_key_idK'] ) and ( Archive_Dict[User_Id]['access_key_idK'] == Archive_Dict[User_Id]['secret_access_keyK'] ) and not Archive_Dict[User_Id]['Done']   :
    if len(Archive_Dict[User_Id]['Bucket']) == 0 :
        message.reply('أدخل اسم النطاق')
        Archive_Dict[User_Id]['BucketK'] = True

    elif len(Archive_Dict[User_Id]['access_key_id']) == 0 :
        message.reply('أدخل الـ access_key_id')
        Archive_Dict[User_Id]['access_key_idK'] = True

    elif len(Archive_Dict[User_Id]['secret_access_key']) == 0 :
        message.reply('أدخل الـ secret_access_key ')
        Archive_Dict[User_Id]['secret_access_keyK'] = True

  
  elif message.text : 
    if Archive_Dict[User_Id]['BucketK'] or Archive_Dict[User_Id]['access_key_idK'] or Archive_Dict[User_Id]['secret_access_keyK'] : 
        if Archive_Dict[User_Id]['BucketK'] : 
            Archive_Dict[User_Id]['Bucket'] = message.text
            Archive_Dict[User_Id]['BucketK'] = False
            message.reply("تم التلقيم \n\n الآن أدخل الـ access_key_id ")
            Archive_Dict[User_Id]['access_key_idK'] = True

        elif Archive_Dict[User_Id]['access_key_idK'] : 
            Archive_Dict[User_Id]['access_key_id'] = message.text
            Archive_Dict[User_Id]['access_key_idK'] = False
            message.reply("تم التلقيم \n\n الآن أدخل الـ secret_access_key ")
            Archive_Dict[User_Id]['secret_access_keyK'] = True
            

        elif Archive_Dict[User_Id]['secret_access_keyK'] : 
            Archive_Dict[User_Id]['secret_access_key'] = message.text
            Archive_Dict[User_Id]['secret_access_keyK'] = False
            Rclone_Text = f'''[myarchive]
type = internetarchive
access_key_id = {Archive_Dict[User_Id]['access_key_id']}
secret_access_key = {Archive_Dict[User_Id]['secret_access_key']}'''
            Create_Dir('/root/.config/rclone/')
            open('/root/.config/rclone/rclone.conf','w').write(Rclone_Text)
            Archive_Dict[User_Id]['Done'] = True
            Text = 'أهلا بك هذا بوت الرفع لأرشيف'
            Buttons = [[KeyboardButton("Upload"), KeyboardButton("Empty Quee")]]
            replied = message.reply_text(text = Text,reply_markup = ReplyKeyboardMarkup(Buttons, resize_keyboard=True))  
    else : 
      if len(Archive_Dict[User_Id]['Bucket']) != 0 and len(Archive_Dict[User_Id]['access_key_id']) != 0  and len(Archive_Dict[User_Id]['secret_access_key']) != 0 :
        # if message.text == '/start' : 
        #     Text = 'أهلا بك هذا بوت الرفع لأرشيف'
        #     Buttons = [[KeyboardButton("Upload"), KeyboardButton("Empty Quee")]]
        #     replied = message.reply_text(text = Text,reply_markup = ReplyKeyboardMarkup(Buttons, resize_keyboard=True))  

        if message.text == 'Empty Quee' : 
            Archive_Dict[User_Id]['Files'].clear()
            message.reply('تم الإفراغ')

        elif message.text == 'Upload' : 
            Msgs = Archive_Dict[User_Id]['Files']
            for msg in Msgs : 
                File = File_Dl(msg,dl_path)
                Link = upld2arch(File,Archive_Dict[User_Id]['Bucket'])
                Check_Dir(dl_path)
                msg.reply(text = Link ,reply_to_message_id = msg.id)

  elif message.video or message.audio or message.photo or message.voice or message.video_note :
    if len(Archive_Dict[User_Id]['Bucket']) != 0 and len(Archive_Dict[User_Id]['access_key_id']) != 0  and len(Archive_Dict[User_Id]['secret_access_key']) != 0 :
       Archive_Dict[User_Id]['Files'].append(message)
       message.reply(f'عدد الملفات {len(Archive_Dict[User_Id]['Files'])} ملفاً')
      

def main():
    try:
        bot.start()
        print("✅ Archive Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()