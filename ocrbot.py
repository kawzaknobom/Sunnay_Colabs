import nest_asyncio
nest_asyncio.apply()
import os

#########################################################

Bot_Token = os.getenv('TOKEN')

########################################################

from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply,Message
from pyrogram import Client, filters
from pyrogram import idle
import os,time,shutil,subprocess

def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  Session_file = Bot_Identifier+'_955hyh95|session_prm_bot'
  bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Bot_Token,in_memory=True)
  return bot,Bot_Identifier

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
bot,Bot_Identifier = Pyrogram_Client(Bot_Token)


Ocr_dl_path = f'./downloads_{Bot_Identifier}/'

ServAcc_Dir = f'./ServAcc_{Bot_Identifier}/'

ServAcc_File = ''


def Get_File(Dl_Dir,File_Ex):
  for file in os.listdir(Dl_Dir):
    if file.lower().endswith(File_Ex):
      return os.path.abspath(Dl_Dir + file)
  return None
      
      
def Ocr_Func(Ocr_Path,Serv_Acc):
  
  Dir_Path = ('.' if Ocr_Path.startswith('.') else '') + '/'.join(Ocr_Path.split('/')[:-1]) + '/'
  Tahweel_Cmd = f'''tahweel "{Ocr_Path}" \
    --service-account-credentials "{Serv_Acc}" \
    --pdf2image-thread-count 8 \
    --processor-max-workers 8 \
    --txt-page-separator 🟥 '''
  p = subprocess.Popen(Tahweel_Cmd,cwd=Dir_Path,shell=True)
  p.wait()
  Txt_File = Get_File(Dir_Path,'txt')
  Docx_File = Get_File(Dir_Path,'docx')
  return Txt_File,Docx_File


@bot.on_message(filters.private & filters.incoming)
async def _telegram_file(client, message):
  if message.document : 
     if message.document.file_name.lower().endswith('json') : 
        globals()['ServAcc_File'] = await message.download(file_name=ServAcc_File)
        await message.reply('تم تلقيم ملف Ocr')
     else :
        if len(globals()['ServAcc_File']) == 0 : 
            await message.reply('قم بإرسال ملف Service Account')
        else : 
           replied = await message.reply('جار العمل')
           Ocr_File = await message.download(file_name=Ocr_dl_path)
           Txt_File,Docx_File = Ocr_Func(Ocr_File,globals()['ServAcc_File'])
           await message.reply_document(Txt_File)
           await message.reply_document(Docx_File)
           await replied.edit_text('تم العمل')
  elif message.photo :
     if len(globals()['ServAcc_File']) == 0 : 
        await message.reply('قم بإرسال ملف Service Account')
     else :
           replied = await message.reply('جار العمل')
           Ocr_File = await message.download(file_name=Ocr_dl_path)
           Txt_File,Docx_File = Ocr_Func(Ocr_File,globals()['ServAcc_File'])
           await message.reply(open(Txt_File,'r').read())
           await replied.edit_text('تم العمل')


def main():
    try:
        bot.start()
        print("✅ TTS Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()
