import nest_asyncio
nest_asyncio.apply()
import os

#########################################################

BOT_TOKEN = os.getenv('TOKEN')

########################################################

import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
import librosa
import soundfile as sf

# إعدادات البوت
API_ID = 15952578          # ضع الـ API ID هنا
API_HASH = "3600ce5f8f9b9e18cba0f318fa0e3600"  # ضع الـ API Hash هنا

app = Client("VoiceChangerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# دالة معالجة الصوت
def process_audio_file(input_audio_path, output_audio_path):
    try:
        y, sr = librosa.load(input_audio_path, sr=None)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_mean = librosa.core.np.mean(pitches[pitches > 0]) if len(pitches[pitches > 0]) > 0 else 200
        
        # إذا كان الصوت يميل ليكون نسائياً
        is_female_dominant = pitch_mean > 165
        
        if is_female_dominant:
            # تعديل طبقة الصوت للخفض
            y_modified = librosa.effects.pitch_shift(y, sr=sr, n_steps=-3.5)
            sf.write(output_audio_path, y_modified, sr)
        else:
            sf.write(output_audio_path, y, sr)
        return True
    except Exception as e:
        print(f"خطأ في معالجة الصوت: {e}")
        return False

# دالة معالجة الفيديو باستخدام FFmpeg مباشرة
def process_video_with_ffmpeg(input_video_path, output_video_path):
    temp_audio = f"temp_audio_{os.getpid()}.wav"
    processed_audio = f"processed_audio_{os.getpid()}.wav"
    
    try:
        # 1. استخراج الصوت من الفيديو باستخدام ffmpeg
        extract_cmd = [
            "ffmpeg", "-y", "-i", input_video_path, 
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", temp_audio
        ]
        subprocess.run(extract_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 2. معالجة الصوت المستخرج (تمييز وتعديل الإناث)
        success = process_audio_file(temp_audio, processed_audio)
        if not success:
            return False
            
        # 3. دمج الفيديو الأصلي مع الصوت الجديد وإزالة الصوت القديم باستخدام ffmpeg
        merge_cmd = [
            "ffmpeg", "-y", 
            "-i", input_video_path,     # الفيديو الأصلي
            "-i", processed_audio,      # الصوت الجديد المعدل
            "-c:v", "copy",             # نسخ الفيديو بدون إعادة ترميز (أسرع بكثير!)
            "-c:a", "aac",              # ترميز الصوت الجديد بصيغة aac
            "-map", "0:v:0",            # استخدام الفيديو من الملف الأول
            "-map", "1:a:0",            # استخدام الصوت من الملف الثاني
            output_video_path
        ]
        subprocess.run(merge_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return True
    except Exception as e:
        print(f"خطأ في معالجة الفيديو عبر FFmpeg: {e}")
        return False
    finally:
        # تنظيف الملفات الصوتية المؤقتة
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        if os.path.exists(processed_audio):
            os.remove(processed_audio)

# استقبال أمر البدء
@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text(
        "أهلاً بك! 🎬🎙️\n\n"
        "أرسل **صوتاً** أو **فيديو** وسأقوم بمعالجته عبر FFmpeg فوراً."
    )

# استقبال الملفات (صوت أو فيديو أو مستندات)
@app.on_message(filters.audio | filters.voice | filters.video | filters.document)
async def handle_media(client, message: Message):
    media = message.audio or message.voice or message.video or message.document
    if not media:
        return

    is_video = bool(message.video or (message.document and message.document.mime_type and "video" in message.document.mime_type))
    
    processing_msg = await message.reply_text("⏳ جاري المعالجة السريعة عبر FFmpeg...")

    input_file = await message.download()
    output_file = f"processed_{message.chat.id}.mp4" if is_video else f"processed_{message.chat.id}.wav"

    try:
        loop = asyncio.get_running_loop()
        
        if is_video:
            success = await loop.run_in_executor(None, process_video_with_ffmpeg, input_file, output_file)
            if success and os.path.exists(output_file):
                await message.reply_video(video=output_file, caption="✅ تم تعديل الفيديو ودمج الصوت بنجاح عبر FFmpeg!")
            else:
                await message.reply_text("❌ حدث خطأ أثناء معالجة الفيديو.")
        else:
            success = await loop.run_in_executor(None, process_audio_file, input_file, output_file)
            if success and os.path.exists(output_file):
                await message.reply_audio(audio=output_file, caption="✅ تم تعديل الملف الصوتي بنجاح!")
            else:
                await message.reply_text("❌ حدث خطأ أثناء معالجة الصوت.")

    except Exception as e:
        await message.reply_text(f"❌ حدث خطأ غير متوقع: {str(e)}")

    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)
        await processing_msg.delete()

if __name__ == "__main__":
    print("البوت يعمل بـ FFmpeg بكفاءة عالية...")
    app.run()