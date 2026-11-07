import nest_asyncio, os
nest_asyncio.apply()

#########################################################
Bot_Token = os.getenv('TOKEN')  # ضع توكن البوت هنا أو في متغيرات البيئة
Admin_Id = int(os.getenv('Admin_Id', '0'))
#########################################################

import json, asyncio
from pyrogram import Client, filters
from pyrogram import idle
from pyrogram.types import Message

# بيانات الاتصال الخاصة بتطبيقك على Telegram
Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'

bot = Client("MergeSubBot", api_id=Api_Id, api_hash=Api_Hash, bot_token=Bot_Token)

# قاموس مؤقت لحفظ رسالة الفيديو للمستخدمين حتى يتم إرسال ملف الترجمة
user_states = {}

async def run_command(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode(), stderr.decode()

async def get_video_dimensions(video_file):
    try:
        cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of json "{video_file}"'
        stdout, _ = await run_command(cmd)
        data = json.loads(stdout)
        width = data['streams'][0]['width']
        height = data['streams'][0]['height']
        return int(width), int(height)
    except Exception as e:
        print(f"Error getting video dimensions: {e}")
        return 1080, 1920

async def burn_subtitles_ffmpeg(video_file, srt_file):
    mainDir = '/'.join(video_file.split('/')[:-1]) + '/'
    base_name = video_file.split('/')[-1].split('.')[0]
    output_video = mainDir + base_name + '_subtitled.mp4'
    
    width, height = await get_video_dimensions(video_file)
    is_portrait = height > width
    
    if is_portrait:
        font_size = max(14, min(18, int(width * 0.024)))
        margin_v = int(height * 0.05)
    else:
        font_size = max(22, min(36, int(width * 0.025)))
        margin_v = int(height * 0.06)
    
    safe_srt_path = srt_file.replace('\\', '/').replace(':', '\\\\:')
    
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
    
    safe_font_path = font_path.replace('\\', '/').replace(':', '\\\\:')

    ffmpeg_cmd = (
        f'ffmpeg -i "{video_file}" -vf "subtitles=\'{safe_srt_path}\':force_style=\'Fontfile={safe_font_path},FontSize={font_size},PrimaryColour=&H00FFFFFF,BackColour=&H00000000,BorderStyle=4,MarginV={margin_v},Alignment=2,Encoding=1\'" '
        f'-c:a copy "{output_video}" -y'
    )
    
    await run_command(ffmpeg_cmd)
    return output_video

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    await message.reply(
        "مرحباً بك في بوت دمج الترجمة! 🎬\n\n"
        "الخطوات:\n"
        "1. أرسل ملف الفيديو أولاً (سيتم حفظه مؤقتاً بدون تحميل).\n"
        "2. أرسل ملف الترجمة (.srt) وسيقوم البوت بتحميل الفيديو والترجمة معاً لدمجهما فوراً."
    )

@bot.on_message(filters.private & (filters.video | filters.document))
async def receive_files(client, message: Message):
    user_id = message.from_user.id
    
    # 1. إذا كان المرفق فيديو: نقوم بحفظ مرجع الرسالة فقط دون تحميل
    if message.video or (message.document and message.document.mime_type and "video" in message.document.mime_type):
        status_msg = await message.reply("📌 تم استلام وحفظ رسالة الفيديو بانتظار ملف الترجمة...")
        
        # تخزين كائن الرسالة الخاص بالفيديو وحالة رسالة التنبيه
        user_states[user_id] = {
            "video_message": message,
            "status_msg_id": status_msg.id
        }
        return

    # 2. إذا كان المرفق ملف ترجمة (.srt): نقوم بتحميل الفيديو والترجمة معاً الآن
    if message.document and (message.document.file_name.endswith(".srt") or message.document.mime_type == "application/x-subrip"):
        if user_id not in user_states or "video_message" not in user_states[user_id]:
            await message.reply("⚠️ الرجاء إرسال ملف الفيديو أولاً قبل إرسال ملف الترجمة!")
            return
            
        state = user_states[user_id]
        status_msg = await client.get_messages(user_id, state["status_msg_id"])
        
        try:
            download_dir = f"./downloads_{user_id}/"
            os.makedirs(download_dir, exist_ok=True)
            
            # تحميل الفيديو الآن
            await status_msg.edit_text("📥 جاري تحميل الفيديو...")
            video_path = await state["video_message"].download(file_name=download_dir)
            
            # تحميل ملف الترجمة الآن
            await status_msg.edit_text("📥 جاري تحميل ملف الترجمة...")
            srt_path = await message.download(file_name=download_dir)
            
            # بدء عملية الدمج عبر FFmpeg
            await status_msg.edit_text("⏳ جاري دمج الترجمة بالفيديو عبر FFmpeg (قد يستغرق ذلك بعض الوقت)...")
            final_video = await burn_subtitles_ffmpeg(video_path, srt_path)
            
            # رفع الناتج
            await status_msg.edit_text("📤 جاري رفع الفيديو المترجم...")
            await message.reply_video(final_video, caption="تم دمج الترجمة بنجاح ✅")
            
            # تنظيف الملفات المؤقتة
            if os.path.exists(final_video):
                os.remove(final_video)
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(srt_path):
                os.remove(srt_path)
                
            del user_states[user_id]
            await status_msg.delete()
            
        except Exception as e:
            await status_msg.edit_text(f"❌ حدث خطأ أثناء عملية الدمج:\n`{str(e)[:3000]}`")

async def start_bot_async():
    try:
        await bot.start()
        if Admin_Id != 0:
            await bot.send_message(Admin_Id, 'Bot is Running ✅')
        print(f"✅ Ytdl Bot is ONLINE!")
        await idle()
    finally:
        if bot.is_connected:
            await bot.stop()

if __name__ == '__main__':
    asyncio.run(start_bot_async())