import nest_asyncio
nest_asyncio.apply()
import os

#########################################################

Bot_Token = os.getenv('TOKEN')
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
########################################################

import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
import librosa
import soundfile as sf
import numpy as np
from pyannote.audio import Pipeline

# إعدادات البوت
API_ID = 15952578          
API_HASH = "3600ce5f8f9b9e18cba0f318fa0e3600"  

# أدخل هنا توكن Hugging Face الخاص بك (مطلوبة لتشغيل نموذج pyannote)

app = Client("VoiceChangerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def process_audio_with_diarization(input_audio_path, output_audio_path):
    try:
        # 1. تحميل نموذج Diarization من pyannote لتحديد أوقات المتحدثين
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=HUGGINGFACE_TOKEN
        )
        
        # تطبيق التحليل على الملف الصوتي
        diarization = pipeline(input_audio_path)
        
        # تحميل الملف الصوتي كاملاً للتعامل معه كمصفوفة
        y, sr = librosa.load(input_audio_path, sr=None)
        
        # قائمة لتخزين الفترات التي تحتاج لتعديل (الإناث)
        # سنقوم بفحص كل متحدث وتحديد جنسه بناءً على متوسط طبقة الصوت لديه
        speaker_genders = {}
        
        # سنمر على الفترات الزمنية لتحديد الجنس لكل متحدث أولاً
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if speaker not in speaker_genders:
                start_sample = int(turn.start * sr)
                end_sample = int(turn.end * sr)
                segment = y[start_sample:end_sample]
                
                if len(segment) > sr * 0.5: # أخذ عينة لا تقل عن نصف ثانية
                    pitches, _ = librosa.piptrack(y=segment, sr=sr)
                    valid_pitches = pitches[pitches > 0]
                    mean_pitch = np.mean(valid_pitches) if len(valid_pitches) > 0 else 200
                    
                    # إذا كان متوسط التردد يقع في نطاق صوت الأنثى
                    speaker_genders[speaker] = "female" if mean_pitch > 160 else "male"
                else:
                    speaker_genders[speaker] = "male" # افتراضي للمقاطع القصيرة جداً

        # 2. إنشاء نسخة معدلة من الصوت
        y_modified = y.copy()
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if speaker_genders.get(speaker) == "female":
                start_sample = int(turn.start * sr)
                end_sample = int(turn.end * sr)
                segment = y[start_sample:end_sample]
                
                if len(segment) > 0:
                    # تعديل طبقة الصوت (Pitch Shifting) للمقاطع النسائية فقط
                    modified_segment = librosa.effects.pitch_shift(segment, sr=sr, n_steps=-4.0)
                    
                    # التأكد من مطابقة الحجم لعدم حدوث أخطاء في الاندماج
                    if len(modified_segment) == len(segment):
                        y_modified[start_sample:end_sample] = modified_segment

        # حفظ الملف النهائي المعدل
        sf.write(output_audio_path, y_modified, sr)
        return True
        
    except Exception as e:
        print(f"خطأ في معالجة Diarization: {e}")
        return False

def process_video_with_pyannote(input_video_path, output_video_path):
    pid = os.getpid()
    temp_audio = f"temp_audio_{pid}.wav"
    processed_audio = f"processed_audio_{pid}.wav"
    
    try:
        # استخراج الصوت من الفيديو
        extract_cmd = [
            "ffmpeg", "-y", "-i", input_video_path, 
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", temp_audio
        ]
        subprocess.run(extract_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # معالجة الصوت باستخدام Pyannote وتغيير أصوات الإناث فقط
        success = process_audio_with_diarization(temp_audio, processed_audio)
        if not success or not os.path.exists(processed_audio):
            return False
            
        # دمج الفيديو الأصلي مع الصوت الجديد المعدل
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
    await message.reply_text("🤖 أهلاً بك! البوت الآن مفعّل بنظام (Pyannote Diarization) لفصل المتحدثين بدقة وتعديل الإناث فقط.")

@app.on_message(filters.audio | filters.voice | filters.video | filters.document)
async def handle_media(client, message: Message):
    media = message.audio or message.voice or message.video or message.document
    if not media:
        return

    is_video = bool(message.video or (message.document and message.document.mime_type and "video" in message.document.mime_type))
    
    processing_msg = await message.reply_text("⏳ جاري تحليل المتحدثين وفصل الأصوات بدقة عالية، قد يستغرق ذلك وقتاً أطول...")

    input_file = await message.download()
    output_file = f"processed_{message.chat.id}.mp4" if is_video else f"processed_{message.chat.id}.wav"

    try:
        loop = asyncio.get_running_loop()
        
        if is_video:
            success = await loop.run_in_executor(None, process_video_with_pyannote, input_file, output_file)
            if success and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                await message.reply_video(video=output_file, caption="✅ تم التعرف على المتحدثين وتعديل أصوات الإناث بدقة داخل الفيديو!")
            else:
                await message.reply_text("❌ حدث خطأ أثناء المعالجة.")
        else:
            success = await loop.run_in_executor(None, process_audio_with_diarization, input_file, output_file)
            if success and os.path.exists(output_file):
                await message.reply_audio(audio=output_file, caption="✅ تم تعديل الملف الصوتي بدقة متناهية!")
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