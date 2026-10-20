import nest_asyncio, os
nest_asyncio.apply()

#########################################################

Bot_Token = os.getenv('TOKEN')

########################################################

from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply, Message
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram import idle
import os, time, shutil, asyncio

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
Audio_Forms = (".mp3", ".ogg", ".m4a", ".aac", ".flac", ".wav", ".wma", ".opus", ".3gpp")
Video_Forms = (".mp4", ".mkv", ".mov", ".avi", ".wmv", ".avchd", ".webm", ".flv")

async def Mp3_Conv(File):
  mainDir = '/'.join(File.split('/')[:-1]) + '/'
  Mp3_File = mainDir + File.split('/')[-1].split('.')[0] + '_Conv.mp3'
  Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
  os.system(Mp3_Cmd)
  return Mp3_File

def format_time(seconds):
  hours = int(seconds // 3600)
  minutes = int((seconds % 3600) // 60)
  secs = int(seconds % 60)
  milliseconds = int(int((seconds - int(seconds)) * 1000))
  return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

async def whisper_transcribe_and_translate_srt(media_file):
  mainDir = '/'.join(media_file.split('/')[:-1]) + '/'
  base_name = media_file.split('/')[-1].split('.')[0]
  Srt_File = mainDir + base_name + '_AR.srt'
  
  # استخراج الصوت للتفريغ السريع
  audio_file = await Mp3_Conv(media_file)
  
  # تحميل نموذج Whisper للتفريغ الدقيق باللغة الإنجليزية
  model = WhisperModel("large-v3", device="cuda", compute_type="int8")
  segments, info = model.transcribe(audio_file, beam_size=5, vad_filter=True, language="en")
  
  translator = GoogleTranslator(source='en', target='ar')
  
  srt_content = ""
  for i, segment in enumerate(segments, start=1):
    start_str = format_time(segment.start)
    end_str = format_time(segment.end)
    text_en = segment.text.strip()
    
    # ترجمة النص الإنجليزي إلى العربية
    try:
      text_ar = translator.translate(text_en) if text_en else ""
    except Exception:
      text_ar = text_en
      
    srt_content += f"{i}\n{start_str} --> {end_str}\n{text_ar}\n\n"
    
  with open(Srt_File, 'w', encoding='utf-8') as f:
    f.write(srt_content)
    
  if os.path.exists(audio_file):
    os.remove(audio_file)
    
  return Srt_File

async def burn_subtitles_ffmpeg(video_file, srt_file):
  mainDir = '/'.join(video_file.split('/')[:-1]) + '/'
  base_name = video_file.split('/')[-1].split('.')[0]
  output_video = mainDir + base_name + '_subtitled.mp4'
  
  safe_srt_path = srt_file.replace('\\', '/').replace(':', '\\\\:')
  
  # FontSize=40, خلفية سوداء مظللة BorderStyle=4, BackColour أسود شبيف
  ffmpeg_cmd = (
    f'ffmpeg -i "{video_file}" -vf "subtitles=\'{safe_srt_path}\':force_style=\'FontSize=40,PrimaryColour=&H00FFFFFF,BackColour=&H80000000,BorderStyle=4\'" '
    f'-c:a copy "{output_video}" -y'
  )
  
  os.system(ffmpeg_cmd)
  return output_video

def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  Session_file = Bot_Identifier + '_955hyh95|session_prm_bot'
  bot = Client(Session_file, api_id=Api_Id, api_hash=Api_Hash, bot_token=Bot_Token, in_memory=True)
  return bot, Bot_Identifier

bot, Bot_Identifier = Pyrogram_Client(Bot_Token)
dl_path = f'./downloads_{Bot_Identifier}/'

@bot.on_message(filters.command('start') & filters.private)
async def command1(bot, message):
   await message.reply('لبقية البوتات \n\n @sunnaybots')
  
@bot.on_message(filters.private & filters.incoming & (filters.audio | filters.voice | filters.video))
async def _telegram_file(client, message):
  reply_msg = await message.reply('جارِ تحميل الفيديو وتفريغ الصوت بالإنجليزية...')
  file = await message.download(file_name=dl_path)
  
  try:
    # 1. تفريغ الصوت الإنجليزي وترجمته للعربية مع استخراج ملف SRT
    await reply_msg.edit_text('جارِ ترجمة النصوص إلى العربية وتوليد ملف SRT...')
    Srt_File = await whisper_transcribe_and_translate_srt(file)
    
    # إرسال ملف الـ SRT العربي للمستخدم
    await message.reply_document(Srt_File, caption="ملف الترجمة العربي المستخرج (SRT) ✅")
    
    # 2. دمج الترجمة على الفيديو عبر FFmpeg
    if message.video or file.lower().endswith(Video_Forms):
      await reply_msg.edit_text('جارِ دمج الترجمة العربية على الفيديو بخلفية مظللة وحجم خط 40...')
      final_video = await burn_subtitles_ffmpeg(file, Srt_File)
      
      await reply_msg.edit_text('جارِ رفع الفيديو المترجم...')
      await message.reply_video(final_video, caption="الفيديو المترجم جاهز ✅")
      
      if os.path.exists(final_video):
        os.remove(final_video)
    else:
      await reply_msg.edit_text('تم استخراج ملف الترجمة العربي بنجاح ✅')
      
    if os.path.exists(Srt_File):
      os.remove(Srt_File)
      
  except Exception as e:
    await reply_msg.edit_text(f'حدث خطأ أثناء المعالجة: {str(e)}')
  
  if os.path.exists(file):
    os.remove(file)

def main():
    if not os.path.exists(dl_path): os.makedirs(dl_path)
    try:
        bot.start()
        print("✅ Whisper + Translator Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
           bot.stop()

main()