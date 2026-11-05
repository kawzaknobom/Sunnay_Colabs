import nest_asyncio, os
nest_asyncio.apply()

#########################################################

BOT_TOKEN = os.getenv('TOKEN')
Admin_Id = int(os.getenv('Admin_Id', '0'))
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
        "👋 **أهلاً بك!** أرسل لي أي رابط فيديو، قائمة تشغيل (Playlist)، أو قناة يوتيوب، وسأتيح لك خيارات التحميل المناسبة."
    )

@app.on_message(filters.text & (filters.regex("http://") | filters.regex("https://")))
async def get_video_options(client: Client, message: Message):
    url = message.text.strip()
    
    status_msg = await message.reply_text("⏳ **جاري جلب معلومات الرابط...**")

    try:
        def fetch_info():
            ydl_opts = {'extract_flat': False, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, fetch_info)
        
        is_playlist = 'entries' in info
        title = info.get('title', 'YouTube Content')
        
        if not hasattr(app, 'url_cache'):
            app.url_cache = {}

        if is_playlist:
            entries_count = len(info.get('entries', []))
            playlist_id = info.get('id', 'playlist')
            
            # استخدام مفتاح قصير لتجنب تجاوز حد 64 بايت في التيليجرام
            short_id = playlist_id[:8] if len(playlist_id) > 8 else playlist_id
            app.url_cache[short_id] = url

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📂 تحميل القائمة كاملة (فيديو)", callback_data=f"pl|vid|{short_id}"),
                    InlineKeyboardButton("🎵 تحميل القائمة كاملة (صوت MP3)", callback_data=f"pl|mp3|{short_id}")
                ]
            ])
            await status_msg.edit_text(
                f"📌 **قائمة تشغيل / قناة:** {title}\n📊 **عدد العناصر الظاهرة:** {entries_count}\n\nاختر صيغة التحميل:",
                reply_markup=keyboard
            )
        else:
            video_id = info.get('id', 'video')
            short_id = video_id[:8] if len(video_id) > 8 else video_id
            app.url_cache[short_id] = url

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎬 جودة عالية (1080p)", callback_data=f"dl|1080|{short_id}"),
                    InlineKeyboardButton("🎬 جودة متوسطة (720p)", callback_data=f"dl|720|{short_id}")
                ],
                [
                    InlineKeyboardButton("🎬 جودة منخفضة (480p)", callback_data=f"dl|480|{short_id}"),
                    InlineKeyboardButton("🎵 تحويل إلى صوت (MP3)", callback_data=f"dl|mp3|{short_id}")
                ]
            ])

            await status_msg.edit_text(
                f"📌 **{title}**\n\nاختر صيغة التحميل المطلوبة:",
                reply_markup=keyboard
            )

    except Exception as e:
        await status_msg.edit_text(f"❌ **حدث خطأ أثناء جلب المعلومات:**\n`{str(e)}`")

# معالجة الضغط على أزرار الفيديوهات الفردية
@app.on_callback_query(filters.regex(r"^dl\|"))
async def handle_download_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")
    quality = data[1]
    short_id = data[2]
    
    url = getattr(app, 'url_cache', {}).get(short_id, f"https://youtu.be/{short_id}")
    
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
            ydl_opts = {
                'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
            }

        def download_media():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # استخدام المعرف الفعلي من الـ info إذا توفر
                actual_id = info.get('id', short_id)
                if quality == "mp3":
                    file_path = os.path.join("downloads", f"{actual_id}.mp3")
                else:
                    file_path = ydl.prepare_filename(info)
                return info, file_path

        loop = asyncio.get_running_loop()
        info, file_path = await loop.run_in_executor(None, download_media)
        
        title = info.get('title', 'Media')
        actual_id = info.get('id', short_id)
        
        if not os.path.exists(file_path):
            for f in os.listdir("downloads"):
                if actual_id in f or f.startswith(short_id):
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

        await message.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await message.edit_text(f"❌ **حدث خطأ أثناء التحميل:**\n`{str(e)}`")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

# معالجة الضغط على أزرار قوائم التشغيل والقنوات مع الترقيم
@app.on_callback_query(filters.regex(r"^pl\|"))
async def handle_playlist_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")
    media_type = data[1] # vid or mp3
    short_id = data[2]
    
    url = getattr(app, 'url_cache', {}).get(short_id)
    if not url:
        await callback_query.message.edit_text("❌ **انتهت صلاحية الرابط أو حدث خطأ، يرجى إرساله مجدداً.**")
        return

    message = callback_query.message
    await message.edit_text("📥 **جاري تحميل قائمة التشغيل/القناة كاملة... قد يستغرق ذلك وقتاً حسب عدد الفيديوهات.**")

    os.makedirs("downloads", exist_ok=True)

    try:
        if media_type == "mp3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(playlist_title)s/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': 'downloads/%(playlist_title)s/%(title)s.%(ext)s',
            }

        def download_playlist():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)

        loop = asyncio.get_running_loop()
        playlist_info = await loop.run_in_executor(None, download_playlist)
        
        playlist_title = playlist_info.get('title', 'Playlist')
        entries = [e for e in playlist_info.get('entries', []) if e is not None]
        total_count = len(entries)

        await message.edit_text(f"📤 **تم اكتمال تحميل قائمة التشغيل ({playlist_title}). جاري رفع {total_count} ملف إلى تيليجرام مع الترقيم...**")

        sent_count = 0
        
        for index, entry in enumerate(entries, start=1):
            vid_title = entry.get('title', 'video')
            vid_id = entry.get('id')
            
            target_file = None
            for root, dirs, files in os.walk("downloads"):
                for file in files:
                    if vid_id in file or (vid_title[:10] in file):
                        target_file = os.path.join(root, file)
                        break
                if target_file:
                    break

            if target_file and os.path.exists(target_file):
                try:
                    caption_text = f"🎬 **{vid_title}**\n\n📌 **فيديو ({index} من أصل {total_count})**"
                    audio_title = f"{vid_title} ({index}/{total_count})"

                    if media_type == "mp3":
                        await client.send_audio(
                            chat_id=message.chat.id,
                            audio=target_file,
                            title=audio_title,
                            performer=f"{playlist_title} [{index}/{total_count}]"
                        )
                    else:
                        await client.send_video(
                            chat_id=message.chat.id,
                            video=target_file,
                            caption=caption_text,
                            supports_streaming=True
                        )
                    sent_count += 1
                    os.remove(target_file)
                except Exception as send_err:
                    print(f"Failed to send {vid_title}: {send_err}")

        await message.edit_text(f"✅ **تم الانتهاء بنجاح!** تم إرسال {sent_count} من أصل {total_count} فيديو/صوت من قائمة التشغيل.")

    except Exception as e:
        await message.edit_text(f"❌ **حدث خطأ أثناء تحميل القائمة:**\n`{str(e)}`")

async def start_bot_async():
    try:
        await app.start()
        if Admin_Id != 0:
            await app.send_message(Admin_Id, 'Bot is Running ✅')
        print(f"✅ Ytdl Bot is ONLINE!")
        await idle()
    finally:
        if app.is_connected:
            await app.stop()

if __name__ == '__main__':
    asyncio.run(start_bot_async())