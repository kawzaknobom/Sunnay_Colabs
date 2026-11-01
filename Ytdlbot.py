import nest_asyncio,os
nest_asyncio.apply()

#########################################################

BOT_TOKEN = os.getenv('TOKEN')
Admin_Id = int(os.getenv('Admin_Id','0'))
API_ID = 15952578
API_HASH = '3600ce5f8f9b9e18cba0f318fa0e3600'

########################################################

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp
from pyrogram import idle

# --- CONFIGURATION ---


app = Client(
    "youtube_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "👋 **أهلاً بك!** أرسل لي أي رابط فيديو من يوتيوب، وسأتيح لك اختيار الجودة أو تحميله كصوت."
    )

@app.on_message(filters.text & (filters.regex("http://") | filters.regex("https://")))
async def get_video_options(client: Client, message: Message):
    url = message.text.strip()
    
    status_msg = await message.reply_text("⏳ **جاري جلب معلومات الفيديو...**")

    # استخراج معلومات الفيديو لتوليد الأزرار المناسبة
    try:
        def fetch_info():
            ydl_opts = {'extract_flat': False, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, fetch_info)
        title = info.get('title', 'YouTube Video')
        
        # إنشاء أزرار الجودات والصوت
        # نستخدم الـ URL أو معرف الفيديو مخفياً في الكولباك (يفضل حفظ الرابط في قاعدة بيانات أو تمريره بحذر، هنا سنبسطه بترميز بسيط أو تمريره مباشرة إذا كان قصيراً)
        # ملاحظة: Telegram Callback data محدود بـ 64 بايت، لذا سنستخدم اختصاراً أو نمرر رابط يوتيوب القصير إن أمكن، أو نستخدم تخزين مؤقت.
        # للتبسيط، سنستخدم معرف الفيديو (video id)
        video_id = info.get('id')
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎬 جودة عالية (1080p)", callback_data=f"dl|1080|{video_id}"),
                InlineKeyboardButton("🎬 جودة متوسطة (720p)", callback_data=f"dl|720|{video_id}")
            ],
            [
                InlineKeyboardButton("🎬 جودة منخفضة (480p)", callback_data=f"dl|480|{video_id}"),
                InlineKeyboardButton("🎵 تحويل إلى صوت (MP3)", callback_data=f"dl|mp3|{video_id}")
            ]
        ])

        await status_msg.edit_text(
            f"📌 **{title}**\n\nاختر صيغة التحميل المطلوبة:",
            reply_markup=keyboard
        )

    except Exception as e:
        await status_msg.edit_text(f"❌ **حدث خطأ أثناء جلب المعلومات:**\n`{str(e)}`")

# معالجة الضغط على الأزرار
@app.on_callback_query(filters.regex("^dl\|"))
async def handle_download_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")
    quality = data[1]
    video_id = data[2]
    url = f"https://youtu.be/{video_id}"
    
    message = callback_query.message
    await message.edit_text("📥 **جاري التحميل والمعالجة... يرجى الانتظار.**")

    os.makedirs("downloads", exist_ok=True)
    
    try:
        if quality == "mp3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            # اختيار الجودة بناءً على طلب المستخدم
            ydl_opts = {
                'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
            }

        def download_media():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # إذا كان MP3، سيتغير الامتداد
                if quality == "mp3":
                    file_path = os.path.join("downloads", f"{video_id}.mp3")
                else:
                    file_path = ydl.prepare_filename(info)
                    # أحياناً yt-dlp لا يدمج الامتداد بدقة مطلقة مع postprocessor إذا لم يُحدد، لكن مع الدمج الافتراضي يعمل جيداً
                return info, file_path

        loop = asyncio.get_running_loop()
        info, file_path = await loop.run_in_executor(None, download_media)
        
        title = info.get('title', 'Media')
        
        if not os.path.exists(file_path):
            # محاولة البحث عن الملف بالامتداد الصحيح إذا تغير
            for f in os.listdir("downloads"):
                if f.startswith(video_id):
                    file_path = os.path.join("downloads", f)
                    break

        if not os.path.exists(file_path):
            await message.edit_text("❌ **فشل التحميل:** لم يتم العثور على الملف الناتج.")
            return

        await message.edit_text("📤 **جاري الرفع إلى تيليجرام...**")

        if quality == "mp3":
            await client.send_audio(
                chat_id=message.chat.id,
                audio=file_path,
                title=title,
                performer=info.get('uploader', 'YouTube')
            )
        else:
            await client.send_video(
                chat_id=message.chat.id,
                video=file_path,
                caption=f"🎬 **{title}**",
                duration=info.get('duration', 0),
                supports_streaming=True
            )

        # تنظيف الملفات المؤقتة
        await message.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await message.edit_text(f"❌ **حدث خطأ أثناء التحميل:**\n`{str(e)}`")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    print("Bot is starting...")
    app.run()

async def start_bot_async():
    try:
        await app.start()
        if Admin_Id != 0:
            await app.send_message(Admin_Id, 'Vidsub Bot Started with Global List Loop ✅')
        print(f"✅ WhisperX + Gemini Async Subtitles Bot (Global List Loop) is ONLINE!")
        await idle()
    finally:
        if app.is_connected:
            await app.stop()

if __name__ == '__main__':
    asyncio.run(start_bot_async())