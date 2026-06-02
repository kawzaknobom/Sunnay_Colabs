from cookies_nodb import Audio_Forms,Video_Forms,Image_forms,count,T_linebreak,Api_Id,Api_Hash,Coloration_File,g_langs,Small_line_break,seg_per_sec

import audioread,cv2,os,docx,arabic_reshaper,shutil,time,datetime,subprocess,re,img2pdf,asyncio,requests,json,urllib.parse
from typing import Union
from functools import reduce
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
import moviepy.video.fx.all as vfx

from pyrogram import Client,enums
from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery ,Message,MessageEntity
from pyrogram.errors import FloodWait
from pyrogram.enums import MessageEntityType

from spire.presentation import *
from spire.presentation.common import *
presentation = Presentation()
from md2pdf.core import md2pdf

from fpdf import FPDF
from PIL import Image 
from pypdf import PdfWriter, PdfReader
import pypdfium2 as pdfium
from pdf2image import convert_from_path
from bidi.algorithm import get_display
import pyarabic.araby as araby
from textwrap import wrap
from pdfCropMargins import crop

from docx.shared import Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from google import genai
from google.genai import types


import tika
tika.initVM()
from tika import parser


###### Pyrogram funcs 

def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  Session_file = Bot_Identifier+'_session_prm_bot'
  bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Bot_Token)
  return bot,Bot_Identifier

def Multi_Op_Dl(bot,dl_path,Files_Ids,User_Id,Del_Orig=False):
  Gen_List = []
  for No,Id in enumerate(Files_Ids) :
    File_Msg = Get_Msg(bot,User_Id,Id)
    File = File_Dl(File_Msg,dl_path)
    Gen_List.append(File)
    if Del_Orig :
      File_Msg.delete()
  return Gen_List

def File_Dl(File_Msg,dl_path): 
  File = File_Msg.download(file_name=dl_path)
  return File 

def Zip_Func(dir):
  Zip_File = os.listdir(dir)[0].split('.')[0]
  shutil.make_archive(base_name=Zip_File,format='zip',root_dir=dir)
  return Zip_File + '.zip'

def Msg_Delete(Msg):
  try : 
     Msg.delete()
  except FloodWait as e :
      time.sleep(e.value)
      return Msg_Delete(Msg)
  except Exception as err : 
    Msg.reply(err)
    pass

def Msg_Reply(Msg,Text,Buttons):
  try : 
     Replied = Msg.reply(text = Text,reply_markup = InlineKeyboardMarkup(Buttons),quote=True)
     return Replied
  except FloodWait as e :
      time.sleep(e.value)
      return Msg_Reply(Msg,Text,Buttons)
  except Exception as err : 
    Msg.reply(err)
    pass

def Reply_Query(Msg,Text,Buttons):
  try : 
     Query = Msg.reply(text = Text,reply_markup = InlineKeyboardMarkup(Buttons),quote=True)
     return Query
  except FloodWait as e :
      time.sleep(e.value)
      return Reply_Query(Msg,Text,Buttons)
  except Exception as err: 
    Msg.reply(err)
    pass

def is_int(val):
    try:
        int(val)
        return True
    except Exception as err :
      return False
    
def Get_Chnl_N(bot,Chnl_Id):
  try : 
     Chnl_Name = bot.get_chat(int(Chnl_Id) if is_int(Chnl_Id) else str(Chnl_Id).replace('=','_')).title
     return Chnl_Name
  except FloodWait as e :
      time.sleep(e.value)
      return Get_Chnl_N(bot,Chnl_Id)
  except Exception as err : 
    pass

  
def Msg_Copy(Msg,Chnl_Id):
  try : 
     Copy = Msg.copy(int(Chnl_Id) if is_int(Chnl_Id) else str(Chnl_Id).replace('=','_'))
     return Copy
  except FloodWait as e :
      time.sleep(e.value)
      return Msg_Copy(Msg,Chnl_Id)
  except Exception as err : 
    Msg.reply(err)
    pass
    
def Get_Msg(bot,Chat_id,msg_id):
  try : 
     msg = bot.get_messages(int(Chat_id) if is_int(Chat_id) else str(Chat_id).replace('=','_'),int(msg_id))
     return msg
  except FloodWait as e :
      time.sleep(e.value)
      return Get_Msg(bot,Chat_id,msg_id)
  except Exception as err : 
      pass

def Check_Admin(bot,Channel_id):
  try : 
     bot.get_chat_members(int(Channel_id) if is_int(Channel_id) else str(Channel_id).replace('=','_'))
     return True
  except FloodWait as e :
      time.sleep(e.value)
      return Check_Admin(bot,Channel_id)
  except : 
      False

def Send_Text_Res(Media_Msg,Text): 
  if len(Text) <= 4096 :
    if len(Text.strip()) != 0 :
        Media_Msg.reply(Text)
  else :
      textlist = wrap(Text.replace('\n','$'),4096)
      for part in textlist:
        if '$' in part : 
          part = part.replace('$','\n')
        Flood_Wait_fix(Media_Msg,part)
  
def Flood_Wait_fix(Media_Msg,part):
  try : 
   Media_Msg.reply(part)
  except FloodWait as err : 
   time.sleep(err.x)
   return Flood_Wait_fix(Media_Msg,part)
   
def Upld_File(file,Msg,cap=' ',isogg=False):
  try:
    if file != None:
      if file.lower().endswith(Audio_Forms):
            RMsg = Msg.reply_audio(file,caption=cap)
      elif file.lower().endswith(Video_Forms):
        Dir = '/'.join(file.split('/')[:-1]) + '/'
        Thumb = Thumbnail_Get(Dir,file)
        Dur = Get_Stream_Dur(file)
        RMsg = Msg.reply_video(file,caption=cap,duration=Dur,thumb=Thumb)
      elif file.lower().endswith(Image_forms):
          RMsg = Msg.reply_photo(file)
      else :
          RMsg = Msg.reply_document(file,caption=cap)
      return RMsg.id
  except FloodWait as e:
    time.sleep(e.value)
    return Upld_File(file,Msg,cap)
  except Exception as err : 
        Err = f'حدث خطأ ما 😞 \n\n {err}'
        raise Exception(Err) 
  
def Upld_Dir_Func(Extract_Dir,Msg):
  Msgs_List = [] 
  filelist = Dir_List(Extract_Dir)
  for file in filelist :
   if os.path.isfile(file) :
    Msg_Pair = Upld_File(file,Msg)
    Msg_Pair = [Msg_Pair,]
   else :
    if os.path.isdir(file+'/'):
      Msg_Pair = Upld_Dir_Func(file+'/',Msg)
   Msgs_List += Msg_Pair
  shutil.rmtree(Extract_Dir)
  return Msgs_List

######## منوعات ######

def Rmv_Dups(Dup_List):
   unique_list = []
   for i in Dup_List:
    if i not in unique_list:
      unique_list.append(i)
   return unique_list 
   
def random_name():
    current_time = datetime.datetime.now()
    timestamp = current_time.strftime("%Y%m%d%H%M%S%f")
    File_Name = f"file_{timestamp}"
    return File_Name
    
def Create_Dir(Dir):
  if not os.path.isdir(Dir):
    Mkdir_Cmd = f'mkdir -p "{Dir}"'
    os.system(Mkdir_Cmd)
      
def Check_Dir(Dir):
  if os.path.isdir(Dir):
      shutil.rmtree(Dir)
  Create_Dir(Dir)

def Check_File(File):
  if os.path.isfile(File):
      os.remove(File)

def Dir_List(Dir): 
  List = sorted(os.listdir(Dir))
  for No,elm in enumerate(List) : 
    List[No] = Dir+elm
  return List 
  
def Get_Name(Msg):
  if Msg.audio :
    Name = Msg.audio.file_name
  elif Msg.video :
    Name = Msg.video.file_id
  elif Msg.voice :
    Name = Msg.voice.file_id
  elif Msg.document :
    Name = Msg.document.file_name
  elif Msg.photo :
    Name = Msg.photo.file_id
  return Name 

def Doc_Filter(Msg):
   if Msg.document : 
    if Msg.document.file_name.lower().endswith(Audio_Forms+Video_Forms) : 
      return True
   else : 
     return True

def U_R_Not_Sub(message) : 
  Paid_Bot = "هذا البوت مدفوع \n\n يمكنك الاشتراك بالباقة المميزة \n\n https://t.me/sunnaybots/9 "
  message.reply(Paid_Bot,disable_web_page_preview=True)

def Wrap_Text(text,num):
 if '\n' in text : 
  text= text.replace('\n','§')
 Text_list = wrap(text,num)
 for No,part in enumerate(Text_list) : 
  if '§' in part :
   Text_list[No] = part.replace('§','\n')
 return Text_list 
    
 
##############

def Encode_Vid(File):
    Mp4_File = ('.' if File[1]=='/' else '') + File.split('.')[(1 if File[0] == '.' else 0)] + '_encoded.mp4'
    Vid_Encode = f'ffmpeg -i "{File}" -c:a aac -codec:v h264 -b:v 1000k "{Mp4_File}" -y'
    os.system(Vid_Encode)
    return Mp4_File
      
def Cv2_PicCap(Media_Path):
  Thumb_Nail = ('.' if Media_Path[1]=='/' else '') + Media_Path.split('.')[(1 if Media_Path[0] == '.' else 0)] + '_Thumb.jpg'
  try:
     cam = cv2.VideoCapture(Media_Path)
     ret, frame = cam.read()
     cv2.imwrite(Thumb_Nail, frame)
     cam.release()
     cv2.destroyAllWindows()
     return Thumb_Nail
  except :
    Media_Path = Encode_Vid(Media_Path)
    return Cv2_PicCap(Media_Path) 
    
def Thumbnail_Get(thumb_dir,Media_Path):
  Img_File = Get_File(thumb_dir,Image_forms)
  if Img_File :
       Thumb_Nail = Img_File
       if not Thumb_Nail.lower().endswith(('jpeg')):
         img = Image.open(Thumb_Nail)
         width, height = img.size
         if width > 320 or height > 320:
          if width > height:
              new_width = 320
              new_height = int(height * (320 / width))
          else:
              new_height = 320
              new_width = int(width * (320 / height))
         img = img.resize((new_width, new_height))
         Thumb_Nail = Thumb_Nail.split('.')[0] + '.jpeg'
         img.save(Thumb_Nail)
         file_size = os.path.getsize(Thumb_Nail) / 1024
         quality = 90
         while file_size >= 200:
          img.save(Thumb_Nail, quality=quality)
          file_size = os.path.getsize(Thumb_Nail) / 1024
          quality -= 5
          if quality < 10:
            break 
  else :
    if Media_Path.lower().endswith(Video_Forms) :
       Thumb_Nail = Cv2_PicCap(Media_Path)
    else : 
     Thumb_Nail = 'Sunnay_Logo.jpg'
     if not os.path.isfile(Thumb_Nail):
      Thumb_Link = 'https://img1.teletype.in/files/81/52/81521984-f683-4a99-88ff-0c5c8896fd8b.jpeg'
      os.system(f"wget -O '{Thumb_Nail}' '{Thumb_Link}' ")
  return Thumb_Nail
             
  
  
### AI Translation  ###


def Grap_Lang(Sym): 
  for lang in g_langs :
    if Sym in lang : 
      F_L = lang.split('|')[0].strip()
      break
  return F_L


## Gemini 

def Rmv_Trans(Res):
  Res_Lines = Res.split('\n')
  for No,line in enumerate(Res_Lines) :
    if any(x in line for x in (  'ترجم', 'translat')):
     Res_Lines.pop(No)
  Res = '\n'.join(Res_Lines)
  return Res


########### AI TRANSCRIPTION ###############

#### Image Funcs ####

def Merge_Images_UP(file1, file2):
    image1 = Image.open(file1)
    image2 = Image.open(file2)
    (width1, height1) = image1.size
    (width2, height2) = image2.size
    result_width = max(width1,width2)
    if width1 > width2 :
      aspectoheight2 = (result_width * height2) / width2
      result_height = height1 + int(aspectoheight2)
      result = Image.new('RGB', (result_width, result_height))
      iso1 = image1.resize((result_width,height1))
      iso2 = image2.resize((result_width,int(aspectoheight2)))
      result.paste(iso1, box=(0, 0))
      result.paste(iso2, box=(0, height1))
    else :
      aspectoheight1 = (result_width * height1) / width1
      result_height = int(aspectoheight1) + height2
      result = Image.new('RGB', (result_width, result_height))
      iso1 = image1.resize((result_width,int(aspectoheight1)))
      iso2 = image2.resize((result_width,height2))
      result.paste(iso1, box=(0, 0))
      result.paste(iso2, box=(0, int(aspectoheight1)))
    if file2.startswith('.'):
     Ind = 1 
    else :
     Ind = 0
    outimg = ('.' if file2.startswith('.') else '') + file2.split('.')[Ind] + '_Merged.jpg'
    result.save(outimg) 
    os.remove(file1)
    os.remove(file2)
    return outimg
    
def Merge_Images_SBS(file1, file2):
    image1 = Image.open(file1)
    image2 = Image.open(file2)
    (width1, height1) = image1.size
    (width2, height2) = image2.size
    result_height = max(height1, height2)
    if height1 > height2 :
      aspectowidth2 = (result_height * width2) / height2
      result_width = width1 + int(aspectowidth2)
      result = Image.new('RGB', (result_width, result_height))
      iso1 = image1.resize((width1,result_height))
      iso2 = image2.resize((int(aspectowidth2),result_height))
      result.paste(iso1, box=(0, 0))
      result.paste(iso2, box=(width1, 0))
    else :
      aspectowidth1 = (result_height * width1) / height1
      result_width = width2 + int(aspectowidth1)
      result = Image.new('RGB', (result_width, result_height))
      iso1 = image1.resize((int(aspectowidth1),result_height))
      iso2 = image2.resize((width2,result_height))
      result.paste(iso1, box=(0, 0))
      result.paste(iso2, box=(int(aspectowidth1), 0))
    if file2.startswith('.'):
     Ind = 1 
    else :
     Ind = 0
    outimg = ('.' if file2.startswith('.') else '') + file2.split('.')[Ind] + '_Merged.jpg'
    result.save(outimg) 
    os.remove(file1)
    os.remove(file2)
    return outimg


def Blur_Func(file_path,blur_rate):
  if file_path.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  P_Name = ('.' if file_path.startswith('.') else '') + file_path.split('.')[Ind]
  Ex = file_path.split('.')[-1]
  Res_File = f"{P_Name}_Blurred.{Ex}"
  
  if file_path.lower().endswith(Image_forms):
    image = cv2.imread(file_path)
    blur_image = cv2.blur(image, (blur_rate,blur_rate))
    cv2.imwrite(Res_File, blur_image)
  else :
    Aud = Mp3_Conv(file_path)
    # file_path = Media_Compress(file_path)
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
      raise ValueError("Error opening video file")
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(Res_File, fourcc, fps, (width, height))
    while True:
      ret, frame = cap.read()
      if ret:
        blurred_frame = cv2.GaussianBlur(frame, (51, 51), blur_rate)
        out.write(blurred_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
      else:
        break 
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    Res_File = Vid_Mk(Res_File,Aud)
    Res_File = Media_Compress(Res_File)
  return Res_File
  
def Color_Pic(colorpath,color):
  if colorpath.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  imgfile = ('.' if colorpath.startswith('.') else '') + colorpath.split('.')[Ind] + '_Colored.jpg'
  #if color == "g" : 
  #  Args = '-f rms'
  if color == "y" :
    Args = '-h 60 -s 50 -l 0'
  elif color == "b":
    Args = '-h 180 -s 50 -l 0'
  elif color == "r":
    Args = '-h 0 -s 50 -l 0'
  elif color == "p":
    Args = '-h 330 -s 50 -l 0'
  Color_Cmd = f'./coloration {Args} "{colorpath}" "{imgfile}" '
  os.system(Color_Cmd)
  os.remove(colorpath)
  return imgfile

### Pdf Funcs ###

def Txt_Trim(Txt_File,Start_Word,End_Word):
    Start_Word = Start_Word.strip()
    End_Word = End_Word.strip()
    Res_File = Txt_File.split('.')[0] + '_Trimmed.txt'
    Orig_Text = open(Txt_File,'r').read()
    start_index = Orig_Text.find(Start_Word)
    end_index = Orig_Text.find(End_Word, start_index) + len(End_Word)
    if start_index == -1 or end_index == -1:
      return
    Extracted_text = Orig_Text[start_index:end_index]
    open(Res_File,'w').write(Extracted_text)
    return Res_File

def Pdf_Compress(bot,dl_path,File):
  pdf_file = ('.' if File.startswith('.') else '') + File.split('.')[1 if File[0] == '.' else 0] + '_Compressed.pdf'
  Multi_Temp_Chnl = -1003456116922
  Extract_Dir = Pdf_Extract(File)
  Repl_Msg = bot.send_message(Multi_Temp_Chnl,'.')
  Msgs_List = Upld_Dir_Func(Extract_Dir,Repl_Msg)
  Process_List = Multi_Op_Dl(bot,dl_path,Msgs_List,Multi_Temp_Chnl,True)
  Pdf_File = Pdf_Make(Process_List)
  os.rename(Pdf_File,pdf_file)
  return pdf_file

def Mdx2PDf(Mdf):
  # pdf_file = ('.' if Mdf.startswith('.') else '') + Mdf.split('.')[1 if Mdf[0] == '.' else 0] + '.pdf'
  Dl_Dir = ('.' if Mdf.startswith('.') else '') + '/' + '/'.join(Mdf.split('/')[:-1]) + '/'
  Mdx2PDf_Cmd = f'python3 mdx_converter.py "{Mdf}" "output-directory/" --format pdf'
  os.system(Mdx2PDf_Cmd)
  Pdf_File = Get_File(Dl_Dir,'pdf')
  # md2pdf(pdf_file,Mdf)
  return Pdf_File

def PPF2PDF(PPF):
  pdf_file = ('.' if PPF.startswith('.') else '') + PPF.split('.')[1 if PPF[0] == '.' else 0] + '.pdf'
  try:
    presentation.LoadFromFile(PPF)
    presentation.SaveToFile(pdf_file, FileFormat.PDF)
    presentation.Dispose()
  except Exception as err :
    print('====>>',err)
  return pdf_file

def Pdf_Margin(Pdf_File):
    Pdf_Cut_File, exit_code, stdout_str, stderr_str = crop(["-p4", "10", "10", "10", "10", Pdf_File],string_io=True, quiet=False)
    return Pdf_Cut_File
  
def Color_Pdf(File,color):
  Extract_Dir = Pdf_Extract(File)
  Img_List = Dir_List(Extract_Dir)
  for Img in Img_List : 
    Colored_Img = Color_Pic(Img,color)
    os.remove(Img)
  Img_List = Dir_List(Extract_Dir)
  Pdf_File = Pdf_Make(Img_List)
  return Pdf_File
  
def Pdf_Page_Num(File):
  Reader = PdfReader(File)
  Num = len(Reader.pages)
  return Num 
  
def Pdf_Make(Img_List):
 if Img_List[-1].startswith('.'):
     Ind = 1 
 else :
     Ind = 0
 Pdf_File = ('.' if Img_List[-1].startswith('.') else '') +Img_List[-1].split('.')[Ind] + '_Created.pdf'
 try : 
   open(Pdf_File,"wb").write(img2pdf.convert(Img_List))
 except : 
  Imgs = []
  for Img in Img_List : 
   image = Image.open(Img).convert("RGB")
   Imgs.append(image)
  if len(Imgs) == 1:
   Imgs[0].save(Pdf_File)
  else :
   Imgs[0].save(Pdf_File, save_all=True,append_images=Imgs[1:])
 return Pdf_File

def Grap_PicDir(Dir,Img_list=[]):
  for Obj in os.listdir(Dir):
    if os.path.isfile(Dir+Obj):
     if Obj.lower().endswith(Image_forms):
      if os.path.getsize(Dir+Obj) > 1024 :
        Img_list.append(Dir+Obj)
    else :
      New_Dir = Dir+Obj+'/'
      return Grap_PicDir(New_Dir,Img_list)
  return Img_list
      
def Pdf_Merge(Files_List):
 if Files_List[-1].startswith('.'):
     Ind = 1 
 else :
     Ind = 0
 Pdf_File = ('.' if Files_List[-1].startswith('.') else '') +Files_List[-1].split('.')[Ind] + '_Merged.pdf'
 Merger = PdfWriter()
 for Elm in Files_List : 
  Merger.append(Elm)
 Merger.write(Pdf_File)
 return Pdf_File

def Pdf_Trim(File,Start,End):
    Reader = PdfReader(File)
    Writer = PdfWriter()
    if File.startswith('.'):
     Ind = 1 
    else :
     Ind = 0
    Res = ('.' if File.startswith('.') else '') +File.split('.')[Ind] + '_Trim.pdf'
    Pages = (Start,End)
    Page_Range = range(Pages[0], Pages[1] + 1)
    for page_num, page in enumerate(Reader.pages, 1):
     if page_num in Page_Range:
        Writer.add_page(page)
    Writer.write(open(Res,'wb'))
    return Res

def Pdf_Page(File,Page):
  Reader = PdfReader(File)
  Writer = PdfWriter()
  Writer.add_page(Reader.pages[Page-1])
  if File.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  Res = ('.' if File.startswith('.') else '') +File.split('.')[Ind] + '_Trim.pdf'
  Writer.write(open(Res,'wb'))
  return Res

def Pdf_Extract(File):
 if File.startswith('.'):
     Ind = 1 
 else :
     Ind = 0
 Nom = os.path.basename(File).split('.')[0]
 Extract_Dir = ('.' if File.startswith('.') else '') +File.split('.')[Ind] + '/Extract_Dir/'
 Check_Dir(Extract_Dir)
 Pdf_Pages = convert_from_path(File,output_folder=Extract_Dir,fmt='jpeg')
 return Extract_Dir

def Unlock_Pdf(File):
  if File.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  Unlocked_File = ('.' if File.startswith('.') else '') +File.split('.')[Ind] + '_Unlocked.pdf'
  Extract_Dir = Pdf_Extract(File)
  Img_List = Dir_List(Extract_Dir)
  Pdf_File = Pdf_Make(Img_List)
  os.rename(Pdf_File,Unlocked_File)
  return Unlocked_File
  

### Epub Extract ###

def Epub_Extract_Func(Epub_File):
  if Epub_File.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  Textfile = ('.' if Epub_File.startswith('.') else '') +Epub_File.split('.')[Ind] + '.txt'
  parsed = parser.from_file(Epub_File)
  finalText = parsed['content']
  open(Textfile, "a").write(f" {finalText} ")
  return Textfile
  
def Zip_Extract(File):
  Ex = '.' + File.split('.')[-1]
  Extract_Dir = File.replace(Ex,'/')
  Check_Dir(Extract_Dir)
  Unzip_Cmd = f'unzip "{File}" -d "{Extract_Dir}"'
  os.system(Unzip_Cmd)
  return Extract_Dir

#### Arch Upld Funcs  ####
      

###### Transcribe #####


def Media_F_func(Media_File,Stream_Dur,ispublic):
  if Media_File.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  result = ('.' if Media_File.startswith('.') else '') +Media_File.split('.')[Ind] + '.txt'
  if Stream_Dur <= 1800 :
    result = Trans_Func(Media_File,ispublic)
  else : 
    Parts_Dir = Aud_Scatter(Media_File,1800)
    numdir = len(os.listdir(Parts_Dir))
    Transcribe_Path = Media_File.replace(Media_File.split('/')[-1],'')
    with open(result,'a') as f : 
      for x in range(0,numdir):
       seg_path=f"{Parts_Dir}rmvd{str(x).zfill(9)}.wav"
       seg_res = Transcribe_Path+'p'+str(x)+result.split('/')[-1]
       seg_res = Trans_Func(seg_path,ispublic)
       text = open(seg_res,'r').read()
       f.write(text+Small_line_break)
       time.sleep(60)
  return result

def Send_TRes(Media_Msg,Txt_File): 
  Media_Msg.reply_document(Txt_File)
  # pdfresult = ('.' if Txt_File[0]=='.' else '' ) + Txt_File.split('.')[1 if Txt_File[0]=='.' else 0 ] + '.pdf'
  # try : 
  #  pdfres = Txt_2_Pdf(Txt_File)
  #  Media_Msg.reply_document(pdfres)
  # except : 
  #  Media_Msg.reply( 'حدث خطأ في صناعة بدف')
  text = open(Txt_File,encoding='utf-8').read()
  Send_Text_Res(Media_Msg,text)

def Trans_Func(mp3file,ispublic):
  aud_path = Mp3_Conv(mp3file)
  if mp3file.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  script = 'speech.py' if ispublic else 'p_speech.py'  
  Txt_File = ('.' if mp3file.startswith('.') else '') + mp3file.split('.')[Ind] + '.txt'
  Check_File(Txt_File)
  public_ar = 'BO6JR7DUZ2EOPIGCQISJUDILS7IWBTJF'
  # public_ar = "NCCGCWTO7ILBXGIEEYSLQF2SBVQDZK5X"
  private_ar = "BO6JR7DUZ2EOPIGCQISJUDILS7IWBTJF"
  Lang_token = public_ar if ispublic else private_ar
  os.system(f'python3 {script} "{Lang_token}" "{aud_path}" "{Txt_File}" ')
  Res_Text = open(Txt_File,'r').read().replace('.',' ، ')
  with open(Txt_File,'w') as f : 
    f.write(Res_Text.replace('?',' ؟'))
  return Txt_File

#### Media Funcs ####

def Mute_Video(File):
  Muted_Vid = ('.' if File.startswith('.') else '') + '.'.join(File.split('.')[:-1]) + '_Muted.mp4'
  Mute_Cmd = f'ffmpeg -i "{File}" -f lavfi -i anullsrc -map 0:v -map 1:a -c:v copy -shortest "{Muted_Vid}"'
  os.system(Mute_Cmd)
  return Muted_Vid

def Sub_Aud(Vid,Aud):
  Sub_Vid = ('.' if Vid.startswith('.') else '') + '.'.join(Vid.split('.')[:-1]) + '_Subed.mp4'
  SubAud_Cmd = f'ffmpeg -i "{Vid}" -i "{Aud}" -c:v copy -map 0:v:0 -map 1:a:0 "{Sub_Vid}"'
  os.system(SubAud_Cmd)
  return Sub_Vid

def Get_Stream_Dur(File): 
  if os.path.basename(File).endswith(Audio_Forms):
    Stream_Dur = int(audioread.audio_open(File).duration)
  else : 
     cap = cv2.VideoCapture(File)
     fps = cap.get(cv2.CAP_PROP_FPS)
     totalNoFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
     durationInSeconds = totalNoFrames // fps
     Stream_Dur = int(durationInSeconds)
  return Stream_Dur
  
def Msg_Dur(Msg):
  if Msg.audio : 
    dur = Msg.audio.duration
  elif Msg.video : 
    dur = Msg.video.duration 
  elif Msg.voice : 
    dur = Msg.voice.duration
  else : 
    dur = 0
  return int(dur)

def Dur_Get(Msg,File):
  Dur = Msg_Dur(Msg)
  if Dur == 0 :
    Dur = Get_Stream_Dur(File)
  return Dur
  
def Vid_Mk(Vid,Aud):
  Vid_Res = ('.' if Vid.startswith('.') else '') + Vid.split('.')[(1 if Vid[0]=='.' else 0)] + '_Merged.mp4'
  Sub_Cmd = f'ffmpeg -i "{Vid}" -i "{Aud}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{Vid_Res}" -y'
  os.system(Sub_Cmd)
  return Vid_Res

def Mp3_Conv(File):
  Mp3_File = ('.' if File.startswith('.') else '') +  File.split('.')[(1 if File[0] == '.' else 0)] + '_Conv.mp3'
  Mp3_Cmd = f'ffmpeg -i "{File}" -q:a 0 -map a "{Mp3_File}" -y'
  os.system(Mp3_Cmd)
  return Mp3_File
  
def Aud_Scatter(File,Seg_Per_Sec):
    if File.startswith('.'):
     Ind = 1 
    else :
     Ind = 0
    Parts_Dir = ('.' if File.startswith('.') else '') + File.split('.')[Ind] + '_Parts/'
    Check_Dir(Parts_Dir)
    File = Mp3_Conv(File)
    Scatter_Cmd = f'ffmpeg -i "{File}" -f segment -segment_time {Seg_Per_Sec} -c copy "{Parts_Dir}rmvd%09d.wav" -y'
    os.system(Scatter_Cmd)
    os.remove(File)
    return Parts_Dir

def Vid_Mon(img_path,aud_path):
      if img_path.startswith('.'):
         Ind = 1 
      else :
       Ind = 0
      vid_path = ('.' if img_path.startswith('.') else '') + img_path.split('.')[Ind] + '_Montaj.mp4'
      Montaj_Cmd = f'nice -n -20 ffmpeg -r 1 -loop 1 -y -i "{img_path}" -i "{aud_path}" -c:v libx264 -tune stillimage -c:a copy -shortest -vf scale=1920:1080 "{vid_path}"'
      os.system(Montaj_Cmd)
      try : 
        Thumbnail = Cv2_PicCap(vid_path)
        return vid_path,Thumbnail
      except : 
        return Vid_Mon(img_path,aud_path)

def Vid_Merge(Vid_Txt) :
  Vid_File = ('.' if Vid_Txt[0] =='.' else '') + Vid_Txt.split('.')[1 if Vid_Txt[0] =='.' else 0 ] + '_VMerged.mkv'
  Vid_Cmd = f'ffmpeg -f concat -safe 0 -i "{Vid_Txt}" -c copy "{Vid_File}"'
  os.system(Vid_Cmd)
  # Vid_File = ('.' if Vid_list[0][0] =='.' else '') + Vid_list[0].split('.')[1 if Vid_list[0][0] =='.' else 0 ] + '_VMerged.mp4'
  # Moviepy_List = []
  # for vid in Vid_list : 
  #   clip = VideoFileClip(vid)
  #   Moviepy_List.append(clip)
  # Method = "chain"
  # final_clip = concatenate_videoclips(Moviepy_List, method=Method)
  # final_clip.write_videofile(Vid_File,codec="libx264")
  
  # max_w = max(clip.w for clip in Moviepy_List)
  # max_h = max(clip.h for clip in Moviepy_List)
  # target_resolution = (max_w, max_h)
  # processed_clips = [vfx.resize(clip,target_resolution) for clip in Moviepy_List]
  # final_clip = concatenate_videoclips(processed_clips, method="chain")
  # final_clip.write_videofile(Vid_File, codec="libx264")

  # resolutions = [tuple(clip.size) for clip in Moviepy_List]
  # unique_resolutions = set(resolutions)
  # try :
  #   if len(unique_resolutions) == 1:
  #       Method = "chain"
  #       final_clip = concatenate_videoclips(Moviepy_List, method=Method)
  #   else:
  #       Method = "compose"
  #       Bg_color=[0,0,0]
  #       final_clip = concatenate_videoclips(Moviepy_List, method=Method,bg_color=Bg_color)
  #   final_clip.write_videofile(Vid_File,codec="libx264")
  # except AttributeError as e:
  #  pass
  return Vid_File

def Aud_Merge(Txt_File):
    if Txt_File.startswith('.'):
     Ind = 1 
    else :
     Ind = 0
    Mp3_File = ('.' if Txt_File.startswith('.') else '') + Txt_File.split('.')[Ind] + '_Merged.mp3'
    Aud_Merge_Cmd = f'ffmpeg -f concat -safe 0 -i "{Txt_File}" "{Mp3_File}" -y'
    os.system(Aud_Merge_Cmd)
    os.remove(Txt_File)
    return Mp3_File

def Media_Amplify(file_path,Rate):
  if file_path.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  Mp3_File = ('.' if file_path.startswith('.') else '') + file_path.split('.')[Ind] + '_Amplified.mp3'
  if file_path.lower().endswith(Audio_Forms):
    Res_File = Mp3_File
  else: 
    Res_File = file_path.split('.')[Ind] + '_Amplified.mp4'
  Amplify_Cmd = f'ffmpeg -i "{file_path}" -filter:a volume={Rate}dB "{Mp3_File}"'
  os.system(Amplify_Cmd)
  if file_path.lower().endswith(Video_Forms):
    Res_File = Vid_Mk(file_path,Mp3_File)
  return Res_File

def Media_Change(file_path):
  if file_path.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  Mp3_File = ('.' if file_path.startswith('.') else '') + file_path.split('.')[Ind] + '_Changed.mp3'
  if file_path.lower().endswith(Audio_Forms):
    Res_File = Mp3_File
  else: 
    Res_File = file_path.split('.')[Ind] + '_Changed.mp4'
  Change_Cmd = f'ffmpeg -i "{file_path}" -af asetrate=44100*0.75,aresample=44100,atempo=4/3 "{Mp3_File}"'
  os.system(Change_Cmd)
  if file_path.lower().endswith(Video_Forms):
    Res_File = Vid_Mk(file_path,Mp3_File)
  return Res_File
  
def Media_Skip(file_path):
  if file_path.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  Res_File = ('.' if file_path.startswith('.') else '') + file_path.split('.')[Ind] + '_Skipped.mp3'
  Skip_Cmd = f'ffmpeg -i "{file_path}" -af "silenceremove=start_periods=1:stop_periods=-1:start_threshold=-30dB:stop_threshold=-50dB:start_silence=2:stop_silence=2" "{Res_File}"'
  os.system(Skip_Cmd)
  return Res_File
  
def Media_Compress(file_path,Rate=None):
  if file_path.lower().endswith(Audio_Forms) : 
   Res_File = ('.' if file_path.startswith('.') else '') + file_path.split('.')[(1 if file_path[0] == '.' else 0)] + '_Comp.mp3'
   Comp_Cmd = f'ffmpeg -i "{file_path}" -b:a "{Rate}" "{Res_File}" -y '
  else :
    Res_File = ('.' if file_path.startswith('.') else '') + file_path.split('.')[(1 if file_path[0] == '.' else 0)] + '_Comp.mp4'
    Comp_Cmd = f'ffmpeg -i "{file_path}" -c:v libx265 -crf 28 "{Res_File}" -y'
  os.system(Comp_Cmd)
  return Res_File

def Media_Speed(file_path,Rate):
  if file_path.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  if file_path.lower().endswith(Audio_Forms) : 
   Res_File = ('.' if file_path.startswith('.') else '') + file_path.split('.')[Ind] + '_Speed.mp3'
   Speed_Cmd = f'ffmpeg -i "{file_path}" -filter:a "atempo={Rate}" -vn "{Res_File}" -y '
  else :
    Res_File = ('.' if file_path.startswith('.') else '') + file_path.split('.')[Ind] + '_Speed.mp4'
    A_Rate = Rate
    V_Rate = Speed_St(Rate)
    if Rate in ('0.75','0.5'):
      A_Rate = V_Rate
      if Rate == '0.75':
         V_Rate = 1.25
      elif Rate == '0.5':
         V_Rate = 1.5
    Speed_Cmd = f'''ffmpeg -i "{file_path}" -filter_complex "[0:v]setpts={V_Rate}*PTS[v];[0:a]atempo={A_Rate}[a]" -map "[v]" -map "[a]" "{Res_File}" -y '''
  os.system(Speed_Cmd)
  return Res_File

def Media_Trim(file_path,Rate):
  point_list = Rate.split('-') 
  strt_point = point_list[0]
  end_point = point_list[1]
  if file_path.startswith('.'):
     Ind = 1 
  else :
     Ind = 0
  if file_path.lower().endswith(Audio_Forms): 
    Res_File = ('.' if file_path.startswith('.') else '') + file_path.split('.')[Ind] + '_Trim.mp3'
    Trim_Cmd = f'ffmpeg -i "{file_path}" -ss {strt_point} -to {end_point} "{Res_File}" -y'
    os.system(Trim_Cmd)
  else :
    Mp4_File = ('.' if file_path.startswith('.') else '') + file_path.split('.')[Ind] + '_Trim1.mp4'
    Trim_Cmd = f'ffmpeg -i "{file_path}" -ss {strt_point} -strict -2 -to {end_point} -c:a aac -codec:v h264 -b:v 1000k "{Mp4_File}" -y '
    os.system(Trim_Cmd)
    Res_File = Media_Compress(Mp4_File)
    # Encode_Vid
    
  return Res_File
  
def Speed_St(A_Rate):
  if A_Rate == '1.25':
    V_Rate = 0.5
  elif A_Rate == '0.75':
    V_Rate = 0.8
  elif A_Rate == '0.5':
    V_Rate = 0.66666666666
  elif A_Rate == '1.5':
    V_Rate = 0.66666666666
  elif A_Rate == '1.75':
    V_Rate = 0.57142857142
  elif A_Rate == '2':
    V_Rate = 0.5
  return V_Rate

######### Demucs Funcs 

def demucs_func(file_path):
  file_path =  Mp3_Conv(file_path)
  File_Dir = '/'.join(file_path.split('/')[:-1]) + '/'
  
  #### rename ####
  New_Name =  random_name()
  New_File = f'{File_Dir}{New_Name}.mp3'
  os.rename(file_path,New_File)
  file_path = New_File
  ########
  demucs_model = 'mdx_extra'
  demucs_Cmd = f"demucs -n '{demucs_model}' '{file_path}'"
  os.system(demucs_Cmd)
  demucs_Dir = f'/content/separated/{demucs_model}'
  vocal_path = f'{demucs_Dir}/{New_Name}/vocals.wav'
  vocal_path =  Mp3_Conv(vocal_path)
  return vocal_path

def Music_Rmv(rmvmessage,rmvpath,streamdur):
  streamdur = int(streamdur)
  if streamdur == 0 :
    streamdur =  Get_Stream_Dur(rmvpath)
  mainDir = '/'.join(rmvpath.split('/')[:-1]) + '/'
  copymp4 = mainDir +  rmvpath.split('/')[-1].split('.')[0] + '_Copy.mp4'
  cp_Cmd = f'cp "{rmvpath}" "{copymp4}"'
  os.system(cp_Cmd)
  if streamdur <= seg_per_sec :
    vocal_path =  demucs_func(rmvpath)
  else :
    musicrmvlist =  mainDir + rmvpath.split('/')[-1].split('.')[0] + '_Mlist.txt'
    Parts_Dir =  Aud_Scatter(rmvpath,seg_per_sec)
    with open(musicrmvlist,'a') as f :
      for x in range(0,len(os.listdir(Parts_Dir))):
        seg_path=f"{Parts_Dir}rmvd{str(x).zfill(9)}.wav"
        vocal_path =  demucs_func(seg_path)
        f.write(f'file {vocal_path} \n')

    vocal_path =  Aud_Merge(musicrmvlist)
  if rmvpath.lower().endswith(Video_Forms):
    vocal_path =  Vid_Mk(copymp4,vocal_path)
  Upld_File(vocal_path,rmvmessage)
  
  ########
  
def Pdf_Prepare():
  pdf = FPDF()
  pdf.add_page()
  pdf.set_draw_color(0, 0, 0) 
  pdf.set_line_width(3)
  #pdf.rect(10, 10, 190, 277)
  pdf.add_font('cal', '', 'cal.ttf', uni=True)
  pdf.set_font('cal', '', 20)
  return pdf 
  
def Text_Prepare_Pdf(Text):
  cleantextemoji = demoji.replace(str(Text),repl=" * ")
  cleantext = araby.strip_diacritics(cleantextemoji)
  if 'الله' in cleantext :
      cleantext = cleantext.replace('الله','اللـه')
  if '﵇' in cleantext :
      cleantext = cleantext.replace('﵇','')
  Text_Portions = []
  if '\n' in cleantext : 
    linelist = cleantext.split('\n')
    for line in linelist :
      if len(line) <= 75 :
          Text_Portions.append(line)
      else : 
        textlist = wrap(line,75)
        for line1 in textlist : 
          Text_Portions.append(line1)
  else : 
    if len(cleantext) <= 75 :
     Text_Portions.append(cleantext)
    else :
      textlist = wrap(cleantext,75)
      for line1 in textlist : 
        Text_Portions.append(line1)
  return Text_Portions
  
def Pdf_Text_Create(pdf,text):
  reshaped_text = arabic_reshaper.reshape(text)
  bidi_text = get_display(reshaped_text)
  pdf.multi_cell(185,13,bidi_text,0,'R')
    
def Insert_Text_Pdf(pdf,Text):
  Text_Portions = Text_Prepare_Pdf(Text) 
  for Por in Text_Portions : 
    Pdf_Text_Create(pdf,Por)  
  
def Txt_2_Pdf(Txt_File): 
 if Txt_File.startswith('.'):
     Ind = 1 
 else :
     Ind = 0
 Pdf_Fpdf_File = ('.' if Txt_File.startswith('.') else '') + Txt_File.split('.')[Ind] + '_Conv.pdf'
 Text = open(Txt_File,'r').read()
 Pdf = Pdf_Prepare()
 Insert_Text_Pdf(Pdf,Text+T_linebreak)
 Pdf.output(Pdf_Fpdf_File)
 return Pdf_Fpdf_File