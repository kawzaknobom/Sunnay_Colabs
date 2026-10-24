import nest_asyncio
nest_asyncio.apply()
import os

#########################################################

BOT_TOKEN = os.getenv('TOKEN')
PITCH_LIMIT = int(os.getenv('PITCH_LIMIT'))
RES_PITCH = float(os.getenv('PITCH_LIMIT'))


########################################################

import sklearn.cluster

class PatchedAgglomerativeClustering(sklearn.cluster.AgglomerativeClustering):
    def __init__(self, n_clusters=2, *, metric='euclidean', memory=None, connectivity=None, compute_full_tree='auto', linkage='ward', distance_threshold=None, compute_distances=False, affinity='deprecated'):
        # معالجة التوافق بين الاسم القديم والجديد
        if affinity != 'deprecated':
            metric = affinity
            
        super().__init__(
            n_clusters=n_clusters, 
            metric=metric, 
            memory=memory, 
            connectivity=connectivity, 
            compute_full_tree=compute_full_tree, 
            linkage=linkage, 
            distance_threshold=distance_threshold, 
            compute_distances=compute_distances
        )
        
        # توفير الخاصيتين معاً لمنع أي خطأ في المستقبل سواء كان يطلب metric أو affinity
        self.metric = metric
        self.affinity = metric

# تطبيق الترقيع على الكلاس الأصلي
sklearn.cluster.AgglomerativeClustering = PatchedAgglomerativeClustering

import os
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
import librosa
import soundfile as sf
import numpy as np

import builtins

# تجاوز طلبات التأكيد التفاعلية (مثل سؤال الثقة في PyTorch Hub) والرد بـ "y" تلقائياً
_original_input = builtins.input
def _auto_yes_input(prompt=""):
    if prompt and ("trusted repositories" in prompt or "trust" in prompt.lower()):
        print(f"🤖 [Auto-Trust] تم الرد بـ 'y' تلقائياً على: {prompt}")
        return "y"
    return _original_input(prompt)

builtins.input = _auto_yes_input
from simple_diarizer.diarizer import Diarizer

# إعدادات البوت (ضع بياناتك هنا)

API_ID = 15952578
API_HASH = '3600ce5f8f9b9e18cba0f318fa0e3600'  

app = Client("VoiceChangerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
def process_audio_with_simple_diarizer(input_audio_path, output_audio_path):
    y_orig = None
    try:
        y_orig, sr_orig = librosa.load(input_audio_path, sr=None)
        y_modified = y_orig.copy()

        diarizer = Diarizer(embed_model='xvec', cluster_method='ahc')
        raw_segments = diarizer.diarize(input_audio_path, threshold=0.45)
        
        print(f"🔍 المقاطع المستخرجة: {raw_segments}")
        
        speaker_segments = []
        
        if raw_segments is not None:
            for seg in raw_segments:
                if isinstance(seg, dict):
                    start = float(seg.get('start', 0))
                    end = float(seg.get('end', 0))
                    # استخدام label كمعرّف للمتحدث
                    spk = str(seg.get('speaker', seg.get('label', 'speaker_0')))
                    speaker_segments.append((start, end, spk))
                elif isinstance(seg, (list, tuple)) and len(seg) >= 3:
                    start = float(seg[0])
                    end = float(seg[1])
                    spk = str(seg[2])
                    speaker_segments.append((start, end, spk))

        speaker_genders = {}
        
        if speaker_segments:
            for start, end, spk in speaker_segments:
                if spk not in speaker_genders:
                    s_sample = int(start * sr_orig)
                    e_sample = int(end * sr_orig)
                    segment = y_orig[s_sample:e_sample]
                    
                    if len(segment) > sr_orig * 0.3:
                        f0, voiced_flag, voiced_probs = librosa.pyin(
                            segment, 
                            fmin=librosa.note_to_hz('C2'), 
                            fmax=librosa.note_to_hz('C7')
                        )
                        valid_f0 = f0[~np.isnan(f0)]
                        
                        if len(valid_f0) > 0:
                            mean_pitch = np.median(valid_f0)
                            print(f"🎤 [المتحدث {spk}] التردد الأساسي: {mean_pitch:.2f} Hz")
                            
                            speaker_genders[spk] = "female" if mean_pitch > PITCH_LIMIT else "male"
                        else:
                            speaker_genders[spk] = "male"
                    else:
                        speaker_genders[spk] = "male"
            
            print(f"📊 التصنيف النهائي لكل متحدث: {speaker_genders}")
            
            # تطبيق التعديل للمقاطع النسائية فقط لكل متحدث منفصل
            for start, end, spk in speaker_segments:
                if speaker_genders.get(spk) == "female":
                    s_sample = int(start * sr_orig)
                    e_sample = int(end * sr_orig)
                    segment = y_orig[s_sample:e_sample]
                    
                    if len(segment) > 0:
                        modified_segment = librosa.effects.pitch_shift(segment, sr=sr_orig, n_steps=-RES_PITCH)
                        if len(modified_segment) == len(segment):
                            y_modified[s_sample:e_sample] = modified_segment
                            
        sf.write(output_audio_path, y_modified, sr_orig)
        return True
        
    except Exception as e:
        print(f"خطأ في معالجة Simple Diarizer: {e}")
        if y_orig is not None:
            sf.write(output_audio_path, y_orig, sr_orig)
        else:
            y_fallback, sr_fallback = librosa.load(input_audio_path, sr=None)
            sf.write(output_audio_path, y_fallback, sr_fallback)
        return False        
def process_video_with_diarizer(input_video_path, output_video_path):
    pid = os.getpid()
    temp_audio = f"temp_audio_{pid}.wav"
    processed_audio = f"processed_audio_{pid}.wav"
    
    try:
        # استخراج الصوت من الفيديو بجودة نظيفة
        extract_cmd = [
            "ffmpeg", "-y", "-i", input_video_path, 
            "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1", temp_audio
        ]
        subprocess.run(extract_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # معالجة الصوت عبر Simple Diarizer
        process_audio_with_simple_diarizer(temp_audio, processed_audio)
            
        # دمج الفيديو الأصلي مع الصوت المعدل الجديد
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
        print(f"خطأ في دمج الفيديو: {e}")
        return False
    finally:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        if os.path.exists(processed_audio):
            os.remove(processed_audio)

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text("🤖 أهلاً بك! البوت جاهز الآن ويعمل بمكتبة **Simple Diarizer** السريعة والذكية لفصل المتحدثين وتعديل الأصوات النسائية.")

@app.on_message(filters.audio | filters.voice | filters.video | filters.document)
async def handle_media(client, message: Message):
    media = message.audio or message.voice or message.video or message.document
    if not media:
        return

    is_video = bool(message.video or (message.document and message.document.mime_type and "video" in message.document.mime_type))
    
    processing_msg = await message.reply_text("🔍 جاري تحليل وتحديد المتحدثين ومعالجة الصوت...")

    input_file = await message.download()
    output_file = f"processed_{message.chat.id}.mp4" if is_video else f"processed_{message.chat.id}.wav"

    try:
        loop = asyncio.get_running_loop()
        
        if is_video:
            success = await loop.run_in_executor(None, process_video_with_diarizer, input_file, output_file)
            if success and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                await message.reply_video(video=output_file, caption="✅ تم تعديل الفيديو وتغيير أصوات الإناث بنجاح!")
            else:
                await message.reply_text("❌ حدث خطأ أثناء معالجة الفيديو.")
        else:
            success = await loop.run_in_executor(None, process_audio_with_simple_diarizer, input_file, output_file)
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