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

import os,shutil,time

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'

Audio_Forms = ("mp3","ogg","m4a","aac","flac","wav","wma","opus","3gpp")


async def Create_Dir(Dir):
  if not os.path.isdir(Dir):
    os.makedirs(Dir, exist_ok=True)

async def Check_Dir(Dir):
  if os.path.isdir(Dir):
      shutil.rmtree(Dir)
  await Create_Dir(Dir)

def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  Session_file = Bot_Identifier+'_session_prm_bot'
  bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Bot_Token)
  return bot,Bot_Identifier


bot,Bot_Identifier = Pyrogram_Client(Bot_Token)
Dl_Dir = f'./Renm_{Bot_Identifier}/'


Audio_Dict = {}

async def Mp3_Conv(File):
  Mp3_File = File.replace('.' + File.split('.')[-1],'_Conv.mp3')
  Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
  os.system(Mp3_Cmd)
  return Mp3_File

async def Get_Msg(bot,Chat_id,msg_id):
  try : 
     msg = await bot.get_messages(int(Chat_id),int(msg_id))
     return msg
  except FloodWait as e :
      time.sleep(e.value)
      return await Get_Msg(bot,Chat_id,msg_id)
  except Exception as err : 
      pass

async def Upld_File(file,Msg,cap=' ',isogg=False):
  try:
    if file != None:
      if file.lower().endswith(Audio_Forms):
            RMsg = await Msg.reply_audio(file,caption=cap)
      return RMsg.id
  except FloodWait as e:
    time.sleep(e.value)
    return await Upld_File(file,Msg,cap)
  except Exception as err : 
        Err = f'حدث خطأ ما 😞 \n\n {err}'
        raise Exception(Err) 
  
async def Renm(AudioList,StartP,message):
   for x,msg in enumerate(AudioList,StartP) :
        Extention = msg.audio.file_name.lower().split('.')[-1]
        dlfile = os.path.join(Dl_Dir,f"{str(x).zfill(4)}.{Extention}")
        File = await msg.download(file_name=dlfile)
        if Extention != 'mp3': 
          Res_File = await Mp3_Conv(File)
          os.remove(File)
          Mp3_File = File.replace(Extention,'mp3')
          os.rename(Res_File,Mp3_File)
          File = Mp3_File
        res = await Upld_File(File,message)
        await Check_Dir(Dl_Dir)


async def Renmid(AudioRange,StartP,Chat_id):
   for x,msgid in enumerate(range(AudioRange[0],AudioRange[1]),StartP) :
        msg = await Get_Msg(bot,Chat_id,msgid)
        print(msg.audio.file_name)
        Extention = msg.audio.file_name.lower().split('.')[-1]
        dlfile = os.path.join(Dl_Dir,f"{str(x).zfill(4)}.{Extention}")
        File = await msg.download(file_name=dlfile)
        if Extention != 'mp3': 
          Res_File = await Mp3_Conv(File)
          os.remove(File)
          Mp3_File = File.replace(Extention,'mp3')
          os.rename(Res_File,Mp3_File)
          File = Mp3_File
        res = await Upld_File(File,msg)
        await Check_Dir(Dl_Dir)

@bot.on_message(filters.private & filters.incoming)
async def _telegram_file(client, message):
  User_Id = message.from_user.id
  if User_Id not in list(Audio_Dict.keys()) :
    Audio_Dict[User_Id] = {'AudioList':[],'StartP':1}
  if message.audio : 
    Audio_Dict[User_Id]["AudioList"].append(message)
  elif message.text : 
    if message.text == '/finish' :
      AudioList = Audio_Dict[User_Id]["AudioList"]
      StartP = Audio_Dict[User_Id]["StartP"]
      await Renm(AudioList,StartP,message)
      Audio_Dict.pop(User_Id)
    
    elif message.text == '/goon' :
      #  msg = await Get_Msg(bot,User_Id,80398)
      #  print(msg)
      #  msg = await Get_Msg(bot,User_Id,80268)
      #  print(msg)
       await Renmid((80338,80399),926,7007648648)

    else : 
      Audio_Dict[User_Id]["StartP"] = int(message.text)


def main():
    if not os.path.exists(Dl_Dir): os.makedirs(Dl_Dir)
    try:
        bot.start()
        print("✅ Rename Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()