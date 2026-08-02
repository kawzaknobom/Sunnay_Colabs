from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply,Message,ReplyKeyboardMarkup, KeyboardButton,ReplyKeyboardRemove
from pyrogram import Client, filters,StopTransmission,idle
from pyrogram.errors import FloodWait
from pyrogram.enums import MessageEntityType


from functools import reduce
import os,re,random, threading,time,subprocess,asyncio,shutil,img2pdf


from pypdf import PdfReader

from PIL import Image 
from pypdf import PdfWriter, PdfReader
import pypdfium2 as pdfium
from pdf2image import convert_from_path
from textwrap import wrap
from pdfCropMargins import crop
from math import ceil

from googletrans import Translator

Merge_Quee = {}
public_q =[]
Renm_L = []


#######

Bot_Token = '8016797331:AAEFGbZ9wWG5mI4Gomcxrskiis-yAzJEgog'
Api_Id = ''
Api_Hash = ''

def Pyrogram_Client(Bot_Token):
  Bot_Identifier = Bot_Token.split(':')[0]
  Session_file = Bot_Identifier+'_session_prm_bot'
  bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,bot_token=Bot_Token)
  return bot,Bot_Identifier
bot,Bot_Identifier = Pyrogram_Client(Bot_Token)

#####

Close_Loop = False

Public_Loop = False

main_dl_path = f'./downloads_{Bot_Identifier}/'


#### Bot Funcs ####

T_linebreak = '\n\n ◾ــــــــــــــ◾ \n\n'

Translate_Opts = [['ترجمة','Trans']]
Other_Opts = [['Zip','Zip']]
Photo_Options = [['دمج','IMerge'],['تلوين','Color'],['بلور','Blur'],['Ocr','Ocr']]  + Other_Opts + Translate_Opts
Photo_Multi_Options = ['IMerge','PMake']

Image_forms = (".jpg",".png",'.tif','webp')
g_langs = [ 'العربية | ar','الإنجليزية | en','الفرنسية | fr','الألمانية | de','العبرية iw  |  iw','العبرية he | he','اليونانية | el','الأمهرية | am','الباسك | eu','البنغالية | bn','البرتغالية  | pt','البلغارية | bg','الكتالانية | ca','الشيروكية | chr','الكرواتية | hr','التشيكية | cs','الدنماركية | da','الهولندية | nl','الإستونية | et','الفلبينية | fil','الفنلندية | fi','الغوجاراتية | gu','الهندية |  hi','المجرية | hu','الأيسلندية | is ','الإندونيسية | id','الإيطالية | it','اليابانية | ja','الكانادا  | kn','الكورية | ko','اللاتفية | lv','الليتوانية | lt','الماليزية |  ms','المالايالامية | ml','الماراثية |  mr','النرويجية | no','البولندية | pl','الرومانية | ro','الروسية | ru','الصربية | sr','الصينية  | zh-cn','الصينية TW | zh-tw','السلوفاكية | sk','السلوفينية | sl','الإسبانية | es','السواحيلية | sw','السويدية | sv','التاميلية | ta','التيلوغوية | te','التايلاندية | th','التركية|  tr','الأوردية | ur','الأوكرانية | uk','الفيتنامية | vi' ,'الويلزية | cy','الأفريكانية | af', 'الأرمينية | hy','الألبانية | sq','الأذريبيجانية | az','البيلاروسية | be','البوسنية | bs','السبيونوية | ceb','الشيشوانية | ny','الكورسيكية | co', 'الهولندية | nl','الاسبرانتو | eo','الاستوانية | et','الفلبينية | tl','الزولو | zu ','يوروبا | yo','اليديشية | yi','xhosa | xh','الأوزبكية | uz ','أويغور | ug','طاجيكية | tg','السودانية | su','الصومالية | so','السنهالية | si','السندية | sd','شونا | sn','سيسوتو | st','الغيلية | gd','ساموا | sm','رومانية | ro','بنجابية | pa' ,'فارسية | fa','باشتو | ps','أوديا | or','نرويجية | no' ,'نيبالية | ne','ميانمارية | my','منغولية | mn','ماورية | mi','مالطية | mt','قيرغيزستانية | ky','كردية | ku','الخميرية | km','الكازخستانية | kk','الجاوية | jw','الأيرلندية | ga','الإندونيسية | id', 'الإيغبو | ig', 'المجرية | hu', 'همونغ | hmn','هاواي | haw','هاوسا | ha','الكريولية | ht' ,'الجورجية | ka','الجاليكية | gl','الفريزية | fy','لاوية | lo', 'لاتينية | la', 'ليتوانية | lt', 'لوكسمبورغية | lb','المقدونية | mk', 'الملغاشية | mg']
Ex_Pdf_Limit = str(500)

Main_Contract = """
السلام عليكم ورحمة الله وبركاته 
`
♦️الوصف 

▪️ بوت متعدد الاستخدامات 

♦️ بنود الاستخدام 

▪️فيما لا يُخالف الشريعة الإسلامية ، لا أفلام أو أغاني أو كرتون 
▪️لعوام المسلمين عامة و لأهل السنة خاصة ، أهل الحديث والأثر ، [ لا للزنادقة خصوصاً الصوفية ] 
`
🛑 قال رسول الله ﷺ  « المسلمون على شروطهم » 

هل توافق على بنود الاستخدام ؟ 
"""
Usage_Button = [["نعم ","Yes"],["لا","No"] ]
Other_Opts = [['رفع لأرشيف','ToArch'],['Zip','Zip']]
Other_Options = [['تسمية','Renm'],['تفاصيل','Det']] + Other_Opts
Renm_msg = "الآن أدخل الاسم الجديد "
Compress_Op = [['ضغط','Compress']]
Trim_Op = [['قص','Trim']]
To_Pdf_Opt = [['Conv to Pdf ','2Pdf']]
Pdf_Options = [['دمج','PMerge'],['Ocr','Ocr'],['فك قفل طباعة','Unlock'],['بلا حواشي','Marg']]  + Trim_Op
Ppf_Opts = Pdf_Options + To_Pdf_Opt
Pdf_Txt_Option = Other_Options + Trim_Op + Translate_Opts + [['دمج','TMerge']]
Pdf_Image_Option = [['صنع بدف','PMake']]
Pdf_Multi_Options = ['PMerge']
Pdf_Refunc_Methods = ['Renm','Trim']
Pdf_Trim_Msg = """
🛑 الآن أرسل نقطة البداية والنهاية بهذه الصورة 
 start-end 

 ♦️ يمكنك إرسال أكتر من مدى 

 مثال | 1-5,7,8,13-16
"""

Txt_Trim_Msg = """
🛑 الآن أرسل جملة البداية والنهاية بهذه الصورة 
 startend 
"""

### Pdf Funcs ###


def Google_Trans_Txt(TxtFile,lang_sy='ar'):
  Txt_File = TxtFile.replace('.txt','_Translated.txt') 
  Check_File(Txt_File)
  Text = open(TxtFile,'r').read()
  Google_CTxt(TxtFile,Txt_File,Text,lang_sy,0,10000)
  return Txt_File


def Wrap_Text(text,num):
 if '\n' in text : 
  text= text.replace('\n','§')
 Text_list = wrap(text,num)
 for No,part in enumerate(Text_list) : 
  if '§' in part :
   Text_list[No] = part.replace('§','\n')
 return Text_list 

    
def Google_CTxt(TxtFile,Txt_File,Text,lang_sy,Req_Count=0,Limit=20000):
  rest = ''
  with open(Txt_File,'a') as f : 
    if len(Text) > Limit : 
      Textlist = Wrap_Text(Text,Limit)
      for Num,part in enumerate(Textlist) : 
        if len(rest.strip()) != 0 :
          part = rest + part
        if '.' in part :
          rest = part.split('.')[-1].strip()
          part = part[:-len(rest)-1]
        elif '\n' in part :
          rest = part.split('\n')[-1].strip()
          part = part[:-len(rest)-1]
        Txt_Part = TxtFile.replace('.txt',f'_P0000{Num}.txt') 
        open(Txt_Part,'a').write(part)
        Res_Text,Req_Count =  asyncio.run(Google_BTxt(Txt_Part,Req_Count,lang_sy))
        if Res_Text == 'None':
          Limit = Limit - 1000
          return Google_CTxt(TxtFile,Txt_File,Text,lang_sy,Req_Count,Limit)
        f.write(Res_Text)
        os.remove(Txt_Part)
    else : 
      Res_Text,Req_Count = asyncio.run(Google_BTxt(TxtFile,Req_Count,lang_sy))
      f.write(Res_Text)
      
def Rmv_Trans(Res):
  Res_Lines = Res.split('\n')
  for No,line in enumerate(Res_Lines) :
    if any(x in line for x in (  'ترجم', 'translat')):
     Res_Lines.pop(No)
  Res = '\n'.join(Res_Lines)
  return Res

async def Google_BTxt(TxtFile,Req_Count,lang_sy='ar') : 
  try : 
    Text = open(TxtFile,'r').read()
    translator = Translator()
    response = await translator.translate(Text, dest=lang_sy)
    if response.text == None :
      Req_Count += 1
      return 'None' ,Req_Count
    else :
      Res =  Rmv_Trans(response.text)
      Res = Res + T_linebreak + open(TxtFile,'r').read() + T_linebreak
      Req_Count += 1
      return Res,Req_Count
  except Exception as err : 
    Req_Count+=1
    if Req_Count%15 == 0 :
        time.sleep(60)
        return await Google_BTxt(TxtFile,Req_Count,lang_sy)


def is_int(val):
    try:
        int(val)
        return True
    except Exception as err :
      return False
    
def Get_Msg(bot,Chat_id,msg_id):
  try : 
     msg = bot.get_messages(int(Chat_id) if is_int(Chat_id) else str(Chat_id).replace('=','_'),int(msg_id))
     return msg
  except FloodWait as e :
      time.sleep(e.value)
      return Get_Msg(bot,Chat_id,msg_id)
  except Exception as err : 
      pass
  
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


def Upld_File(file,Msg,cap=' ',isogg=False):
  try:
    if file != None:
      if file.lower().endswith(Image_forms):
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

def Rmv_Dups(Dup_List):
   unique_list = []
   for i in Dup_List:
    if i not in unique_list:
      unique_list.append(i)
   return unique_list 

    
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

def Txt_Merge(FilesList):
  Res_File = FilesList[0].split('.')[0] + '_Merged.txt'
  with open(Res_File,'a') as f :
    for file in FilesList :
      Text = open(file,'r').read()
      f.write(Text+T_linebreak)
  return Res_File

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
  if File_Msg.audio or File_Msg.video or File_Msg.document  :
    if File_Msg.audio :
      file_name = File_Msg.audio.file_name
    elif File_Msg.video :
      file_name = File_Msg.video.file_name
    elif File_Msg.document :
      file_name = File_Msg.document.file_name
    if file_name == None :
      Name = File_Msg.id
      if File_Msg.audio : 
        Ex = 'mp3'
      elif File_Msg.video : 
        Ex = 'mp4'
    else :
      Splitted = file_name.split('.')
      Name = Splitted[0]
      Ex =  Splitted[1]
    custom_name = os.path.join(dl_path,f"{Name}_{random.randint(1,1000)}.{Ex}")
    File = File_Msg.download(file_name=custom_name)
  else :
    File = File_Msg.download(file_name=dl_path)
  return File 

def Zip_Func(dir):
  Zip_File = os.listdir(dir)[0].split('.')[0]
  shutil.make_archive(base_name=Zip_File,format='zip',root_dir=dir)
  return Zip_File + '.zip'


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


def Pdf_Margin(Pdf_File):
    Pdf_Cut_File, exit_code, stdout_str, stderr_str = crop(["-p4", "10", "10", "10", "10", Pdf_File],string_io=True, quiet=False)
    return Pdf_Cut_File
  
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
  
########

def Get_File(Dl_Dir,File_Ex):
  for file in os.listdir(Dl_Dir):
    if file.lower().endswith(File_Ex):
      return os.path.abspath(Dl_Dir + file)
  return None

      
def Ocr_Func(Ocr_Path):
  Serv_Acc = os.environ['Service_Acc']
  ServAcc_File = 'servac.json'
  open(ServAcc_File,'w').write(Serv_Acc)
  Dir_Path = ('.' if Ocr_Path.startswith('.') else '') + '/'.join(Ocr_Path.split('/')[:-1]) + '/'
  Tahweel_Cmd = f'''tahweel "{Ocr_Path}" \
    --service-account-credentials "{ServAcc_File}" \
    --pdf2image-thread-count 8 \
    --processor-max-workers 8 \
    --txt-page-separator 🟥 '''
  p = subprocess.Popen(Tahweel_Cmd,cwd=Dir_Path,shell=True)
  p.wait()
  Txt_File = Get_File(Dir_Path,'txt')
  Docx_File = Get_File(Dir_Path,'docx')
  return Txt_File,Docx_File

  
def Callback_Add(CallbackQuery):
  Quee = public_q
  replied = CallbackQuery.edit_message_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
  Item = CallbackQuery.data + f'_{replied.id}_{CallbackQuery.from_user.id}'
  Item_add(Item)

def Item_add(Item):
  User_Id = int(Item.split("_")[-1])
  Quee = public_q
  Quee.append(Item)
  loop_name = "Public_Loop"
  if not globals()[loop_name] :	
    globals()[loop_name] = True
    Multi_loop()
    
def Pdf_Cases(Case,File,Msg):
  if any(x in Case for x in ('-','/')):
    if '-' in Case : 
      Sep =  '-' 
    elif '/' in Case : 
      Sep =  '/' 
    point_list = Case.split(Sep) 
    Start = int(point_list[0])
    End = int(point_list[1])
    Pdf_File = Pdf_Trim(File,Start,End)
    cap =  ( f"`{Start}` to `{End}`")
    Upld_File(Pdf_File,Msg,cap)
  else : 
    Pdf_File = Pdf_Page(File,int(Case))
    Extract_Dir = Pdf_Extract(Pdf_File)
    Msgs_List = Upld_Dir_Func(Extract_Dir,Msg)
 
def Universal_Concat(message,Merge_Quee,Method):
      User_Id = message.from_user.id
      Merge_Quee[Method][1].append(str(message.id))
      method = Method.split('_')[0]
      if method == 'Zip' :
        Word = 'الملفات'
        Cmd = '/Z_Finish'
        C_Cmd = '/Z_Clear'
      else :
        if message.photo : 
          Word = 'الصور'
          if method == 'IMerge' :
            Cmd = '/IM_Finish'
            C_Cmd = '/IM_Clear'
          else :
            Cmd = '/IP_Finish'
            C_Cmd = '/IP_Clear'
        

        elif message.document : 
          if message.document.file_name.lower().endswith(Image_forms) : 
            Word = 'الصور'
            if method == 'IMerge' :
              Cmd = '/IM_Finish'
              C_Cmd = '/IM_Clear'
            else :
              Cmd = '/IP_Finish'
              C_Cmd = '/IP_Clear'
          elif message.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')) : 
            Word = 'الملفات'
            Cmd = '/P_Finish'
            C_Cmd = '/P_Clear'
          
          elif message.document.file_name.lower().endswith('txt') : 
            Word = 'الملفات'
            Cmd = '/T_Finish'
            C_Cmd = '/T_Clear'
            
      M_Text = f"""
      ▪️عدد {Word} 👈 {len(Merge_Quee[Method][1])} ملفاً
      ▪️بعد الانتهاء اضغط الأمر 
      {Cmd}
      ▪️لإلغاء عملية الدمج ، اضغط الأمر 
      {C_Cmd}
      """
      Replied_Msg = Get_Msg(bot,User_Id,Merge_Quee[Method][0][0])
      Replied_Msg.edit_text(M_Text)

###### Main Loop ####

def reload_loop(process):
      if process in public_q :
        msg_list = process.split('_')
        rp_msg_id = int(msg_list[-2])
        user_id = int(msg_list[-1])
        reply_msg = Get_Msg(bot,user_id,rp_msg_id)
        File_Msg = Get_Msg(bot,user_id,msg_list[1])
        try : 
            reply_msg.edit_text("لقد تخطيت الحد الزمني الأقصى للطلب ( 30 دقيقة )")
        except :
          reply_msg.delete()
          reply_msg = File_Msg.reply("لقد تخطيت الحد الزمني الأقصى للطلب ( 30 دقيقة )")
        del public_q[0]
        thread = threading.Thread(target=Multi_loop, args=["MainQ"])
        thread.start()

def Multi_loop():
  Multi_Q = public_q
  dl_path = f'./downloads_{Bot_Identifier}/'
  for obj in range (0,len(Multi_Q)) :
   timer = threading.Timer(1800, reload_loop, args=[public_q[0]])
   timer.start()

   for elem in range (1,len(Multi_Q)) :
        try :
         A_Reply_List = Multi_Q[elem].split('_')
         A_rp_msg_id = A_Reply_List[-2]
         A_user_id = A_Reply_List[-1]
         A_reply = Get_Msg(bot,A_user_id,A_rp_msg_id)
         A_reply.edit_text(f"تمت الإضافة للصف \n\n ترتيبك هو {elem} ☕ ")
        except :
          pass
   try :
    C_Process = Multi_Q[0]
    msg_list = C_Process.split('_')
    msg_id = msg_list[1]
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    process = msg_list[0]
    rp_msg_id = int(msg_list[-2])
    user_id = int(msg_list[-1])
    reply_msg = Get_Msg(bot,user_id,rp_msg_id)
    File_Msg = Get_Msg(bot,user_id,msg_id)
    File_Name = Get_Name(File_Msg)
    if any(x in File_Name for x in ('أحمد السيد','أحمد_السيد','احمد_السيد','احمد السيد')) :
        reply_msg.edit_text('آسف ، لا أخدم لـ [أحمد السيد](https://telegra.ph/من-هو-أحمد-السيد-03-26) 🌿',disable_web_page_preview=True)
    else :
      try : 
        reply_msg.edit_text(f"جار العمل  ☕")
      except :
        reply_msg.delete()
        reply_msg = File_Msg.reply('جار العمل ☕')
      if process == 'Det' :
        if File_Msg.audio :
          Size = File_Msg.audio.file_size
        elif File_Msg.voice :
          Size = File_Msg.voice.file_size
        elif File_Msg.video :
          Size = File_Msg.video.file_size
        elif File_Msg.document :
          Size = File_Msg.document.file_size
        Details =  f"اسم الملف : \n {File_Name} \n حجم الملف : \n {round(int(Size)/(1024*1024),2)} ميغا بايت  "
        reply_msg.reply(Details)
        
      elif process in ['PMerge','IMerge','PMake','Zip','TMerge'] : 
        
        Files_Ids = msg_list[1:-2]
        if process == 'IMerge' :
          Files_Ids = msg_list[1:-3]
        Process_List = Multi_Op_Dl(bot,dl_path,Files_Ids,user_id)
        if process == 'PMerge' : 
          Res_File = Pdf_Merge(Process_List)
        elif process == 'TMerge':
          Res_File = Txt_Merge(Process_List)
            

        elif process == 'IMerge' :
         if len(Process_List) < 11 :
          if msg_list[-3] == 'SBS':
            Merge_Mode = Merge_Images_SBS
          else : 
            Merge_Mode = Merge_Images_UP
          Res_File = reduce(Merge_Mode,Process_List)
          File_Msg.reply_document(Res_File)
         else :
           File_Msg.reply('غير مسموح بأكثر من عشر صور ')
          
        elif process == 'PMake' : 
         Res_File = Pdf_Make(Process_List)
        elif process == 'Zip' :
          Res_File = Zip_Func(dl_path)
         
        Upld_File(Res_File,File_Msg)
        if process == 'Zip' :
          os.remove(Res_File)
      
      else :
       Rate = msg_list[2]
       if not (File_Msg.photo or File_Msg.video or File_Msg.audio or File_Msg.voice or (File_Msg.document and not File_Msg.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx'))) or (File_Msg.document and File_Msg.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')) and int(int(File_Msg.document.file_size)/(1024*1024)) <= 500 )) :
        File_Msg.reply(f'حد الملف {Ex_Pdf_Limit} ميغا')
       else : 
         File = File_Dl(File_Msg,dl_path)
         if process == 'Trim' :
           if '|' in Rate : 
              Rate = Rate.replace('|',' ')
           if File.lower().endswith(('pdf')) :

            if any(x in Rate for x in [',','،']):
             if ',' in Rate : 
                splitor = ','
             else : 
                splitor = '،'
             Cases = Rate.split(splitor)
             for Case in Cases : 
               Pdf_Cases(Case,File,File_Msg)
            else : 
             Pdf_Cases(Rate,File,File_Msg)

           elif File.lower().endswith('txt'):
             Phrase_List = Rate.split('~')
             Start_ph = Phrase_List[0]
             End_ph = Phrase_List[-1]
             Res_File = Txt_Trim(File,Start_ph,End_ph)
             Upld_File(Res_File,File_Msg)
                    
         elif process == 'Ex':
          
            if File.lower().endswith(('.pdf')):
                  Extract_Dir = Pdf_Extract(File)
                  Msgs_List = Upld_Dir_Func(Extract_Dir,File_Msg)

         elif process in ['Ocr','Trans']:
            
            if File.lower().endswith('txt'):
              Txt_File = File
            else :
              if File.endswith('PDF'):
                os.rename(File,File.lower())
                File = File.lower()
              Txt_File,Docx_File = Ocr_Func(File)
          

            if File.lower().endswith(Image_forms):
              Send_Text_Res(File_Msg,open(Txt_File,'r').read())
            else :
              File_Msg.reply_document(Txt_File)
              if process == 'Ocr' :
                File_Msg.reply_document(Docx_File)
         
  
         elif process in ('Compress','Marg','Unlock','Renm') :
              
              if process == 'Renm':
               Ext = File.split('.')[-1]
               Res_File = f"{dl_path}{Rate.replace('|',' ')}.{Ext}"
               Cmd = f'mv "{File}" "{Res_File}"'
               os.system(Cmd)

              elif process == 'Marg' :
               if Pdf_Page_Num(File) < Ex_Pdf_Limit : 
                Res_File = Pdf_Margin(File)
               else :
                  File_Msg.reply(f'حد الملف {Ex_Pdf_Limit} ميغا')
              elif process == 'Unlock' :
               
                if Pdf_Page_Num(File) < Ex_Pdf_Limit : 
                  Res_File = Unlock_Pdf(File)
                else :
                    File_Msg.reply(f'حد الملف {Ex_Pdf_Limit} صفحة')
              elif process == 'Compress' :
                if File.lower().endswith('pdf'):
                  Res_File = Pdf_Compress(bot,dl_path,File)
              
      try :
        reply_msg.edit_text('تمت  ☑️')
      except :
        pass
      Check_Dir(dl_path)
   except Exception as err :
       try : 
        reply_msg.edit_text(err)
       except : 
         pass
   if C_Process in Multi_Q : 
    globals()['Close_Loop'] = False
    del Multi_Q[0]
   else :
    globals()['Close_Loop'] = True
    break
  if not globals()['Close_Loop'] :
    if len(Multi_Q) != 0 :
        return Multi_loop()
    else :
      loop_name = "Public_Loop"
      if globals()[loop_name] :	
        globals()[loop_name] = False

###### Bot Funcs #####

@bot.on_message((filters.command('P_Clear') | filters.command('IM_Clear') | filters.command('A_Clear') | filters.command('V_Clear') | filters.command('IP_Clear') | filters.command('Z_Clear') | filters.command('T_Clear') ) & filters.private)
def command1(bot,message):
  
   User_Id = message.from_user.id
   if message.text.strip() == '/P_Clear' : 
     Method = 'PMerge'
     Key = f'{Method}_{User_Id}'
     
   elif message.text.strip() == '/IM_Clear': 
     Method = 'IMerge'
     Key = f'{Method}_{User_Id}'
    
   elif message.text.strip() == '/IP_Clear': 
    Method = 'PMake'
    Key = f'{Method}_{User_Id}'
    
   elif message.text.strip() == '/A_Clear':
     Method = 'AMerge'
     Key = f'{Method}_{User_Id}'
    
   elif message.text.strip() == '/V_Clear':
     Method = 'VMerge'
     Key = f'{Method}_{User_Id}'

   elif message.text.strip() == '/T_Clear':
     Method = 'TMerge'
     Key = f'{Method}_{User_Id}'

   elif message.text.strip() == '/Z_Clear':
     Method = 'Zip'
     Key = f'{Method}_{User_Id}'

   Reply_Id = Merge_Quee[Key][0][0]
   Replied_Msg = Get_Msg(bot,User_Id,Reply_Id)
   Replied_Msg.edit_text('تم الإلغاء ✅')
   del Merge_Quee[Key]


@bot.on_message((filters.command('P_Finish') | filters.command('IM_Finish') | filters.command('A_Finish') | filters.command('V_Finish') | filters.command('IP_Finish') | filters.command('Z_Finish') | filters.command('T_Finish') ) & filters.private)
def command1(bot,message):
  
   User_Id = message.from_user.id
   if message.text.strip() == '/P_Finish' : 
     Method = 'PMerge'
     Key = f'{Method}_{User_Id}'
     
   elif message.text.strip() == '/IM_Finish': 
     Method = 'IMerge'
     Key = f'{Method}_{User_Id}'
    
   elif message.text.strip() == '/IP_Finish': 
    Method = 'PMake'
    Key = f'{Method}_{User_Id}'
    
   elif message.text.strip() == '/A_Finish':
     Method = 'AMerge'
     Key = f'{Method}_{User_Id}'

   elif message.text.strip() == '/V_Finish':
     Method = 'VMerge'
     Key = f'{Method}_{User_Id}'

   elif message.text.strip() == '/T_Finish':
     Method = 'TMerge'
     Key = f'{Method}_{User_Id}'
   
   elif message.text.strip() == '/Z_Finish':
     Method = 'Zip'
     Key = f'{Method}_{User_Id}'

   Replied_Msg_id = Merge_Quee[Key][0][0]
   Replied_Msg = Get_Msg(bot,User_Id,Replied_Msg_id)
   if len(Merge_Quee[Key][1]) < 2 and not Method in ('PMake','Zip') :
        Replied_Msg.edit_text("لقد أرسلت ملفاً واحداً فقط !")
        return
   else :
     if Method == 'IMerge':
        Replied_Msg.delete()
        MERGE_MODE_IMAGE = "اختر نمط الدمج "
        Merge_Modes = [['أفقياً','SBS'],['رأسياً','UD']]
        MERGE_MODE_Buttons = []
        for Mod in Merge_Modes : 
         MERGE_MODE_Buttons.append([InlineKeyboardButton(Mod[0],callback_data=f'IMerge_{Mod[1]}_{message.from_user.id}')])
        message.reply(text = MERGE_MODE_IMAGE,reply_markup = InlineKeyboardMarkup(MERGE_MODE_Buttons))
     else :
      Quee = public_q 
      replied = Replied_Msg.edit_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
      Key = f'{Method}_{message.from_user.id}'
      Msgs_ids = '_'.join(Merge_Quee[Key][1])
      Item = f"{Method}_{Msgs_ids}_{replied.id}_{message.from_user.id}"
      del Merge_Quee[Key]
      Item_add(Item)
      

@bot.on_message(filters.command('start') & filters.private)
def command1(bot,message):
   User_Id = message.from_user.id
   message.reply('لبقية البوتات \n\n @sunnay6626')
   #My_Db.Insert_User(message.from_user.id)
  
#####

@bot.on_message(filters.private & filters.incoming & (filters.photo | filters.audio | filters.voice | filters.video | filters.document ))
def _telegram_file(client, message):
    
  User_Id = message.from_user.id
  Zip_Key = f'Zip_{User_Id}'
  IMerge_Key = f'IMerge_{User_Id}'
  Pmake_Key = f'PMake_{User_Id}'
  PMerge_Key = f'PMerge_{User_Id}'
  TMerge_Key = f'TMerge_{User_Id}'
  if Zip_Key in list(Merge_Quee.keys()):
    Universal_Concat(message,Merge_Quee,Zip_Key)
    return
  else :
      
    if IMerge_Key in list(Merge_Quee.keys()):
     if message.photo or message.document.file_name.lower().endswith(Image_forms):
      Universal_Concat(message,Merge_Quee,IMerge_Key)
      return
    elif PMerge_Key in list(Merge_Quee.keys()):
     if message.document.file_name.lower().endswith('pdf'):
      Universal_Concat(message,Merge_Quee,PMerge_Key)
      return
    elif Pmake_Key in list(Merge_Quee.keys()):
     if message.photo or message.document.file_name.lower().endswith(Image_forms):
      Universal_Concat(message,Merge_Quee,Pmake_Key)
      return
    elif TMerge_Key in list(Merge_Quee.keys()):
     if message.document.file_name.lower().endswith('txt') :
      Universal_Concat(message,Merge_Quee,TMerge_Key)
      return

  if message.photo : 
      Options =  Photo_Options + Pdf_Image_Option
   
  elif message.document : 
   
   if message.document.file_name.lower().endswith(Image_forms) : 
      Options = Photo_Options + Pdf_Image_Option
   
   elif message.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')) : 
       if message.document.file_name.lower().endswith('pdf'):
        Options = Pdf_Options
       else :
         Options = Ppf_Opts
   
   elif message.document.file_name.lower().endswith('txt') : 
     
     Options = Pdf_Txt_Option
   
   else :
     Options = Other_Options
     
  CHOOSE_UR_BUTTONS = []
  CHOOSE_UR_Option = "اختر ما تريد "
  for Index,option in enumerate(Options) : 
    if Index > 6 : 
      CHOOSE_UR_BUTTONS[(Index-1)%6].append(InlineKeyboardButton(option[0],callback_data=option[1]+'_'+str(message.id)))
    else : 
     CHOOSE_UR_BUTTONS.append([InlineKeyboardButton(option[0],callback_data=option[1]+'_'+str(message.id))])
     
  CHOOSE_UR_BUTTONS = Rmv_Dups(CHOOSE_UR_BUTTONS)
  message.reply(text = CHOOSE_UR_Option,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))
 
#####################################

callback_dict = {}

@bot.on_callback_query()
def callback_query(CLIENT,CallbackQuery):
  User_Id = CallbackQuery.from_user.id
  Quee = public_q
  Callback_List = CallbackQuery.data.split('_')
  Method = Callback_List[0]
  Msg_Id = Callback_List[1]
  if not Msg_Id in ('SBS','UD'):
    file_msg = Get_Msg(bot,User_Id,Msg_Id)
  if Method == 'Yes':
    CallbackQuery.edit_message_text("أهلا بك 🌿 ")

  elif Method in ('PMake','PMerge','IMerge','Zip','TMerge') :
    if Method == 'PMerge':
      Word = 'الملفات'
      Cmd = '/P_Finish'
      C_Cmd = '/P_Clear'
    elif Method == 'Zip':
      Word = 'الملفات'
      Cmd = '/Z_Finish'
      C_Cmd = '/Z_Clear'
    elif Method == 'TMerge':
      Word = 'الملفات'
      Cmd = '/T_Finish'
      C_Cmd = '/T_Clear'
    elif Method == 'IMerge':
     if Msg_Id in ('SBS','UD') :
      replied = CallbackQuery.edit_message_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
      Key = f'IMerge_{User_Id}'
      Msgs_ids = '_'.join(Merge_Quee[Key][1])
      Item = f"IMerge_{Msgs_ids}_{Msg_Id}_{replied.id}_{User_Id}"
      Item_add(Item)
      del Merge_Quee[Key]
      return
     else :
      Word = 'الصور'
      Cmd = '/IM_Finish'
      C_Cmd = '/IM_Clear'
    
    elif Method == 'PMake':
      Word = 'الصور'
      Cmd = '/IP_Finish'
      C_Cmd = '/IP_Clear'
      
    Key = f'{Method}_{User_Id}'
    if Key in list(Merge_Quee.keys()):
     del Merge_Quee[Key]
    Merge_Quee[Key] = [[],[Callback_List[-1]]]
    M_Text = f"""
      ▪️عدد {Word} 👈 {len(Merge_Quee[Key][1])} ملفاً
      ▪️بعد الانتهاء اضغط الأمر 
      {Cmd}
      ▪️لإلغاء عملية الدمج ، اضغط الأمر 
      {C_Cmd}
      """
    Replied = CallbackQuery.edit_message_text(M_Text)
    Merge_Quee[Key][0].append(Replied.id)
  

  elif Method in ['Compress'] :           
        if file_msg.document.file_name.lower().endswith('pdf'):
          replied = CallbackQuery.edit_message_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
          File_Id = Callback_List[-1]
          Item = f"{Method}_{File_Id}_{replied.id}_{User_Id}"
          Item_add(Item)      
    
  elif Method in ('Trim','Renm'):
   bot.delete_messages(User_Id,CallbackQuery.message.id)
   if Method == 'Renm' :
     Renm_L.append(User_Id)
     Text = Renm_msg
   elif Method == 'Trim' :
     if file_msg.document :
       if file_msg.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')):
         Text = Pdf_Trim_Msg
       elif file_msg.document.file_name.lower().endswith('txt'):
        Text = Txt_Trim_Msg
   
   file_msg.reply_text(Text,reply_markup=ForceReply(True),reply_to_message_id=file_msg.id)
  
  elif Method in ('Ocr','2Pdf','Det','Ex','Marg','Unlock') :
   
    replied = CallbackQuery.edit_message_text(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
    File_Id = Callback_List[-1]
    Item = f"{Method}_{File_Id}_{replied.id}_{User_Id}"
    Item_add(Item)
 
##################################

@bot.on_message(filters.private & filters.reply)
def refunc(client,message):
   if (message.reply_to_message.reply_markup) and isinstance(message.reply_to_message.reply_markup, ForceReply)  :
    User_Id = message.from_user.id
    Msg_Text = message.text
    reply_id = message.reply_to_message_id
    reply_msg = Get_Msg(bot,User_Id,reply_id)
    file_id = reply_msg.reply_to_message_id
    file_msg = Get_Msg(bot,User_Id,file_id)
    message.delete()
  
    ReplyMsg_Text = reply_msg.text
    reply_msg.delete()
    Quee = public_q
    replied = file_msg.reply(f"تمت الإضافة للصف  \n\n ترتيبك هو {len(Quee)+1} ☕ ")
    Pdf_Trim_Pattern = r"^\d+(?:[,-/]\d+(?:-\d+)?)*$"
    
    if User_Id in Renm_L :
      Process = 'Renm'
      Text = Msg_Text.replace(' ','|')
      Renm_L.remove(User_Id)

    elif re.search(Pdf_Trim_Pattern,Msg_Text) or '~' in Msg_Text  :
        Process = 'Trim'
        Text = Msg_Text.strip()
        if ' ' in Text:
          Text = Msg_Text.replace(' ','|')

    Item = f"{Process}_{file_id}_{Text}_{replied.id}_{User_Id}"
    Item_add(Item)

##############


def main():
    try:
        bot.start()
        print("✅ pdf Bot is ONLINE!")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()