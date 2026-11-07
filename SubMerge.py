import nest_asyncio, os
nest_asyncio.apply()

#########################################################
Bot_Token = os.getenv('TOKEN')  # ضع توكن البوت هنا أو في متغيرات البيئة
Admin_Id = int(os.getenv('Admin_Id', '0'))
#########################################################

import json,asyncio
from pyrogram import Client, filters
from pyrogram import idle
from pyrogram.types import Message

# بيانات الاتصال الخاصة بتطبيقك على Telegram
Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'

bot = Client("MergeSubBot", api_id=Api_Id, api_hash=Api_Hash, bot_token=Bot_Token)

# قاموس مؤقت لحفظ حالة المستخدمين (فيديو في انتظار ملف الترجمة)
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
        "1. أرسل ملف الفيديو أولاً.\n"
        "2. أرسل ملف الترجمة بصيغة (.srt) ثانياً وسأقوم بدمجهما فوراً وإرسال الفيديو المترجم."
    )

@bot.on_message(filters.private & (filters.video | filters.document))
async def receive_files(client, message: Message):
    user_id = message.from_user.id
    
    # التحقق مما إذا كان المرفق فيديو
    if message.video or (message.document and message.document.mime_type and "video" in message.document.mime_type):
        status_msg = await message.reply("📥 جاري تحميل الفيديو...")
        download_dir = f"./downloads_{user_id}/"
        os.makedirs(download_dir, exist_ok=True)
        
        video_path = await message.download(file_name=download_dir)
        user_states[user_id] = {"video_path": video_path, "status_msg_id": status_msg.id}
        
        await status_msg.edit_text("✅ تم استلام الفيديو بنجاح.\nالآن يرجى إرسال ملف الترجمة بصيغة (.srt).")
        return

    # التحقق مما إذا كان المرفق ملف ترجمة سبرت (.srt)
    if message.document and (message.document.file_name.endswith(".srt") or message.document.mime_type == "application/x-subrip"):
        if user_id not in user_states or "video_path" not in user_states[user_id]:
            await message.reply("⚠️ الرجاء إرسال ملف الفيديو أولاً قبل إرسال ملف الترجمة!")
            return
            
        state = user_states[user_id]
        status_msg = await client.get_messages(user_id, state["status_msg_id"])
        
        await status_msg.edit_text("📥 جاري تحميل ملف الترجمة...")
        download_dir = f"./downloads_{user_id}/"
        srt_path = await message.download(file_name=download_dir)
        
        try:
            await status_msg.edit_text("⏳ جاري دمج الترجمة بالفيديو عبر FFmpeg (قد يستغرق ذلك بعض الوقت)...")
            final_video = await burn_subtitles_ffmpeg(state["video_path"], srt_path)
            
            await status_msg.edit_text("📤 جاري رفع الفيديو المترجم...")
            await message.reply_video(final_video, caption="تم دمج الترجمة بنجاح ✅")
            
            # تنظيف الملفات المؤقتة
            if os.path.exists(final_video):
                os.remove(final_video)
            if os.path.exists(state["video_path"]):
                os.remove(state["video_path"])
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