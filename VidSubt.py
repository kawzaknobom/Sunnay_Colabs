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

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
Audio_Forms = (".mp3", ".ogg", ".m4a", ".aac", ".flac", ".wav", ".wma", ".opus", ".3gpp")
Video_Forms = (".mp4", ".mkv", ".mov", ".avi", ".wmv", ".avchd", ".webm", ".flv")

async def Mp3_Conv(File):
  mainDir = '/'.join(File.split('/')[:-1]) + '/'
  Mp3_File = mainDir + File.split('/')[-1].split('.')[0] + '_Conv.mp3'
  Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
  os.system(Mp3_Cmd)
  if os.path.exists(File) and not File.endswith(Audio_Forms) and not File.endswith('.mp3'):
      # الحفاظ على الفيديو الأصلي وعدم حذفه لكي نستخدمه لاحقاً في دمج الترجمة
      pass
  return Mp3_File

def format_time(seconds):
  hours = int(seconds // 3600)
  minutes = int((seconds % 3600) // 60)
  secs = int(seconds % 60)
  milliseconds = int(int((seconds - int(seconds)) * 1000))
  return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

async def whisper_transcribe_srt(media_file):
  mainDir = '/'.join(media_file.split('/')[:-1]) + '/'
  base_name = media_file.split('/')[-1].split('.')[0]
  Srt_File = mainDir + base_name + '.srt'
  
  # تحويل لاستخراج الصوت بغرض التفريغ السريع مع الاحتفاظ بملف الفيديو الأصلي
  audio_file = await Mp3_Conv(media_file)
  
  model = WhisperModel("large-v3", device="cuda", compute_type="int8")
  # استخدام task="translate" لترجمة أي لغة إلى الإنجليزية أو استخدم نموذج يدعم الترجمة المباشرة للعربية، أو task="translate" لترجمة الصوت الأجنبي للإنجليزية، أو إزالة task لجعلها باللغة الأصلية. 
  # بما أن المطلوب ترجمتها للعربية، يمكن ضبط task="translate" (إذا كانت من لغة أخرى) أو ترك النموذج يفرغ وينطق، وللحصول على ترجمة عربية دقيقة عبر وايسبر يمكن تمرير task="translate".
  segments, info = model.transcribe(audio_file, beam_size=5, vad_filter=True, task="translate")
  
  srt_content = ""
  for i, segment in enumerate(segments, start=1):
    start_str = format_time(segment.start)
    end_str = format_time(segment.end)
    text = segment.text.strip()
    srt_content += f"{i}\n{start_str} --> {end_str}\n{text}\n\n"
    
  with open(Srt_File, 'w', encoding='utf-8') as f:
    f.write(srt_content)
    
  if os.path.exists(audio_file):
    os.remove(audio_file)
    
  return Srt_File

async def burn_subtitles_ffmpeg(video_file, srt_file):
  mainDir = '/'.join(video_file.split('/')[:-1]) + '/'
  base_name = video_file.split('/')[-1].split('.')[0]
  output_video = mainDir + base_name + '_subtitled.mp4'
  
  # تجهيز مسار ملف الترجمة وتجنب مشاكل المسارات في FFMPEG (خصوصاً على أنظمة لينكس/ويندوز)
  # استخدام صيغة الفلتر subtitles مع تحديد حجم الخط 40 وخلفية مظللة (Box) باللون الأسود
  # force_style='FontSize=40,BackColour=&H80000000,BorderStyle=4' -> خلفية سوداء شبه شفافة مع خط بحجم 40
  # ملاحظة: في فلتر الـ subtitles بـ ffmpeg، المسارات التي تحتوى على رموز خاصة قد تحتاج الهروب (escaping)
  safe_srt_path = srt_file.replace('\\', '/').replace(':', '\\\\:')
  
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
  reply_msg = await message.reply('جارِ تحميل الملف ومعالجته عبر Whisper...')
  file = await message.download(file_name=dl_path)
  
  try:
    # 1. استخراج النصوص وتوليد ملف SRT مترجم
    await reply_msg.edit_text('جارِ استخراج وترجمة النصوص وتوليد ملف SRT...')
    Srt_File = await whisper_transcribe_srt(file)
    
    # إرسال ملف الـ SRT للمستخدم أولاً
    await message.reply_document(Srt_File, caption="ملف الترجمة المستخرج (SRT)")
    
    # 2. إذا كان الملف المدخل فيديو، نقوم بدمج الترجمة عليه
    if message.video or file.lower().endswith(Video_Forms):
      await reply_msg.edit_text('جارِ دمج الترجمة مع الفيديو عبر FFmpeg...')
      final_video = await burn_subtitles_ffmpeg(file, Srt_File)
      
      await reply_msg.edit_text('جارِ إرسال الفيديو المترجم...')
      await message.reply_video(final_video, caption="الفيديو بعد دمج الترجمة ✅")
      
      if os.path.exists(final_video):
        os.remove(final_video)
    else:
      await reply_msg.edit_text('تم استخراج ملف الترجمة بنجاح ✅')
      
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
        if Admin_Id :
          bot.send_message(Admin_Id, 'Started ✅')
        print("✅ Whisper Bot with SRT & FFmpeg Burn is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
           bot.stop()

main()