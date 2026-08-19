import nest_asyncio
nest_asyncio.apply()
import os

#########################################################

Bot_Token = os.environ['Bot_Token']
Api_Id = os.environ['Api_Id']
Api_Hash = os.environ['Api_Hash']

########################################################

from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply,Message
from pyrogram import Client, filters
from pyrogram import idle
import time,shutil,random

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  Session_file = Bot_Identifier+'_955hyh95|session_prm_bot'
  bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Bot_Token,in_memory=True)
  return bot,Bot_Identifier


bot,Bot_Identifier = Pyrogram_Client(Bot_Token)


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

    
def Create_Dir(Dir):
  if not os.path.isdir(Dir):
    Mkdir_Cmd = f'mkdir -p "{Dir}"'
    os.system(Mkdir_Cmd)
      
def Check_Dir(Dir):
  if os.path.isdir(Dir):
      shutil.rmtree(Dir)
  Create_Dir(Dir)

@bot.on_message(filters.command('start') & filters.private)
def command1(bot,message):
   User_Id = message.from_user.id
   message.reply('لبقية البوتات \n\n @sunnay6626')


def extract_epub(epub_path):
    Res_File = epub_path.replace('.epub','.txt')
    book = epub.read_epub(epub_path)
    content_blocks = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        text = soup.get_text(separator='\n', strip=True)
        
        if text:
            content_blocks.append(text)

    print(len(content_blocks))
    open(Res_File,'w').write("\n\n".join(content_blocks))
    return Res_File



@bot.on_message(filters.private & filters.incoming & (filters.document ))
def _telegram_file(client, message):
  User_Id = message.from_user.id
  dl_path = f'./downloads_{message.id}_{Bot_Identifier}/'
  dl_path = os.path.abspath(dl_path) + '/'
  if message.document.file_name.lower().endswith('epub'):
     Epub_File = File_Dl(message,dl_path)
     Res_File = Epub_File.replace('.epub','.txt')
     Text = extract_epub(Epub_File)
     message.reply_document(Res_File)
     Check_Dir(dl_path)

     

def main():
    try:
        bot.start()
        
        print("✅ Gemini Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()