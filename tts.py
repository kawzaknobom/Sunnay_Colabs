import nest_asyncio
nest_asyncio.apply()
import os

#########################################################

Bot_Token = os.getenv('TOKEN')

########################################################

from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply,Message
from pyrogram import Client, filters
from pyrogram import idle
import os,time,shutil,asyncio,edge_tts
from shakkala import Shakkala
sh = Shakkala()

VOICE = "ar-EG-ShakirNeural"

# from TTS.api import TTS

# tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")

# Cloned_Voice_Link = "https://archive.org/download/Arch_Sunnay_Upld/shams.mp3" ###### صوت محمد بن شمس الدين كاختبار 
# os.sytem(f"wget '{Cloned_Voice_Link}'")

async def Mp3_Conv(File):
  Mp3_File = ('.' if File.startswith('.') else '') +  File.split('.')[(1 if File[0] == '.' else 0)] + '_Conv.mp3'
  Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
  os.system(Mp3_Cmd)
  return Mp3_File

async def tts_ai(text):
 Res = 'test_arabic.mp3'
 communicate = edge_tts.Communicate(text, VOICE)
 await communicate.save(Res)
 # Res = "output.wav"
 # await tts.tts_to_file(
 #    text=text,
 #    speaker_wav="Cloned_Voice_Link.split('/')[-1]", 
 #    language="ar",
 #    file_path="output.wav")
 return Res

async def tashkil_func(text):
  input_int = sh.prepare_input(text)
  model, graph = sh.get_model()
  logits = model.predict(input_int)[0]
  predicted_harakat = sh.logits_to_text(logits)
  final_output = sh.get_final_text(text, predicted_harakat)
  return final_output

def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  Session_file = Bot_Identifier+'_955hyh95|session_prm_bot'
  bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Bot_Token,in_memory=True)
  return bot,Bot_Identifier

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
bot,Bot_Identifier = Pyrogram_Client(Bot_Token)


@bot.on_message(filters.private & filters.incoming & (filters.text))
async def _telegram_file(client, message):
  reply_msg = await message.reply('جار العمل')
  text = await tashkil_func(message.text)
  await message.reply(text)
  # Audio_File = await tts_ai(text)
  # # Audio_File = Mp3_Conv(Audio_File)
  # await message.reply_document(Audio_File)
  # os.remove(Audio_File)
  await reply_msg.edit_text('تم الإنتاج ✅')


def main():
    try:
        bot.start()
        print("✅ TTS Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()
