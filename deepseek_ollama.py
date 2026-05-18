import nest_asyncio
import os
nest_asyncio.apply()
#########################################################

Bot_Token = os.getenv('TOKEN')

if Bot_Token == '5623514771:AAEUXl-8JzuhWhRoQBujXQRALoSKYVbqHDA':
   Admin_Id = 7007648648
else :
   Admin_Id = None

########################################################

from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , ReplyKeyboardMarkup , CallbackQuery , ForceReply,Message
from pyrogram import Client, filters,enums,StopTransmission,idle
from pyrogram.errors import FloodWait

from pathlib import Path
from PIL import Image
import os,shutil,datetime,time
import ollama


######### Constants

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
Image_forms = (".jpg",".png",'.tif','webp')
Token = str(Bot_Token)
Token_Identifier = Token.split(':')[0]
Download_Path = f'./Download_{Token_Identifier}/'
Session_file = Token_Identifier +'_session_bot'

###########

def Get_File(Dl_Dir,File_Ex):
  for file in os.listdir(Dl_Dir):
    if file.lower().endswith(File_Ex):
      return os.path.abspath(Dl_Dir + file)
  return None

async def OllamaAi_Trans(Text):
    response = ollama.chat(model='deepseek-r1:8b', messages=[
        {
            'role': 'user',
            'content': f"ترجم النص التالي إلى العربية بدقة وبأسلوب بليغ:\n\n{Text}"
        }
    ])

    return response['message']['content']


#### Token #####

bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Token)

#############


@bot.on_message(filters.private & filters.incoming)
async def _telegram_file(client, message):
      if message.text : 
          if message.text == '/start':
              await message.reply('لبقية البوتات \n\n @sunnaybots')
          else :
              replied = await message.reply(f"جاري الترجمة  ☕️ ")
              res = await OllamaAi_Trans(message.text)
              await message.reply(res)
              await replied.edit_text('تمت الترجمة')
      elif message.document :
        replied = await message.reply(f"جاري الترجمة  ☕️ ")
        File = await message.download(file_name=Download_Path)
        if ' ' in File:
            os.rename(File,File.replace(' ','_'))
            File = File.replace(' ','_')
        res = await OllamaAi_Trans(open(File,'r').read())
        await message.reply(res)
        await replied.edit_text('تمت الترجمة')


def main():
    if not os.path.exists(Download_Path): os.makedirs(Download_Path)
    try:
        bot.start()
        if Admin_Id :
          bot.send_message(Admin_Id,'Started ✅')
        print("✅ Music Removal Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()
