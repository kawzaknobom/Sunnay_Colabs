import nest_asyncio
nest_asyncio.apply()
import os

#########################################################

BOT_TOKEN = os.getenv('TOKEN')

########################################################
import os
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
import librosa
import soundfile as sf
import numpy as np

# إعدادات البوت
API_ID = 15952578
API_HASH = '3600ce5f8f9b9e18cba0f318fa0e3600'

app = Client("VoiceChangerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def process_audio_smart_chunks(input_audio_path, output_audio_path):
    try:
        # 1. تحميل الملف الصوتي
        y, sr = librosa.load(input_audio_path, sr=None)
        
        # تقسيم الصوت إلى شرائح زمنية قصيرة (كل 1.5 ثانية) لضمان فصل المتحدثين المختلفين
        chunk_duration = 1.5 
        chunk_samples = int(chunk_duration * sr)
        processed_chunks = []
        
        for i in range(0, len(y), chunk_samples):
            chunk = y[i:i + chunk_samples]
            if len(chunk) < sr * 0.1:  # إهمال الأجزاء القصيرة جداً في النهاية
                processed_chunks.append(chunk)
                continue
                
            # حساب طبقة الصوت (Pitch) لهذه الشريحة فقط
            pitches, magnitudes = librosa.piptrack(y=chunk, sr=sr)
            valid_pitches = pitches[pitches > 0]
            
            chunk_pitch_mean = np.mean(valid_pitches) if len(valid_pitches) > 0 else 0
            
            # نطاق ترددات الأصوات النسائية البشرية الطبيعية
            is_female_voice = 165 < chunk_pitch_mean < 350
            
            if is_female_voice:
                # خفض طبقة الصوت للمقطع النسائي فقط لجعله يبدو أخشونة أو أقرب لصوت ذكر
                modified_chunk = librosa.effects.pitch_shift(chunk, sr=sr, n_steps=-4.0)
                processed_chunks.append(modified_chunk)
            else:
                # ترك أصوات الذكور أو الأصوات الأخرى كما هي بدون تعديل
                processed_chunks.append(chunk)
                
        # دمج جميع الشرائح معاً
        y_final = np.concatenate(processed_chunks)
        sf.write(output_audio_path, y_final, sr)
        return True
        
    except Exception as e:
        print(f"خطأ في معالجة الصوت: {e}")
        return False

def process_video_file(input_video_path, output_video_path):
    pid = os.getpid()
    temp_audio = f"temp_audio_{pid}.wav"
    processed_audio = f"processed_audio_{pid}.wav"
    
    try:
        # استخراج الصوت من الفيديو عبر FFmpeg
        extract_cmd = [
            "ffmpeg", "-y", "-i", input_video_path, 
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", temp_audio
        ]
        subprocess.run(extract_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # معالجة الصوت بالتحليل الذكي للشرائح
        success = process_audio_smart_chunks(temp_audio, processed_audio)
        if not success or not os.path.exists(processed_audio):
            return False
            
        # دمج الفيديو الأصلي مع الصوت الجديد المعدل بدون إعادة ضغط الفيديو (سريع جداً)
        merge_cmd = [
            "ffmpeg", "-y", 
            "-i", input_video_path,     
            "-i", processed_audio,      
            "-c:v", "copy",             
            "-c:a", "aac",              
            "-b:a", "192k",             
            "-map", "0:v:0",            
            "-map", "1:a:0",            
            "-shortest",                
            output_video_path
        ]
        subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
        
    except Exception as e:
        print(f"خطأ في معالجة الفيديو: {e}")
        return False
    finally:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        if os.path.exists(processed_audio):
            os.remove(processed_audio)

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text("🤖 أهلاً بك! البوت جاهز الآن لمعالجة الفيديوهات والصوتيات محلياً بدون أي قيود أو توكنات.")

@app.on_message(filters.audio | filters.voice | filters.video | filters.document)
async def handle_media(client, message: Message):
    media = message.audio or message.voice or message.video or message.document
    if not media:
        return

    is_video = bool(message.video or (message.document and message.document.mime_type and "video" in message.document.mime_type))
    
    processing_msg = await message.reply_text("⏳ جاري تحليل وتعديل الأصوات محلياً...")

    input_file = await message.download()
    output_file = f"processed_{message.chat.id}.mp4" if is_video else f"processed_{message.chat.id}.wav"

    try:
        loop = asyncio.get_running_loop()
        
        if is_video:
            success = await loop.run_in_executor(None, process_video_file, input_file, output_file)
            if success and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                await message.reply_video(video=output_file, caption="✅ تم تعديل الأصوات النسائية داخل الفيديو بنجاح!")
            else:
                await message.reply_text("❌ حدث خطأ أثناء المعالجة.")
        else:
            success = await loop.run_in_executor(None, process_audio_smart_chunks, input_file, output_file)
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
    app.run()