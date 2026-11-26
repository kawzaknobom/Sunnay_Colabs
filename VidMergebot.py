import nest_asyncio, os, json, asyncio
nest_asyncio.apply()

#########################################################
Bot_Token = os.getenv('TOKEN')  # ضع توكن البوت هنا أو في متغيرات البيئة
Admin_Id = int(os.getenv('Admin_Id', '0'))
TARGET_MODE = "first"  # "first" لأبعاد أول فيديو، أو "max" لأكبر أبعاد بين الفيديوهات
TARGET_FPS = 30
#########################################################

from pyrogram import Client, filters, idle
from pyrogram.types import Message

# بيانات الاتصال الخاصة بتطبيقك على Telegram
Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'

bot = Client("MergeVideosBot", api_id=Api_Id, api_hash=Api_Hash, bot_token=Bot_Token)

# قاموس مؤقت لحفظ قائمة رسائل الفيديو لكل مستخدم حتى أمر الدمج
user_states = {}


async def run_command(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode(), stderr.decode()


async def probe_video(video_file):
    """إرجاع (width, height, has_audio) لأي ملف فيديو."""
    width, height = 1920, 1080
    has_audio = False
    try:
        cmd = f'ffprobe -v error -show_streams -of json "{video_file}"'
        stdout, _ = await run_command(cmd)
        data = json.loads(stdout)
        streams = data.get("streams", [])

        v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        if v_stream:
            width = int(v_stream.get("width", width))
            height = int(v_stream.get("height", height))

        has_audio = any(s.get("codec_type") == "audio" for s in streams)
    except Exception as e:
        print(f"Error probing video {video_file}: {e}")

    # ضمان أن الأبعاد زوجية لتوافق ترميز H.264/yuv420p
    width = width if width % 2 == 0 else width + 1
    height = height if height % 2 == 0 else height + 1
    return width, height, has_audio


def choose_target_dimensions(probe_list, mode="first"):
    if not probe_list:
        return 1920, 1080
    if mode == "max":
        w = max(p[0] for p in probe_list)
        h = max(p[1] for p in probe_list)
    else:
        w, h = probe_list[0][0], probe_list[0][1]
    w = w if w % 2 == 0 else w + 1
    h = h if h % 2 == 0 else h + 1
    return w, h


async def merge_videos_ffmpeg(video_files, output_video):
    """دمج عدة فيديوهات ذات دقات/أبعاد مختلفة في ملف واحد عبر filter_complex."""
    probes = [await probe_video(v) for v in video_files]
    target_w, target_h = choose_target_dimensions(probes, TARGET_MODE)

    inputs_cmd = " ".join(f'-i "{v}"' for v in video_files)
    filter_parts = []
    concat_inputs = []

    for idx, (_, _, has_audio) in enumerate(probes):
        v_label = f"v{idx}"
        a_label = f"a{idx}"

        # توحيد الأبعاد مع الحفاظ على النسبة وإضافة حواف سوداء عند اختلاف الـ aspect ratio
        filter_parts.append(
            f"[{idx}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,fps={TARGET_FPS},format=yuv420p[{v_label}]"
        )

        # توحيد المسار الصوتي أو توليد صمت إذا كان الفيديو بدون صوت
        if has_audio:
            filter_parts.append(
                f"[{idx}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[{a_label}]"
            )
        else:
            filter_parts.append(
                f"anullsrc=channel_layout=stereo:sample_rate=44100[{a_label}_raw];"
                f"[{a_label}_raw]aresample=44100[{a_label}]"
            )

        concat_inputs.append(f"[{v_label}][{a_label}]")

    n = len(video_files)
    filter_parts.append(f"{''.join(concat_inputs)}concat=n={n}:v=1:a=1[outv][outa]")
    filter_complex = ";".join(filter_parts)

    ffmpeg_cmd = (
        f'ffmpeg {inputs_cmd} -filter_complex "{filter_complex}" '
        f'-map "[outv]" -map "[outa]" '
        f'-c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k '
        f'"{output_video}" -y'
    )

    _, stderr = await run_command(ffmpeg_cmd)
    if not os.path.exists(output_video) or os.path.getsize(output_video) == 0:
        raise RuntimeError(f"فشل FFmpeg في إنتاج الفيديو المدمج:\n{stderr[-1500:]}")

    return output_video


def is_video_message(message: Message) -> bool:
    return bool(
        message.video or
        (message.document and message.document.mime_type and "video" in message.document.mime_type)
    )


@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    await message.reply(
        "مرحباً بك في بوت دمج الفيديوهات متعددة الأبعاد! 🎬\n\n"
        "الخطوات:\n"
        "1. أرسل الفيديوهات التي تريد دمجها واحداً تلو الآخر بالترتيب المطلوب (يتم حفظ مراجعها بدون تحميل مسبق).\n"
        "2. أرسل الأمر /merge لبدء التحميل وتوحيد الأبعاد ودمج الفيديوهات في مقطع واحد.\n"
        "3. استخدم /clear لإلغاء القائمة الحالية."
    )


@bot.on_message(filters.command("clear") & filters.private)
async def clear_handler(client, message: Message):
    user_id = message.from_user.id
    if user_id in user_states:
        del user_states[user_id]
        await message.reply("🗑️ تم مسح قائمة الفيديوهات المؤقتة.")
    else:
        await message.reply("لا توجد قائمة فيديوهات نشطة حالياً.")


@bot.on_message(filters.command("merge") & filters.private)
async def merge_handler(client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if not state or len(state.get("video_messages", [])) < 2:
        await message.reply("⚠️ الرجاء إرسال فيديوَين على الأقل أولاً قبل استخدام الأمر /merge.")
        return

    video_messages = state["video_messages"]
    download_dir = f"./downloads_{user_id}/"
    os.makedirs(download_dir, exist_ok=True)
    downloaded_files = []
    final_video = os.path.join(download_dir, "merged_output.mp4")

    status_msg = await message.reply(f"📥 جاري تحميل {len(video_messages)} فيديو...")

    try:
        for idx, v_msg in enumerate(video_messages, start=1):
            await status_msg.edit_text(f"📥 جاري تحميل الفيديو ({idx}/{len(video_messages)})...")
            ext = ".mp4"
            if v_msg.document and v_msg.document.file_name and "." in v_msg.document.file_name:
                ext = "." + v_msg.document.file_name.rsplit(".", 1)[-1]
            v_path = await v_msg.download(file_name=os.path.join(download_dir, f"vid_{idx}{ext}"))
            downloaded_files.append(v_path)

        await status_msg.edit_text("⏳ جاري توحيد الأبعاد ودمج الفيديوهات عبر FFmpeg (قد يستغرق ذلك بعض الوقت)...")
        await merge_videos_ffmpeg(downloaded_files, final_video)

        await status_msg.edit_text("📤 جاري رفع الفيديو المدمج...")
        await message.reply_video(final_video, caption=f"تم دمج {len(downloaded_files)} فيديوهات بنجاح ✅")

    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ أثناء عملية الدمج:\n`{str(e)[:3000]}`")

    finally:
        for f_path in downloaded_files + [final_video]:
            if f_path and os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except OSError:
                    pass
        if user_id in user_states:
            del user_states[user_id]
        try:
            await status_msg.delete()
        except Exception:
            pass


@bot.on_message(filters.private & (filters.video | filters.document))
async def receive_videos(client, message: Message):
    if not is_video_message(message):
        return

    user_id = message.from_user.id
    if user_id not in user_states:
        user_states[user_id] = {"video_messages": []}

    user_states[user_id]["video_messages"].append(message)
    count = len(user_states[user_id]["video_messages"])

    await message.reply(
        f"📌 تم حفظ الفيديو رقم **#{count}** في القائمة (بدون تحميل).\n"
        f"أرسل المزيد أو أرسل /merge للدمج الآن."
    )


async def start_bot_async():
    try:
        await bot.start()
        if Admin_Id != 0:
            await bot.send_message(Admin_Id, 'Video Merge Bot is Running ✅')
        print("✅ Video Merge Bot is ONLINE!")
        await idle()
    finally:
        if bot.is_connected:
            await bot.stop()


if __name__ == '__main__':
    asyncio.run(start_bot_async())