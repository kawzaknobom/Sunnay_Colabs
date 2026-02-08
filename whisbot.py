import nest_asyncio,os
nest_asyncio.apply()

#########################################################

Bot_Token = os.getenv('TOKEN')

########################################################

from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply,Message
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram import idle
from textwrap import wrap
import os,time,shutil,asyncio
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
from faster_whisper import WhisperModel

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
Audio_Forms = (".mp3",".ogg",".m4a",".aac",".flac",".wav",".wma",".opus",".3gpp")
Video_Forms = (".mp4",".mkv",".mov",".avi",".wmv",".avchd",".webm",".flv")

async def Mp3_Conv(File):
  mainDir = '/'.join(File.split('/')[:-1]) + '/'
  Mp3_File = mainDir +  File.split('/')[-1].split('.')[0] + '_Conv.mp3'
  Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
  os.system(Mp3_Cmd)
  return Mp3_File

async def whisper_transcribe(media_file):
  mainDir = '/'.join(media_file.split('/')[:-1]) + '/'
  TxtFile = mainDir + media_file.split('/')[-1].split('.')[0] + '_WTranscribed.txt'
  media_file = await Mp3_Conv(media_file)
  model = WhisperModel("large-v3", device="cuda", compute_type="int8")
  segments, info = model.transcribe(media_file, beam_size=5, vad_filter=True)
  for segment in segments:
    open(TxtFile,'a').write(f"{segment.text}")
  return TxtFile

def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  Session_file = Bot_Identifier+'_955hyh95|session_prm_bot'
  bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Bot_Token,in_memory=True)
  return bot,Bot_Identifier

bot,Bot_Identifier = Pyrogram_Client(Bot_Token)
dl_path = f'./downloads_{Bot_Identifier}/'

@bot.on_message(filters.command('start') & filters.private)
async def command1(bot,message):
   await message.reply('لبقية البوتات \n\n @sunnaybots')
  
@bot.on_message(filters.private & filters.incoming & (filters.audio | filters.voice | filters.video ))
async def _telegram_file(client, message):
  reply_msg = await message.reply('جار التفريغ')
  file = await message.download(file_name=dl_path)
  Txt_File = await whisper_transcribe(file)
  await message.reply_document(Txt_File)
  os.remove(Txt_File)
  await reply_msg.edit_text('تم التفريغ ✅')


def main():
    if not os.path.exists(dl_path): os.makedirs(dl_path)
    try:
        bot.start()
        print("✅ Whisper Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
           bot.stop()

main()
