import nest_asyncio, os, json, textwrap, asyncio, gc, time, random
nest_asyncio.apply()

#########################################################

Bot_Token = os.getenv('TOKEN')
Admin_Id = int(os.getenv('Admin_Id','0'))

########################################################

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply, Message
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageTooLong
from pyrogram import idle

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import torch
import whisperx
from google import genai

GEMINI_MODEL_NAME = 'gemini-2.5-flash-lite'

gemini_keys_env = os.getenv('GEMINI_API_KEYS') or os.getenv('GEMINI_API_KEY') or ''
raw_gemini_keys = [k.strip() for k in gemini_keys_env.split(' ') if k.strip()]

VALID_GEMINI_KEYS = raw_gemini_keys
current_key_index = 0

Global_Main_Queue = []
Public_Loop = False

def test_single_key(key):
    try:
        client = genai.Client(api_key=key)
        client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents="Test",
        )
        return True, None
    except Exception as e:
        return False, str(e).splitlines()[0]

async def validate_and_filter_keys_async():
    global VALID_GEMINI_KEYS
    if not raw_gemini_keys:
        print("⚠️ تحذير: لم يتم العثور على أي توكن لجمناي في متغيرات البيئة.")
        return

    print(f"🔍 جاري فحص واختبار {len(raw_gemini_keys)} توكن لـ Gemini...")
    for index, key in enumerate(raw_gemini_keys):
        try:
            is_valid, err = await asyncio.wait_for(
                asyncio.to_thread(test_single_key, key),
                timeout=4.0
            )
            if is_valid:
                VALID_GEMINI_KEYS.append(key)
                print(f"  [✅ صالح] التوكن رقم {index + 1}")
            else:
                print(f"  [❌ تالف] التوكن رقم {index + 1} - السبب: {err}")
        except asyncio.TimeoutError:
            print(f"  [⏳ انتهت المهلة] التوكن رقم {index + 1} لم يستجب وتم استبعاده.")
        except Exception as e:
            print(f"  [❌ خطأ] التوكن رقم {index + 1} - {e}")
            
    print(f"✨ إجمالي التوكنات الصالحة للعمل: {len(VALID_GEMINI_KEYS)} من {len(raw_gemini_keys)}")

def get_next_valid_client():
    global current_key_index
    if not VALID_GEMINI_KEYS:
        raise ValueError("❌ لا توجد أي توكنات صالحة لجمناي للعمل بها!")
    
    key = VALID_GEMINI_KEYS[current_key_index % len(VALID_GEMINI_KEYS)]
    current_key_index += 1
    return genai.Client(api_key=key)

Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'
Audio_Forms = (".mp3", ".ogg", ".m4a", ".aac", ".flac", ".wav", ".wma", ".opus", ".3gpp")
Video_Forms = (".mp4", ".mkv", ".mov", ".avi", ".wmv", ".avchd", ".webm", ".flv")

async def run_command(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode(), stderr.decode()

async def Mp3_Conv(File):
    mainDir = '/'.join(File.split('/')[:-1]) + '/'
    Mp3_File = mainDir + File.split('/')[-1].split('.')[0] + '_Conv.mp3'
    Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
    await run_command(Mp3_Cmd)
    return Mp3_File

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(int((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

async def get_video_duration(video_file):
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
        stdout, _ = await run_command(cmd)
        return float(stdout.strip())
    except Exception as e:
        print(f"Error getting video duration: {e}")
        return 0.0

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

async def split_video_into_hour_chunks(video_file, task_dl_path):
    duration = await get_video_duration(video_file)
    if duration <= 3600:
        return [video_file]

    chunk_duration = 3600
    chunks = []
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    
    start_time = 0
    part_idx = 1
    while start_time < duration:
        chunk_output = os.path.join(task_dl_path, f"{base_name}_part{part_idx}.mp4")
        cmd = f'ffmpeg -ss {start_time} -i "{video_file}" -t {chunk_duration} -c copy "{chunk_output}" -y'
        await run_command(cmd)
        if os.path.exists(chunk_output) and os.path.getsize(chunk_output) > 0:
            chunks.append(chunk_output)
        start_time += chunk_duration
        part_idx += 1
        
    return chunks

def run_whisperx_pipeline(audio_file):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "int8" if device == "cuda" else "float32"
    
    model = whisperx.load_model("large-v3", device, compute_type=compute_type)
    audio = whisperx.load_audio(audio_file)
    result = model.transcribe(audio, batch_size=16)
    
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
    
    return result

async def whisperx_extract_srt_chunk(media_file, time_offset=0.0, subtitle_index_offset=0):
    """استخراج الترجمة الإنجليزية فقط دون ترجمة لكل جزء"""
    audio_file = await Mp3_Conv(media_file)
    result = await asyncio.to_thread(run_whisperx_pipeline, audio_file)
    
    srt_content = ""
    seg_counter = 1 + subtitle_index_offset
    for segment in result["segments"]:
        start_sec = segment.get("start", 0.0) + time_offset
        end_sec = segment.get("end", 0.0) + time_offset
        
        start_str = format_time(start_sec)
        end_str = format_time(end_sec)
        text_en = segment.get("text", "").strip()
        
        if text_en:
            srt_content += f"{seg_counter}\n{start_str} --> {end_str}\n{text_en}\n\n"
            seg_counter += 1
        
    if os.path.exists(audio_file):
        os.remove(audio_file)
        
    return srt_content, seg_counter - subtitle_index_offset

async def translate_full_srt_with_gemini(srt_file_path):
    """ترجمة ملف الترجمة الشامل دفعة واحدة عبر Gemini"""
    if not VALID_GEMINI_KEYS:
        raise ValueError("❌ لا توجد أي توكنات صالحة لجمناي متروكة بعد الفحص!")

    with open(srt_file_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()

    prompt = (
        "You are a professional subtitle translator. Translate the following full SRT subtitle content from English to Arabic. "
        "Strictly adhere to these rules:\n"
        "1. Keep the exact SRT format, subtitle index numbers, and timecodes (e.g., 00:00:01,000 --> 00:00:04,000) completely unchanged.\n"
        "2. Translate ONLY the English text spoken in the subtitles into natural, accurate, and fluent Arabic suitable for video subtitles.\n"
        "3. Do not add any extra explanations, notes, or markdown formatting outside the SRT structure. Return only the valid translated SRT content.\n\n"
        f"{srt_content}"
    )

    translated_text = None
    max_attempts = len(VALID_GEMINI_KEYS)

    for attempt in range(max_attempts):
        try:
            client = get_next_valid_client()
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=GEMINI_MODEL_NAME,
                contents=prompt,
            )
            
            if response and response.text:
                translated_text = response.text.strip()
                if translated_text.startswith("```"):
                    lines = translated_text.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    translated_text = "\n".join(lines).strip()
                break 
        except Exception as e:
            print(f"⚠️ خطأ أثناء الترجمة بمحاولة {attempt + 1}: {e}")
            continue

    if not translated_text:
        raise Exception("فشلت عملية الترجمة باستخدام التوكنات الصالحة.")

    translated_srt_path = srt_file_path.replace('_EN.srt', '_AR.srt')
    with open(translated_srt_path, 'w', encoding='utf-8') as f:
        f.write(translated_text)

    return translated_srt_path

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

def Pyrogram_Client(Bot_Token):
    Bot_Identifier = Bot_Token.split(':')[0]
    Session_file = Bot_Identifier + '_955hyh95|session_prm_bot'
    bot = Client(Session_file, api_id=Api_Id, api_hash=Api_Hash, bot_token=Bot_Token, in_memory=True)
    return bot, Bot_Identifier

bot, Bot_Identifier = Pyrogram_Client(Bot_Token)
dl_path = f'./downloads_{Bot_Identifier}/'

# ==================== نظام الـ Global List Loop ==================== #

def Item_add(Item):
    global Global_Main_Queue, Public_Loop
    Global_Main_Queue.append(Item)
    if not Public_Loop:
        Public_Loop = True
        asyncio.create_task(Multi_loop_async())

async def Multi_loop_async():
    global Global_Main_Queue, Public_Loop
    Public_Loop = True

    while len(Global_Main_Queue) > 0:
        for elem in range(1, len(Global_Main_Queue)):
            try:
                A_Reply_List = Global_Main_Queue[elem].split('_')
                A_rp_msg_id = int(A_Reply_List[-2])
                A_user_id = int(A_Reply_List[-1])
                A_reply = await bot.get_messages(A_user_id, A_rp_msg_id)
                await A_reply.edit_text(f"تمت الإضافة للصف \n\n ترتيبك هو {elem} ☕ ")
            except Exception:
                pass

        C_Process = Global_Main_Queue[0]
        msg_list = C_Process.split('_')
        msg_id = int(msg_list[1])
        rp_msg_id = int(msg_list[-2])
        user_id = int(msg_list[-1])

        reply_msg = await bot.get_messages(user_id, rp_msg_id)
        File_Msg = await bot.get_messages(user_id, msg_id)

        try:
            try:
                await reply_msg.edit_text("جارِ العمل على الملف الآن ☕...")
            except Exception:
                reply_msg = await File_Msg.reply("جارِ العمل ☕", reply_to_message_id=File_Msg.id)

            task_dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
            if not os.path.exists(task_dl_path):
                os.makedirs(task_dl_path)

            # 1. تنزيل الفيديو الأصلي الكامل
            file = await File_Msg.download(file_name=task_dl_path)

            # 2. تقسيم الفيديو مؤقتاً لأجزاء (لكفاءة WhisperX)
            await reply_msg.edit_text('جارِ فحص مدة الفيديو وتقسيمه مؤقتاً (إذا تجاوز 60 دقيقة)...')
            chunks = await split_video_into_hour_chunks(file, task_dl_path)
            
            total_chunks = len(chunks)
            combined_en_srt = ""
            
            time_offset = 0.0
            subtitle_index_offset = 0

            # 3. استخراج الترجمة الإنجليزية من كل جزء ودمجها في ملف شامل
            for idx, chunk_path in enumerate(chunks, start=1):
                await reply_msg.edit_text(f'جارِ استخراج النصوص من الجزء ({idx}/{total_chunks}) عبر WhisperX...')
                
                chunk_duration = await get_video_duration(chunk_path)
                
                chunk_srt_content, count_added = await whisperx_extract_srt_chunk(
                    chunk_path, 
                    time_offset=time_offset, 
                    subtitle_index_offset=subtitle_index_offset
                )
                
                combined_en_srt += chunk_srt_content + "\n"
                
                time_offset += chunk_duration
                subtitle_index_offset += (count_added - 1)

            # حفظ ملف الترجمة الإنجليزي الشامل مؤقتاً
            final_en_srt_path = os.path.join(task_dl_path, "Full_Subtitles_EN.srt")
            with open(final_en_srt_path, 'w', encoding='utf-8') as f:
                f.write(combined_en_srt)

            # 4. ترجمة ملف الترجمة الشامل عبر Gemini دفعة واحدة
            await reply_msg.edit_text('جارِ ترجمة ملف الترجمة الشامل عبر Gemini (بصياغة سياقية متكاملة)...')
            final_ar_srt_path = await translate_full_srt_with_gemini(final_en_srt_path)

            # إرسال ملف الترجمة العربي الشامل للمستخدم
            await File_Msg.reply_document(
                final_ar_srt_path, 
                caption="📄 ملف الترجمة العربي الشامل للملف بالكامل (SRT) ✅"
            )

            # 5. حرق الترجمة العربية الشاملة على الفيديو الأصلي الكامل
            await reply_msg.edit_text('جارِ دمج وحرق الترجمة العربية على الفيديو الأصلي الكامل...')
            final_merged_video = await burn_subtitles_ffmpeg(file, final_ar_srt_path)

            # 6. إرسال الفيديو النهائي للمستخدم
            await reply_msg.edit_text('جارِ رفع الفيديو المترجم النهائي...')
            await File_Msg.reply_video(final_merged_video, caption="الفيديو المترجم بالعربية بالكامل جاهز ✅")

            # التنظيف النهائي للملفات المؤقتة
            for ch in chunks:
                if ch != file and os.path.exists(ch): 
                    os.remove(ch)
            if os.path.exists(final_merged_video):
                os.remove(final_merged_video)
            if os.path.exists(final_en_srt_path):
                os.remove(final_en_srt_path)
            if os.path.exists(final_ar_srt_path):
                os.remove(final_ar_srt_path)
            if os.path.exists(file):
                os.remove(file)

            await reply_msg.edit_text('تمت العملية بنجاح ☑️')

        except Exception as err:
            err_text = str(err)[:3000]
            try:
                await reply_msg.edit_text(f"حدث خطأ أثناء المعالجة:\n`{err_text}`")
            except Exception:
                pass

        Global_Main_Queue.pop(0)

    gc.collect()
    Public_Loop = False

# ==================================================================== #

@bot.on_message(filters.command('start') & filters.private)
async def command1(bot, message):
    await message.reply('لبقية البوتات \n\n @sunnaybots')
  
@bot.on_message(filters.private & filters.incoming & (filters.audio | filters.voice | filters.video))
async def _telegram_file(client, message):
    global Global_Main_Queue
    replied = await message.reply(f"تمت الإضافة لصف الانتظار ☕\nترتيبك في القائمة: {len(Global_Main_Queue) + 1}")
    
    Item = f"VidSub_{message.id}_{replied.id}_{message.from_user.id}"
    Item_add(Item)

async def start_bot_async():
    if not os.path.exists(dl_path): 
        os.makedirs(dl_path)
    try:
        await bot.start()
        if Admin_Id != 0:
            await bot.send_message(Admin_Id, 'Vidsub Bot Started with Global List Loop ✅')
        print(f"✅ WhisperX + Gemini Async Subtitles Bot (Global List Loop) is ONLINE!")
        await idle()
    finally:
        if bot.is_connected:
            await bot.stop()

if __name__ == '__main__':
    asyncio.run(start_bot_async())