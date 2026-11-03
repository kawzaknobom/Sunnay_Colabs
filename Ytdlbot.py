import nest_asyncio, os
nest_asyncio.apply()

#########################################################

BOT_TOKEN = os.getenv('TOKEN')
Admin_Id = int(os.getenv('Admin_Id','0'))
Playlist_Num = int(os.getenv('Playlist_Num','0'))
API_ID = 15952578
API_HASH = '3600ce5f8f9b9e18cba0f318fa0e3600'

########################################################

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp
from pyrogram import idle

# --- CONFIGURATION ---

bot = Client(
    "youtube_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "👋 **أهلاً بك!** أرسل لي رابط فيديو فردي، قائمة تشغيل (Playlist)، أو قناة يوتيوب، وسأقوم بالتعامل معها وتحميلها لك[cite: 1]."
    )

@bot.on_message(filters.text & (filters.regex("http://") | filters.regex("https://")))
async def get_video_options(client: Client, message: Message):
    url = message.text.strip()
    
    status_msg = await message.reply_text("⏳ **جاري فحص الرابط وجلب المعلومات...**[cite: 1]")

    try:
        def fetch_info():
            # استخراج المعلومات مع السماح برصد قوائم التشغيل أو القنوات
            ydl_opts = {'extract_flat': 'in_playlist', 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, fetch_info)
        
        # التحقق مما إذا كان الرابط يمثل قائمة تشغيل أو قناة تحتوي على عدة عناصر
        if 'entries' in info:
            entries = list(info['entries'])
            total_items = len(entries)
            playlist_title = info.get('title', 'Playlist / Channel')
            
            if total_items == 0:
                await status_msg.edit_text("❌ **عذراً:** لم يتم العثور على أي فيديوهات في هذا الرابط.")
                return

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎬 تحميل كفيديوهات (720p)", callback_data=f"dl_pl|720|{url}"),
                    InlineKeyboardButton("🎬 تحميل كفيديوهات (480p)", callback_data=f"dl_pl|480|{url}")
                ],
                [
                    InlineKeyboardButton("🎵 تحويل الكل إلى صوت (MP3)", callback_data=f"dl_pl|mp3|{url}")
                ]
            ])

            await status_msg.edit_text(
                f"📁 **{playlist_title}**\n"
                f"📊 **عدد العناصر المكتشفة:** {total_items} فيديو\n\n"
                f"اختر صيغة التحميل للقائمة/القناة:",
                reply_markup=keyboard
            )
        else:
            # فيديو فردي عادي
            title = info.get('title', 'YouTube Video')
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

# معالجة الضغط على أزرار الفيديوهات الفردية
@bot.on_callback_query(filters.regex(r"^dl\|"))
async def handle_download_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")
    quality = data[1]
    video_id = data[2]
    url = f"https://youtu.be/{video_id}"
    
    message = callback_query.message
    await message.edit_text("📥 **جاري التحميل والمعالجة... يرجى الانتظار.**[cite: 1]")

    os.makedirs("downloads", exist_ok=True)
    
    file_path = None
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
                if quality == "mp3":
                    fp = os.path.join("downloads", f"{video_id}.mp3")
                else:
                    fp = ydl.prepare_filename(info)
                return info, fp

        loop = asyncio.get_running_loop()
        info, file_path = await loop.run_in_executor(None, download_media)
        
        title = info.get('title', 'Media')
        
        if not os.path.exists(file_path):
            for f in os.listdir("downloads"):
                if f.startswith(video_id):
                    file_path = os.path.join("downloads", f)
                    break

        if not os.path.exists(file_path):
            await message.edit_text("❌ **فشل التحميل:** لم يتم العثور على الملف الناتج.")
            return

        await message.edit_text("📤 **جاري الرفع إلى تيليجرام...**[cite: 1]")

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
                caption=f"🎬 **{title}**\n\n📌 الفيديو رقم 1 من أصل 1",
                duration=info.get('duration', 0),
                supports_streaming=True
            )

        await message.delete()
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await message.edit_text(f"❌ **حدث خطأ أثناء التحميل:**\n`{str(e)}`")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

# معالجة الضغط على أزرار قوائم التشغيل أو القنوات
@bot.on_callback_query(filters.regex(r"^dl_pl\|"))
async def handle_playlist_download_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split("|")
    quality = data[1]
    url = data[2] # استرجاع الرابط كاملاً
    
    message = callback_query.message
    await message.edit_text("📥 **جاري بدء تحميل القائمة/القناة بالكامل... قد يستغرق ذلك وقتاً حسب عدد الفيديوهات.**")

    os.makedirs("downloads", exist_ok=True)

    try:
        # جلب قائمة الفيديوهات كاملة بدون تحميل مسبق لمعرفة العدد الكلي
        def fetch_playlist_info():
            ydl_opts = {'extract_flat': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        loop = asyncio.get_running_loop()
        pl_info = await loop.run_in_executor(None, fetch_playlist_info)
        entries = list(pl_info.get('entries', []))
        total_videos = len(entries)

        if total_videos == 0:
            await message.edit_text("❌ **عذراً:** القائمة فارغة ولا تحتوي على فيديوهات.")
            return

        current_index = 0
        for entry in entries[Playlist_Num:]:
            current_index += 1
            v_id = entry.get('id')
            v_url = f"https://youtu.be/{v_id}"
            
            status_text = f"📥 **جاري تحميل الفيديو ({current_index} من أصل {total_videos})...**\n📌 العنوان: {entry.get('title', 'Unknown')}"
            try:
                await message.edit_text(status_text)
            except Exception:
                pass

            file_path = None
            try:
                if quality == "mp3":
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': f'downloads/%(id)s.%(ext)s',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    }
                else:
                    ydl_opts = {
                        'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best',
                        'outtmpl': f'downloads/%(id)s.%(ext)s',
                    }

                def download_single_in_pl():
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        v_info = ydl.extract_info(v_url, download=True)
                        if quality == "mp3":
                            fp = os.path.join("downloads", f"{v_id}.mp3")
                        else:
                            fp = ydl.prepare_filename(v_info)
                        return v_info, fp

                v_info, file_path = await loop.run_in_executor(None, download_single_in_pl)
                v_title = v_info.get('title', 'Media')

                if not file_path or not os.path.exists(file_path):
                    for f in os.listdir("downloads"):
                        if f.startswith(v_id):
                            file_path = os.path.join("downloads", f)
                            break

                if file_path and os.path.exists(file_path):
                    if quality == "mp3":
                        await client.send_audio(
                            chat_id=message.chat.id,
                            audio=file_path,
                            title=v_title,
                            performer=v_info.get('uploader', 'YouTube'),
                            caption=f"🎵 الفيديو رقم {current_index} من أصل {total_videos}"
                        )
                    else:
                        await client.send_video(
                            chat_id=message.chat.id,
                            video=file_path,
                            caption=f"🎬 **{v_title}**\n\n📌 الفيديو رقم {current_index} من أصل {total_videos}",
                            duration=v_info.get('duration', 0),
                            supports_streaming=True
                        )
                    
                    os.remove(file_path)

            except Exception as single_err:
                print(f"Error downloading video {v_id}: {single_err}")
                continue # تخطي الفيديو المعطوب والمتابعة لبقية القائمة

        await message.edit_text(f"✅ **تم الانتهاء من تحميل وتنزيل جميع الفيديوهات بنجاح!** (الإجمالي: {total_videos} فيديو)")

    except Exception as e:
        await message.edit_text(f"❌ **حدث خطأ أثناء تحميل القائمة:**\n`{str(e)}`")

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