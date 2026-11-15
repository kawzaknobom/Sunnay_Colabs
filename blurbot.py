import nest_asyncio, os, asyncio
nest_asyncio.apply()

Bot_Token = os.getenv('TOKEN')

from pyrogram import Client, filters, idle
from pyrogram.types import ForceReply, ReplyKeyboardMarkup, KeyboardButton
import cv2, shutil, numpy as np
from ultralytics import YOLO

# تحميل نموذج الـ Segmentation الخاص بيولو (يعطي أقنعة دقيقة للجسم بالكامل)
model = YOLO('yolov8n-seg.pt')

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
Audio_Forms = (".mp3", ".ogg", ".m4a", ".aac", ".flac", ".wav", ".wma", ".opus", ".3gpp")

Settings_Dict = {}

async def Create_Dir(Dir):
  if not os.path.isdir(Dir):
    os.makedirs(Dir, exist_ok=True)

async def Check_Dir(Dir):
  if os.path.isdir(Dir):
      shutil.rmtree(Dir)
  await Create_Dir(Dir)

async def Mp3_Conv(File):
  mainDir = '/'.join(File.split('/')[:-1]) + '/'
  Mp3_File = mainDir + File.split('/')[-1].split('.')[0] + '_Conv.mp3'
  os.system(f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y')
  return Mp3_File

async def Media_Compress(file_path, Rate=None):
  mainDir = '/'.join(file_path.split('/')[:-1]) + '/'
  if file_path.lower().endswith(Audio_Forms): 
   Res_File = mainDir + file_path.split('/')[-1].split('.')[0] + '_Comp.mp3'
   Comp_Cmd = f'ffmpeg -i "{file_path}" -b:a "{Rate}" "{Res_File}" -y '
  else:
    Res_File = mainDir + file_path.split('/')[-1].split('.')[0] + '_Comp.mp4'
    Comp_Cmd = f'ffmpeg -i "{file_path}" -c:v libx264 -crf 28 "{Res_File}" -y'
  os.system(Comp_Cmd)
  return Res_File

async def Vid_Mk(Vid, Aud):
  mainDir = '/'.join(Vid.split('/')[:-1]) + '/'
  Vid_Res = mainDir + Vid.split('/')[-1].split('.')[0] + '_Merged.mp4'
  os.system(f'ffmpeg -i "{Vid}" -i "{Aud}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{Vid_Res}" -y')
  return Vid_Res

def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  return Client(Bot_Identifier + '_session_seg_bot', api_id=Api_Id, api_hash=Api_Hash, bot_token=Bot_Token), Bot_Identifier

async def get_seconds(clock_time):
    splitted = clock_time.split(':')
    if len(splitted) == 3: 
      hours, minutes, seconds = map(float, clock_time.split(':'))
    elif len(splitted) == 2: 
      minutes = float(splitted[0])
      seconds = float(splitted[-1])
      hours = 0
    return (hours * 3600) + (minutes * 60) + seconds

async def Process_Video_Pro_Segmentation(file_path, replied, BlurRate, isfull, Ranges):
  BlurRate = int(BlurRate)
  mainDir = '/'.join(file_path.split('/')[:-1]) + '/'
  P_Name = mainDir + file_path.split('/')[-1].split('.')[0]
  Ex = file_path.split('.')[-1]
  Res_File = f"{P_Name}_ProBlurred.{Ex}"
  
  Aud = await Mp3_Conv(file_path)
  compressed_path = await Media_Compress(file_path)
  
  cap = cv2.VideoCapture(compressed_path)
  if not cap.isOpened():
    raise ValueError("Error opening video file")
  
  fps = cap.get(cv2.CAP_PROP_FPS)
  totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
  durationInSeconds = totalNoFrames // fps
  width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
  height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
  out = cv2.VideoWriter(Res_File, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
  
  ranges = []
  if not isfull and Ranges:
    for Range in Ranges.split(' '): 
      splitted = Range.split('-') 
      ranges.append([int(await get_seconds(splitted[0]) * fps), int(await get_seconds(splitted[1]) * fps)])

  ret_num = 0

  while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
      break
    ret_num += 1
    
    ispermit = True
    if not isfull:
      ispermit = False
      for x in ranges:
        if ret_num in range(x[0], x[1]):
          ispermit = True
          break

    if ret_num % int(fps) == 0 and durationInSeconds > 0:
      try:
        await replied.edit_text(f"🎬 جاري معالجة الفيديو بالتقسيم وتوسعة الأطراف... {int(ret_num / fps)} من {int(durationInSeconds)} ثانية")
      except:
        pass

    if ispermit:
      # تشغيل نموذج الـ Segmentation والتتبع الاحترافي للفريمات
      results = model.track(
          frame, 
          persist=True, 
          classes=[0],  # فئة الأشخاص فقط
          conf=0.4, 
          iou=0.4, 
          tracker="bytetrack.yaml", 
          verbose=False
      )
      
      # إذا وُجدت أقنعة (Masks) للأشخاص في الفريم
      if results[0].masks is not None:
        masks = results[0].masks.data.cpu().numpy()
        
        # إنشاء نسخة معالجة للبلور على كامل الفريم
        blurred_frame = cv2.blur(frame, (BlurRate, BlurRate))
        
        for mask in masks:
          resized_mask = cv2.resize(mask, (width, height))
          binary_mask = (resized_mask > 0.3).astype(np.uint8) * 255
          
          # توسيع القناع (Dilation) لتغطية الأطراف والأكتاف بالكامل دون فراغات
          kernel = np.ones((25, 25), np.uint8)
          dilated_mask = cv2.dilate(binary_mask, kernel, iterations=1)
          
          final_mask = (dilated_mask > 0).astype(np.uint8)
          
          # دمج البلور مع الفريم الأصلي بناءً على القناع المُوَسَّع
          frame = np.where(final_mask[:, :, None] == 1, blurred_frame, frame)

    out.write(frame)

  cap.release()
  out.release()
  
  Final_Res = await Vid_Mk(Res_File, Aud)
  return await Media_Compress(Final_Res)

bot, Bot_Identifier = Pyrogram_Client(Bot_Token)
Dl_Dir = f'./ProSeg_{Bot_Identifier}/'

@bot.on_message(filters.command('start') & filters.private)
async def command_start(bot, message):
   Settings_Dict.clear()
   await message.reply_text(
    "👋 أهلاً بك في بوت العزل الاحترافي (Segmentation).\nاختر درجة البلور المطلوبة:",
    reply_markup=ReplyKeyboardMarkup([
        [KeyboardButton("11"), KeyboardButton("31")],
        [KeyboardButton("109"), KeyboardButton("185")],
        [KeyboardButton("261"), KeyboardButton("491")]
    ], resize_keyboard=True)
   )

@bot.on_message(filters.private & filters.incoming & filters.text)
async def _text_handler(client, message):
  User_Id = message.from_user.id
  if User_Id not in Settings_Dict: 
    Settings_Dict[User_Id] = {'BlurRate': '', 'isfull': True, 'Ranges': ''}
  
  if message.text in ['11', '31', '109', '185', '261', '491']:
    Settings_Dict[User_Id]['BlurRate'] = message.text 
    await message.reply_text(
        "اختر نمط المعالجة:",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("Full Vid"), KeyboardButton("Ranges")]
        ], resize_keyboard=True)
    )
  elif message.text == 'Full Vid':
    Settings_Dict[User_Id]['isfull'] = True
    await message.reply("✅ تم الحفظ. أرسل الفيديو الآن للمعالجة!")
  elif message.text == 'Ranges':
    Settings_Dict[User_Id]['isfull'] = False
    await message.reply("أرسل النطاق الزمني بصيغة:\n`hh:mm:ss-hh:mm:ss`", reply_markup=ForceReply(True))

@bot.on_message(filters.private & filters.reply & filters.text)
async def _ranges_reply_handler(client, message):
  User_Id = message.from_user.id
  if User_Id in Settings_Dict:
    Settings_Dict[User_Id]['Ranges'] = message.text
    await message.reply("✅ تم حفظ النطاق. أرسل الفيديو الآن!")

@bot.on_message(filters.private & filters.incoming & filters.video)
async def _video_handler(client, message):
  User_Id = message.from_user.id
  if User_Id not in Settings_Dict or not Settings_Dict[User_Id]['BlurRate']:
    await message.reply('⚠️ يرجى إعادة ضبط الإعدادات بالضغط على: /start')
    return

  cfg = Settings_Dict[User_Id]
  replied = await message.reply('🚀 جاري تحميل الفيديو وبدء التقسيم والعزل الاحترافي...')
  Vid_Path = await message.download(file_name=Dl_Dir)
  
  try:
    Blurred_Vid = await Process_Video_Pro_Segmentation(Vid_Path, replied, cfg['BlurRate'], cfg['isfull'], cfg['Ranges'])
    await replied.edit_text('✅ تمت العملية باحترافية تامة!')
    await message.reply_video(Blurred_Vid)
  except Exception as e:
    await replied.edit_text(f'❌ حدث خطأ: {str(e)}')
  finally:
    await Check_Dir(Dl_Dir)

def main():
    if not os.path.exists(Dl_Dir): os.makedirs(Dl_Dir)
    bot.start()
    print("✅ Pro Segmentation Bot is ONLINE!")
    idle()
    bot.stop()

if __name__ == '__main__':
    main()