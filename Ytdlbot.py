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

user_data = {}

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "👋 **أهلاً بك!** أرسل لي رابط قائمة تشغيل (Playlist)، قناة يوتيوب، أو فيديو فردي وسأتعامل معه فوراً."
    )

@app.on_message(filters.text & (filters.regex("http://") | filters.regex("https://")))
async def get_video_options(client: Client, message: Message):
    url = message.text.strip()
    user_id = message.from_user.id
    
    status_msg = await message.reply_text("⏳ **جاري فحص الروابط واستخراج القائمة...**")

    try:
        def fetch_links():
            # استخراج الروابط بطريقة مسطحة وسريعة ومضمونة عبر yt-dlp دون مشاكل الفيديوهات المحذوفة
            ydl_opts = {
                'extract_flat': True,
                'skip_download': True,
                'ignoreerrors': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return "video", "YouTube Content", [url]
                
                title = info.get('title', 'YouTube Content')
                if 'entries' in info:
                    links = []
                    for entry in info['entries']:
                        if entry:
                            vid_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                            links.append(vid_url)
                    content_type = "playlist" if "playlist" in url or "list=" in url else "channel"
                    return content_type, title, links
                else:
                    return "video", title, [url]

        loop = asyncio.get_running_loop()
        content_type, title, links = await loop.run_in_executor(None, fetch_links)
        
        user_data[user_id] = {
            "type": content_type,
            "links": links,
            "title": title
        }

        if content_type in ["playlist", "channel"]:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📂 تحميل القائمة كاملة (فيديو 480p)", callback_data="pl|480"),
                    InlineKeyboardButton("📂 تحميل القائمة كاملة (فيديو 720p)", callback_data="pl|720")
                ],
                [
                    InlineKeyboardButton("🎵 تحميل القائمة كاملة (صوت MP3)", callback_data="pl|mp3")
                ]
            ])
            await status_msg.edit_text(
                f"📌 **{'قائمة تشغيل' if content_type == 'playlist' else 'قناة'}:** {title}\n📊 **عدد الروابط المستخرجة:** {len(links)}\n\nاختر صيغة التحميل المطلوبة:",
                reply_markup=keyboard
            )
        else:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎬 جودة (720p)", callback_data="dl|720"),
                    InlineKeyboardButton("🎬 جودة (480p)", callback_data="dl|480")
                ],
                [
                    InlineKeyboardButton("🎵 تحويل إلى صوت (MP3)", callback_data="dl|mp3")
                ]
            ])
            await status_msg.edit_text(
                f"📌 **{title}**\n\nاختر صيغة التحميل المطلوبة:",
                reply_markup=keyboard
            )

    except Exception as e:
        await status_msg.edit_text(f"❌ **حدث خطأ أثناء جلب الروابط:**\n`{str(e)}`")

# معالجة تحميل الفيديو الفردي
@app.on_callback_query(filters.regex(r"^dl\|"))
async def handle_single_download(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    action = callback_query.data.split("|")[1]
    
    user_info = user_data.get(user_id)
    if not user_info or not user_info["links"]:
        await callback_query.message.edit_text("❌ **انتهت صلاحية الجلسة، أرسل الرابط مجدداً.**")
        return
    
    url = user_info["links"][0]
    message = callback_query.message
    await message.edit_text("📥 **جاري التحميل والمعالجة... يرجى الانتظار.**")

    os.makedirs("downloads", exist_ok=True)

    try:
        if action == "mp3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            }
        else:
            height = action
            ydl_opts = {
                'format': f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/bestvideo[height<=360][ext=mp4]+bestaudio/best[height<=360]/best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
            }

        def download_single():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info, ydl.prepare_filename(info)

        loop = asyncio.get_running_loop()
        info, file_path = await loop.run_in_executor(None, download_single)
        
        if not os.path.exists(file_path):
            for f in os.listdir("downloads"):
                if info.get('id', '') in f:
                    file_path = os.path.join("downloads", f)
                    break

        await message.edit_text("📤 **جاري الرفع إلى تيليجرام...**")
        if action == "mp3":
            await client.send_audio(chat_id=message.chat.id, audio=file_path, title=info.get('title', 'Media'))
        else:
            await client.send_video(chat_id=message.chat.id, video=file_path, caption=f"🎬 **{info.get('title')}**", supports_streaming=True)

        await message.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await message.edit_text(f"❌ **حدث خطأ أثناء التحميل:**\n`{str(e)}`")
    finally:
        user_data.pop(user_id, None)

# معالجة لوب قوائم التشغيل والقنوات وتخطي المحذوف مع اختيار الجودة الاحتياطية (360p)
@app.on_callback_query(filters.regex(r"^pl\|"))
async def handle_playlist_download(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    action = callback_query.data.split("|")[1] # mp3, 480, 720
    
    user_info = user_data.get(user_id)
    if not user_info:
        await callback_query.message.edit_text("❌ **انتهت صلاحية الجلسة، أرسل الرابط مجدداً.**")
        return

    links = user_info["links"]
    playlist_title = user_info["title"]
    total_count = len(links)

    message = callback_query.message
    await message.edit_text(f"📥 **بدء تحميل القائمة ({playlist_title}) - إجمالي العناصر: {total_count}**")

    os.makedirs("downloads", exist_ok=True)
    sent_count = 0

    for index, link in enumerate(links, start=1):
        try:
            if action == "mp3":
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': 'downloads/%(id)s.%(ext)s',
                    'ignoreerrors': True,
                    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                }
            else:
                height = action
                # اللوب يضمن أنه لو الجودة المطلوبة غير متوفرة سينزل إلى 360p تلقائياً
                ydl_opts = {
                    'format': f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/bestvideo[height<=360][ext=mp4]+bestaudio/best[height<=360]/best',
                    'outtmpl': 'downloads/%(id)s.%(ext)s',
                    'ignoreerrors': True,
                }

            def download_item():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=True)
                    if not info:
                        return None, None
                    return info, ydl.prepare_filename(info)

            loop = asyncio.get_running_loop()
            info, file_path = await loop.run_in_executor(None, download_item)
            
            if not info or not file_path or not os.path.exists(file_path):
                found = False
                for f in os.listdir("downloads"):
                    if info and info.get('id', '') in f:
                        file_path = os.path.join("downloads", f)
                        found = True
                        break
                if not found:
                    continue

            vid_title = info.get('title', 'video')
            caption_text = f"🎬 **{vid_title}**\n\n📌 **فيديو ({index} من أصل {total_count})**"
            audio_title = f"{vid_title} ({index}/{total_count})"

            if action == "mp3":
                await client.send_audio(
                    chat_id=message.chat.id,
                    audio=file_path,
                    title=audio_title,
                    performer=playlist_title
                )
            else:
                await client.send_video(
                    chat_id=message.chat.id,
                    video=file_path,
                    caption=caption_text,
                    supports_streaming=True
                )
            
            sent_count += 1
            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception as item_err:
            print(f"Skipped item {index} due to error: {item_err}")
            continue

    await message.edit_text(f"✅ **تم الانتهاء من تحميل القائمة!** تم إرسال {sent_count} من أصل {total_count} بنجاح.")
    user_data.pop(user_id, None)

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