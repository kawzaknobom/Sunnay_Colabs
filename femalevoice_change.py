import nest_asyncio
nest_asyncio.apply()
import os

#########################################################

BOT_TOKEN = os.getenv('TOKEN')
PITCH_LIMIT = int(os.getenv('PITCH_LIMIT'))
RES_PITCH = float(os.getenv('RES_PITCH'))


########################################################

import os
import subprocess
import librosa
import soundfile as sf
import numpy as np
from pyrogram import Client, filters

# إعدادات بوت التيليجرام (قم بوضع بياناتك هنا أو عبر متغيرات البيئة)

API_ID = "15952578"
API_HASH = "3600ce5f8f9b9e18cba0f318fa0e3600"

app = Client("voice_modifier_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def process_media_smart(input_path, output_path):
   
    y_orig = None
    try:
        # تحميل الصوت (سواء كان مرفوعاً كملف صوتي أو مستخرجاً من فيديو)
        y_orig, sr_orig = librosa.load(input_path, sr=None)
        y_modified = y_orig.copy()
        
        print("🔍 بدء التحليل الذكي وتقسيم الصوت إلى مقاطع زمنية...")
        intervals = librosa.effects.split(y_orig, top_db=30, frame_length=2048, hop_length=512)
        print(f"📊 عدد المقاطع المكتشفة: {len(intervals)}")
        
        for idx, (start_sample, end_sample) in enumerate(intervals):
            segment = y_orig[start_sample:end_sample]
            duration = (end_sample - start_sample) / sr_orig
            
            if duration > 0.3:
                f0, voiced_flag, voiced_probs = librosa.pyin(
                    segment, 
                    fmin=librosa.note_to_hz('C2'), 
                    fmax=librosa.note_to_hz('C7')
                )
                valid_f0 = f0[~np.isnan(f0)]
                
                if len(valid_f0) > 0:
                    mean_pitch = np.median(valid_f0)
                    print(f"🎵 [مقطع {idx+1}] المدة: {duration:.2f}s | التردد المرصود: {mean_pitch:.2f} Hz")
                    
                    if mean_pitch > PITCH_LIMIT:
                        print(f"   ↳ [نتيجة] أنثى (أعلى من {PITCH_LIMIT}) ♀️ -> جاري تعديل الصوت...")
                        modified_segment = librosa.effects.pitch_shift(segment, sr=sr_orig, n_steps=-RES_PITCH)
                        if len(modified_segment) == len(segment):
                            y_modified[start_sample:end_sample] = modified_segment
                    else:
                        print(f"   ↳ [نتيجة] ذكر (أقل من أو يساوي {PITCH_LIMIT}) 👨 -> إبقاء بدون تعديل")
                else:
                    print(f"🎵 [مقطع {idx+1}] لم يتم رصد تردد واضح")
                    
        # حفظ الصوت المعالج مؤقت بصيغة wav الآمنة
        temp_audio_path = "temp_processed.wav"
        sf.write(temp_audio_path, y_modified, sr_orig)
        
        # التحقق إذا كان الملف الأصلي فيديو أم صوت عادٍ
        if input_path.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')):
            print("🎬 دمج الصوت المعالج مع الفيديو الأصلي باستخدام FFmpeg...")
            # استخدام ffmpeg لدمج الصوت الجديد مع الفيديو الأصلي مع الحفاظ على الكواليتي
            cmd = [
                'ffmpeg', '-y', '-i', input_path, '-i', temp_audio_path,
                '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0',
                output_path
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
        else:
            # إذا كان صوتياً بحتاً، نقوم بإعادة تسمية ملف الـ wav للناتج النهائي
            os.rename(temp_audio_path, output_path)
            
        print("✨ تم الانتهاء من المعالجة وحفظ الملف بنجاح!")
        return True
        
    except Exception as e:
        print(f"خطأ في المعالجة: {e}")
        if y_orig is not None:
            sf.write(output_path, y_orig, sr_orig)
        else:
            y_fallback, sr_fallback = librosa.load(input_path, sr=None)
            sf.write(output_path, y_fallback, sr_fallback)
        return False

@app.on_message(filters.audio | filters.voice | filters.video | filters.document)
async def handle_media(client, message):
    msg = await message.reply("📥 جاري تحميل الملف الصوتي/المرئي...")
    
    input_file = await message.download()
    output_file = "processed_" + os.path.basename(input_file)
    
    await msg.edit("⚙️ جاري تحليل الترددات ومعالجة المقاطع النسائية...")
    
    success = process_media_smart(input_file, output_file)
    
    if success:
        await msg.edit("📤 جاري رفع الملف المعالج...")
        if message.video or (message.document and any(ext in str(message.document.mime_type) for ext in ["video", "mp4"])):
            await message.reply_video(output_file)
        else:
            await message.reply_audio(output_file)
        await msg.delete()
    else:
        await msg.edit("❌ حدث خطأ أثناء معالجة الملف.")
        
    if os.path.exists(input_file):
        os.remove(input_file)
    if os.path.exists(output_file):
        os.remove(output_file)

if __name__ == "__main__":
    print("🤖 البوت يعمل الآن...")
    app.run()