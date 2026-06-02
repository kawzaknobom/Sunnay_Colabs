import nest_asyncio,os
nest_asyncio.apply()

#########################################################

Bot_Token = os.getenv('TOKEN')

########################################################

from pyrogram.types import InlineKeyboardMarkup , InlineKeyboardButton , CallbackQuery , ForceReply,Message
from pyrogram import Client, filters

from functools import reduce
import os,re,random, threading 

from cookies_nodb import Image_forms,Video_Forms,Audio_Forms,Video_Options,Audio_Options,Aud_Comp_Buttons,Amplify_Buttons,Speed_Buttons,Slow_Buttons,Media_Trim_Msg,Renm_msg,Photo_Options,Photo_Multi_Options,Photo_Blur_buttons,Color_button,Pdf_Options,Pdf_Txt_Option,Pdf_Image_Option,Pdf_Multi_Options,Pdf_Refunc_Methods,Pdf_Trim_Msg,Txt_Trim_Msg,Renm_msg,Audio_Multi_Options,Other_Options,Cbx_Option,Vid_Cov_Ops,Main_Contract,Usage_Button,Epub_Opts,Ex_Pdf_Limit,Ppf_Opts

from common_func_nodb import Color_Pic,Pdf_Extract,Pdf_Page,Pdf_Trim,Pdf_Make,Pyrogram_Client,Check_File,Check_Dir,Pdf_Merge,Ocr_Func,Pdf_Margin,Upld_Dir_Func,Color_Pdf,Txt_2_Pdf,Unlock_Pdf,Rmv_Dups,Zip_Extract,Grap_PicDir,Merge_Images_UP,Merge_Images_SBS,Blur_Func,Mp3_Conv,Media_Amplify,Media_Change,Media_Skip,Media_Compress,Media_Speed,Media_Trim,Upld_File,Send_Text_Res,Aud_Merge,Encode_Vid,Vid_Mon,Dur_Get,Media_F_func,Send_TRes,Get_Name,Get_Msg,File_Dl,Epub_Extract_Func,Pdf_Page_Num,Mute_Video,Sub_Aud,PPF2PDF,Mdx2PDf,Pdf_Compress,Multi_Op_Dl,Txt_Trim,upld2arch,delarch_file,Zip_Func,Vid_Merge,Aud_Scatter,Msg_Dur,Get_Stream_Dur,Music_Rmv,Gemini_Trans_Txt,Gemini_Transcribe

from pypdf import PdfReader

Delete_Downloads = r"find . -maxdepth 1 -type d -name 'downloads*' -exec rm -rf {} +"
os.system(Delete_Downloads)

Merge_Quee = {}

#######

bot,Bot_Identifier = Pyrogram_Client(Bot_Token)

#####

Public_Loop = False
Private_Loop = False

main_dl_path = f'./downloads_{Bot_Identifier}/'


#### Bot Funcs ####

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
        
        elif message.audio or message.voice :
          Word = 'الصوتيات'
          Cmd = '/A_Finish'
          C_Cmd = '/A_Clear'
        
        elif message.video :
          Word = 'الفيديوهات'
          Cmd = '/V_Finish'
          C_Cmd = '/V_Clear'

        elif message.document : 
          if message.document.file_name.lower().endswith(Image_forms) : 
            Word = 'الصور'
            if method == 'IMerge' :
              Cmd = '/IM_Finish'
              C_Cmd = '/IM_Clear'
            else :
              Cmd = '/IP_Finish'
              C_Cmd = '/IP_Clear'
          elif message.document.file_name.lower().endswith(Audio_Forms) : 
            Word = 'الصوتيات'
            Cmd = '/A_Finish'
            C_Cmd = '/A_Clear'
          elif message.document.file_name.lower().endswith(Video_Forms) : 
            Word = 'الفيديوهات'
            Cmd = '/V_Finish'
            C_Cmd = '/V_Clear'
          elif message.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')) : 
            Word = 'الملفات'
            Cmd = '/P_Finish'
            C_Cmd = '/P_Clear'
            
      M_Text = f"""
      ▪️عدد {Word} 👈 {len(Merge_Quee[Method][1])} ملفاً
      ▪️بعد الانتهاء اضغط الأمر 
      {Cmd}
      ▪️لإلغاء عملية الدمج ، اضغط الأمر 
      {C_Cmd}
      """
      Replied_Msg = Get_Msg(bot,User_Id,Merge_Quee[Method][0][0])
      Replied_Msg.edit_text(M_Text)

def New_Member(message):
   CHOOSE_UR_BUTTONS = []
   for option in Usage_Button :
    CHOOSE_UR_BUTTONS.append([InlineKeyboardButton(option[0],callback_data=option[1]+'_'+str(message.id))])
   CHOOSE_UR_BUTTONS = Rmv_Dups(CHOOSE_UR_BUTTONS)
   message.reply(text = Main_Contract,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))
    

###### Main Loop ####

# multi_methods = Multi_Method()

class Multi_Method():
  
  def Det(self,msg_id,user_id):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    File_Name = Get_Name(File_Msg)
    if File_Msg.audio :
          Size = File_Msg.audio.file_size
    elif File_Msg.voice :
        Size = File_Msg.voice.file_size
    elif File_Msg.video :
        Size = File_Msg.video.file_size
    elif File_Msg.document :
        Size = File_Msg.document.file_size
    Details =  f"اسم الملف : \n {File_Name} \n حجم الملف : \n {round(int(Size)/(1024*1024),2)} ميغا بايت  "
    File_Msg.reply(Details)
  
  def IMerge(self,msg_id,user_id,mode):
    msg_ids = msg_id.split("_")
    File_Msg = Get_Msg(bot,user_id,msg_ids[0])
    dl_path = f'./downloads_{msg_ids[0]}_{Bot_Identifier}/'
    Process_List = Multi_Op_Dl(bot,dl_path,msg_ids,user_id)
    if len(Process_List) < 11 :
        if mode == 'SBS':
            Merge_Mode = Merge_Images_SBS
        else : 
            Merge_Mode = Merge_Images_UP
        Res_File = reduce(Merge_Mode,Process_List)
        File_Msg.reply_document(Res_File)
        Upld_File(Res_File,File_Msg)
        Check_Dir(dl_path)
    else :
      File_Msg.reply('غير مسموح بأكثر من عشر صور ')
          
  def Zip(self,msg_id,user_id):
    msg_ids = msg_id.split("_")
    File_Msg = Get_Msg(bot,user_id,msg_ids[0])
    dl_path = f'./downloads_{msg_ids[0]}_{Bot_Identifier}/'
    Process_List = Multi_Op_Dl(bot,dl_path,msg_ids,user_id)
    Res_File = Zip_Func(dl_path)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)
  
  def PMerge(self,msg_id,user_id):
    msg_ids = msg_id.split("_")
    File_Msg = Get_Msg(bot,user_id,msg_ids[0])
    dl_path = f'./downloads_{msg_ids[0]}_{Bot_Identifier}/'
    Process_List = Multi_Op_Dl(bot,dl_path,msg_ids,user_id)
    Res_File = Pdf_Merge(Process_List)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)

  def AMerge(self,msg_id,user_id):
    msg_ids = msg_id.split("_")
    File_Msg = Get_Msg(bot,user_id,msg_ids[0])
    dl_path = f'./downloads_{msg_ids[0]}_{Bot_Identifier}/'
    Process_List = Multi_Op_Dl(bot,dl_path,msg_ids,user_id)
    mergtxt = Process_List[0].split('.')[0] + '.txt'
    for File_Elm in Process_List :
        mp3_path = Mp3_Conv(File_Elm)
        open(mergtxt,'a').write(f"file '{mp3_path}' \n")
    Res_File = Aud_Merge(mergtxt)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)

  def VMerge(self,msg_id,user_id):
    msg_ids = msg_id.split("_")
    File_Msg = Get_Msg(bot,user_id,msg_ids[0])
    dl_path = f'./downloads_{msg_ids[0]}_{Bot_Identifier}/'
    Process_List = Multi_Op_Dl(bot,dl_path,msg_ids,user_id)
    mergtxt = Process_List[0].split('.')[0] + '.txt'
    for File_Elm in Process_List :
        Main_Dir = ('.' if File_Elm[0] == '.' else '' ) + ('/'.join(File_Elm.split('/')[:-1])) + '/'
        New_Name = f"Vid_{random.randint(0,1000)}.mp4"
        New_File = Main_Dir+New_Name
        os.rename(File_Elm,New_File)
        open(mergtxt,'a').write(f"file '{New_File}' \n")
    Res_File = Vid_Merge(mergtxt)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)
    
  def PMake(self,msg_id,user_id):
    msg_ids = msg_id.split("_")
    File_Msg = Get_Msg(bot,user_id,msg_ids[0])
    dl_path = f'./downloads_{msg_ids[0]}_{Bot_Identifier}/'
    Process_List = Multi_Op_Dl(bot,dl_path,msg_ids,user_id)
    Res_File = Pdf_Make(Process_List)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)
  
  def SubAud(self,msg_id,user_id):
    msg_ids = msg_id.split("_")
    File_Msg = Get_Msg(bot,user_id,msg_ids[0])
    dl_path = f'./downloads_{msg_ids[0]}_{Bot_Identifier}/'
    Process_List = Multi_Op_Dl(bot,dl_path,msg_ids,user_id)
    for item in Process_List :
      if item.lower().endswith(Video_Forms):
        Vid = item 
      else :
        Aud = item 
    Res_File = Sub_Aud(Vid,Aud)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)
  
  def Montaj(self,msg_id,user_id):
    msg_ids = msg_id.split("_")
    File_Msg = Get_Msg(bot,user_id,msg_ids[0])
    dl_path = f'./downloads_{msg_ids[0]}_{Bot_Identifier}/'
    Process_List = Multi_Op_Dl(bot,dl_path,msg_ids,user_id)
    for item in Process_List :
      if item.lower().endswith(Image_forms):
        Img = item 
      else :
        Aud = item 
    Mp3_Path = Mp3_Conv(Aud)
    Res_File,Thumbnail = Vid_Mon(Img,Mp3_Path)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)
  
  def Trim(self,msg_id,user_id,Rate):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    if '|' in Rate : 
      Rate = Rate.replace('|',' ')

    if File.lower().endswith(('pdf','ppt','pptx','mdx')) :
            if File.lower().endswith(('ppt','pptx')) :
              File = PPF2PDF(File)
            elif File.lower().endswith(('mdx')) :
              File = Mdx2PDf(File)
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
    else :
    
             if ' ' in Rate : 
               Parts = Rate.split(" ")
               for part in Parts : 
                Res_File = Media_Trim(File,part)
                start = part.split('-')[0]
                End = part.split('-')[1]
                cap =  ( f"`{start}` to `{End}`")
                Upld_File(Res_File,File_Msg,cap)
             else :
               Res_File = Media_Trim(File,Rate)
               start = Rate.split('-')[0]
               End = Rate.split('-')[1]
               cap =  ( f"`{start}` to `{End}`")
               Upld_File(Res_File,File_Msg,cap)
    Check_Dir(dl_path)

  def Ex(self,msg_id,user_id):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    if File.lower().endswith('.epub'):
            Txt_File = Epub_Extract_Func(File)
            Upld_File(Txt_File,File_Msg)
    else :
            if File.lower().endswith(('.pdf','ppt','pptx','mdx')):
                  if File.lower().endswith(('ppt','pptx')) :
                    File = PPF2PDF(File)
                  elif File.lower().endswith(('mdx')) :
                    File = Mdx2PDf(File)
                  Extract_Dir = Pdf_Extract(File)
                  Msgs_List = Upld_Dir_Func(Extract_Dir,File_Msg)
            elif File.lower().endswith(('cbz','cbr','zip','rar')) :
              Extract_Dir = Zip_Extract(File)
              Msgs_List = Upld_Dir_Func(Extract_Dir,File_Msg)
    Check_Dir(dl_path)

  def Ocr(self,msg_id,user_id,getback=False):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    if File.endswith('PDF'):
                os.rename(File,File.lower())
                File = File.lower()
    elif File.lower().endswith(('ppt','pptx')) :
                File = PPF2PDF(File)
    elif File.lower().endswith(('mdx')) :
                 File = Mdx2PDf(File)
    Txt_File,Docx_File = Ocr_Func(File)
    if getback :
      return Txt_File,File_Msg,dl_path
    else :
      if File.lower().endswith(Image_forms):
              Send_Text_Res(File_Msg,open(Txt_File,'r').read())
      else :
            Upld_File(Txt_File,File_Msg)
      Upld_File(Docx_File,File_Msg)
      Check_Dir(dl_path)
  
  def Trans(self,msg_id,user_id,model,lang):
    Txt_File,File_Msg,dl_path = self.Ocr(msg_id,user_id,True)
    if model == 'Gemini':
      try:
                Txt_File = Gemini_Trans_Txt(Txt_File,lang)
                Upld_File(Txt_File,File_Msg)
                Send_Text_Res(File_Msg,open(Txt_File,'r').read())
      except Exception as err :
                 TxtFile = Txt_File.split('.')[0] + '_Translated.txt'
                 Rest_File = Txt_File.split('.')[0] + '_Translated_Rest.txt'
                 File_Msg.reply_document(TxtFile)
                 File_Msg.reply_document(Rest_File)
    Check_Dir(dl_path)

  def ToArch(self,msg_id,user_id):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    upld2arch(File,File_Msg)
    Check_Dir(dl_path)
  
  def Trac(self,msg_id,user_id,model):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    if model == 'Gemini':
      Txt_File = Gemini_Transcribe(File)
    elif model == 'Wit':
      Stream_Dur = Dur_Get(File_Msg,File)
      Txt_File = Media_F_func(File,Stream_Dur,True)
    Send_TRes(File_Msg,Txt_File)
    Check_Dir(dl_path)

  def Mute(self,msg_id,user_id):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    Muted_Vid = Mute_Video(File)
    Upld_File(Muted_Vid,File_Msg)
    Check_Dir(dl_path)

  def Frag(self,msg_id,user_id,seglength):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    Parts_Dir = Aud_Scatter(File,int(seglength)*60)
    for file in sorted(os.listdir(Parts_Dir)):
              Res_File = Mp3_Conv(Parts_Dir+file)
              Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)

  def Color(self,msg_id,user_id,Rate):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    if File.lower().endswith(Image_forms): 
                  Res_File = Color_Pic(File,Rate)
    else :
                  Res_File = Color_Pdf(File,Rate)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)

  def Blur(self,msg_id,user_id,Rate):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    Res_File = Blur_Func(File,int(Rate))
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)
 
  def Renm(self,msg_id,user_id,NewName):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    Ext = File.split('.')[-1]
    Res_File = f"{dl_path}{NewName.replace('|',' ')}.{Ext}"
    Cmd = f'mv "{File}" "{Res_File}"'
    os.system(Cmd)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)

  def toPdf(self,msg_id,user_id):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    if File.lower().endswith(('ppt','pptx')) :
                  Res_File = PPF2PDF(File)
    elif File.lower().endswith(('mdx')) :
                 Res_File = Mdx2PDf(File)
    elif File.lower().endswith('txt') :
                  Res_File = Txt_2_Pdf(File)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)

  def Marg(self,msg_id,user_id):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    if File.lower().endswith(('ppt','pptx')) :
                File = PPF2PDF(File)
    elif File.lower().endswith(('mdx')) :
                File = Mdx2PDf(File)
    if Pdf_Page_Num(File) < Ex_Pdf_Limit : 
                Res_File = Pdf_Margin(File)
                Upld_File(Res_File,File_Msg)
    else :
      File_Msg.reply(f'حد الملف {Ex_Pdf_Limit} ميغا')
    Check_Dir(dl_path)       

  def Unlock(self,msg_id,user_id):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    if File.lower().endswith(('ppt','pptx')) :
                Res_File = PPF2PDF(File)
                Upld_File(Res_File,File_Msg)
    elif File.lower().endswith(('mdx')) :
                Res_File = Mdx2PDf(File)
                Upld_File(Res_File,File_Msg)
    else :
      if Pdf_Page_Num(File) < Ex_Pdf_Limit : 
                  Res_File = Unlock_Pdf(File)
                  Upld_File(Res_File,File_Msg)
      else :
                    File_Msg.reply(f'حد الملف {Ex_Pdf_Limit} صفحة')
              
    Check_Dir(dl_path) 

  def Amplify(self,msg_id,user_id,Rate):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    Res_File = Media_Amplify(File,Rate)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)
  
  def Compress(self,msg_id,user_id,Rate='10'):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    if File.lower().endswith('pdf'):
                  Res_File = Pdf_Compress(bot,dl_path,File)
    else :
                  Res_File = Media_Compress(File,Rate)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)
  
  def Speeden(self,msg_id,user_id,Rate):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    Res_File = Media_Speed(File,Rate)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)
  
  def Slowen(self,msg_id,user_id,Rate):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    Res_File = Media_Speed(File,Rate)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)

  def Change(self,msg_id,user_id):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    Res_File = Media_Change(File)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)
  
  def Convert(self,msg_id,user_id,mode):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    if File.lower().endswith(Audio_Forms) :
                Res_File = Mp3_Conv(File)
    else :
                if mode == '2mp3':
                  Res_File = Mp3_Conv(File)
                else :
                  Res_File = Encode_Vid(File)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)
  
  def Silence(self,msg_id,user_id):
    File_Msg = Get_Msg(bot,user_id,msg_id)
    dl_path = f'./downloads_{msg_id}_{Bot_Identifier}/'
    File = File_Dl(File_Msg,dl_path)
    Res_File = Media_Skip(File)
    Upld_File(Res_File,File_Msg)
    Check_Dir(dl_path)

multi_method = Multi_Method()

#######################

###### Bot Funcs #####

@bot.on_message(filters.command('clear') & filters.text & filters.private)
def _telegram_file(client, message):
 admins = Admins
 if message.from_user.id in admins :
   private_q.clear()
   message.reply('تم الحذف')

@bot.on_message((filters.command('P_Clear') | filters.command('IM_Clear') | filters.command('A_Clear') | filters.command('V_Clear') | filters.command('IP_Clear') | filters.command('Z_Clear') ) & filters.private)
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
   
   elif message.text.strip() == '/Z_Clear':
     Method = 'Zip'
     Key = f'{Method}_{User_Id}'

   Reply_Id = Merge_Quee[Key][0][0]
   Replied_Msg = Get_Msg(bot,User_Id,Reply_Id)
   Replied_Msg.edit_text('تم الإلغاء ✅')
   del Merge_Quee[Key]
 

@bot.on_message((filters.command('P_Finish') | filters.command('IM_Finish') | filters.command('A_Finish') | filters.command('V_Finish') | filters.command('IP_Finish') | filters.command('Z_Finish')) & filters.private)
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
      replied = Replied_Msg.edit_text(f"جار العمل ☕️ ")
      Key = f'{Method}_{message.from_user.id}'
      Msgs_ids = '_'.join(Merge_Quee[Key][1])
      Item = f"{Method}_{Msgs_ids}_{replied.id}_{message.from_user.id}"
      del Merge_Quee[Key]
      if Method == 'PMerge' :
         multi_method.PMerge(Msgs_ids,message.from_user.id)
      elif Method == 'PMake' :
         multi_method.PMake(Msgs_ids,message.from_user.id)
      elif Method == 'AMerge' :
         multi_method.AMerge(Msgs_ids,message.from_user.id)
      elif Method == 'VMerge' :
         multi_method.VMerge(Msgs_ids,message.from_user.id)
      elif Method == 'Zip' :
         multi_method.Zip(Msgs_ids,message.from_user.id)
      replied.edit_text('تم')
      

@bot.on_message(filters.command('start') & filters.private)
def command1(bot,message):
   User_Id = message.from_user.id
   message.reply('لبقية البوتات \n\n @sunnaybots')
   #My_Db.Insert_User(message.from_user.id)
  

#####

@bot.on_message(filters.private & filters.incoming & (filters.photo | filters.audio | filters.voice | filters.video | filters.document ))
def _telegram_file(client, message):
    
  User_Id = message.from_user.id
  Zip_Key = f'Zip_{User_Id}'
  Montaj_Key = f'Montaj_{User_Id}'
  IMerge_Key = f'IMerge_{User_Id}'
  Pmake_Key = f'PMake_{User_Id}'
  AMerge_Key = f'AMerge_{User_Id}'
  VMerge_Key = f'VMerge_{User_Id}'
  SubAud_Key = f'SubAud_{User_Id}'
  PMerge_Key = f'PMerge_{User_Id}'
  if Zip_Key in list(Merge_Quee.keys()):
    Universal_Concat(message,Merge_Quee,Zip_Key)
    return
  else :
    if Montaj_Key in list(Merge_Quee.keys()) or SubAud_Key in list(Merge_Quee.keys()) :
      Key = (Montaj_Key if Montaj_Key in list(Merge_Quee.keys()) else SubAud_Key)
      if (message.voice or message.photo or message.audio) or (message.document.file_name.lower().endswith(Image_forms+Audio_Forms)) :
        Merge_Quee[Key][1].append(str(message.id))
        Replied_Id = Merge_Quee[Key][0][0]
        Replied_Msg = Get_Msg(bot,User_Id,Replied_Id)
        
        replied = Replied_Msg.edit_text(f"جار العمل ☕ ")
        Msgs_ids = '_'.join(Merge_Quee[Key][1])
        Item = f"{Key.split('_')[0]}_{Msgs_ids}_{replied.id}_{User_Id}"
        del Merge_Quee[Key]
        if Key == Montaj_Key :
          multi_method.Montaj(Msgs_ids,User_Id)
        else :
           multi_method.SubAud(Msgs_ids,User_Id)
        replied.edit_text('تم')
        return None
      
    elif IMerge_Key in list(Merge_Quee.keys()):
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
    elif AMerge_Key in list(Merge_Quee.keys()):
     if message.audio or message.voice or message.document.file_name.lower().endswith(Audio_Forms) :
      Universal_Concat(message,Merge_Quee,AMerge_Key)
      return
    elif VMerge_Key in list(Merge_Quee.keys()):
     if message.video or message.document.file_name.lower().endswith(Video_Forms) :
      Universal_Concat(message,Merge_Quee,VMerge_Key)
      return

  if message.photo : 
      Options =  Photo_Options + Pdf_Image_Option
  
  elif message.audio or message.voice : 
      Options = Audio_Options

  elif message.video : 
   Options = Video_Options
   
  elif message.document : 
   
   if message.document.file_name.lower().endswith(Image_forms) : 
      Options = Photo_Options + Pdf_Image_Option
     
   elif message.document.file_name.lower().endswith(Video_Forms) : 
     Options = Video_Options
     
   elif message.document.file_name.lower().endswith(Audio_Forms) : 
     
      Options = Audio_Options
   
   elif message.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')) : 
       if message.document.file_name.lower().endswith('pdf'):
        Options = Pdf_Options
       else :
         Options = Ppf_Opts
   
   elif message.document.file_name.lower().endswith('txt') : 
     
     Options = Pdf_Txt_Option
   
   elif message.document.file_name.lower().endswith(('cbz','cbr','zip','rar')) : 
     
     Options = Cbx_Option
   
   elif message.document.file_name.lower().endswith('epub'): 
     Options = Epub_Opts
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

@bot.on_callback_query()
def callback_query(CLIENT,CallbackQuery):
  User_Id = CallbackQuery.from_user.id
  Callback_List = CallbackQuery.data.split('_')
  Method = Callback_List[0]
  Msg_Id = Callback_List[1]
  if not Msg_Id in ('SBS','UD'):
    file_msg = Get_Msg(bot,User_Id,Msg_Id)
  if Method == 'Yes':
    CallbackQuery.edit_message_text("أهلا بك 🌿 ")
  
  elif Method == 'No':
    CallbackQuery.edit_message_text("شكراً لك على صدقك🌿 ")
  elif Method == 'DelArch':
    Replied = CallbackQuery.edit_message_text("جار الحذف 🌿")
    Arch_Url = CallbackQuery.message.text
    File_Name = Arch_Url.split('/')[-1]
    delarch_file(File_Name)
    Replied.edit_text("تم الحذف 🌿")

  elif Method in ('Trans','Trac'):
   
   if Method == 'Trac':
    if len(Callback_List) == 3 :
      if Callback_List[2] == 'Gemini':
       if User_Id not in Prv_Members : 
        CallbackQuery.edit_message_text(f"هذه الميزة خاصة  ☕ ")
        return
       if not User_Id in Gemini_Users :
        CallbackQuery.edit_message_text(f"هذه الميزة معطلة  ☕ ")
       else : 
          replied = CallbackQuery.edit_message_text(f"جار العمل  ☕️ ")
          multi_method.Trac(Msg_Id,User_Id,'Gemini')
          replied.edit_text('تم')
      else :
        replied = CallbackQuery.edit_message_text(f"جار العمل  ☕️ ")
        multi_method.Trac(Msg_Id,User_Id,'Wit')
        replied.edit_text('تم')
    
    elif len(Callback_List) == 2 :
      CHOOSE_UR_Mod = "اختر النموذج "
      Tracs_BUTTONS = []
      for Mod in Tracs_Modules : 
        Data = f"{CallbackQuery.data}_{Mod[1]}"
        Tracs_BUTTONS.append([InlineKeyboardButton(Mod[0],callback_data=Data)])
      CallbackQuery.edit_message_text(text = CHOOSE_UR_Mod,reply_markup = InlineKeyboardMarkup(Tracs_BUTTONS))

   elif Method == 'Trans':
    if len(Callback_List) == 4 :
      if Callback_List[3] == 'Gemini':
       if not User_Id in Gemini_Users :
        CallbackQuery.edit_message_text(f"هذه الميزة معطلة  ☕ ")
       else : 
         replied = CallbackQuery.edit_message_text(f"جار العمل  ☕️ ")
         multi_method.Trans(Msg_Id,User_Id,'Gemini',Callback_List[-2])
         replied.edit_text('تم')

    elif len(Callback_List) == 3 :
      CHOOSE_UR_Mod = "اختر النموذج "
      LANGS_BUTTONS = []
      for Mod in LANGS_Modules : 
        Data = f"{CallbackQuery.data}_{Mod[1]}"
        LANGS_BUTTONS.append([InlineKeyboardButton(Mod[0],callback_data=Data)])
      CallbackQuery.edit_message_text(text = CHOOSE_UR_Mod,reply_markup = InlineKeyboardMarkup(LANGS_BUTTONS))
    else :
      CHOOSE_UR_LANG = "اختر اللغة المراد الترجمة إليها"
      LANGS_BUTTONS = []
      for lang in g_langs : 
        
        Rom_Num = int(len(g_langs)/3)
        Data = f"{CallbackQuery.data}_{lang.split('|')[-1].strip()}"
        if g_langs.index(lang) > Rom_Num-1 :
         LANGS_BUTTONS[g_langs.index(lang)%Rom_Num].append(InlineKeyboardButton(lang.split('|')[0],callback_data=Data))
        else : 
         LANGS_BUTTONS.append([InlineKeyboardButton(lang.split('|')[0],callback_data=Data)])
      CallbackQuery.edit_message_text(text = CHOOSE_UR_LANG,reply_markup = InlineKeyboardMarkup(LANGS_BUTTONS))
      
  elif Method in ('Montaj','SubAud'):
      #Clear_Dict(Merge_Quee,User_Id)
      Key = f'{Method}_{User_Id}'
      if Method == 'Montaj' :
       if Key in list(Merge_Quee.keys()):
        del Merge_Quee[Key]
       Merge_Quee[Key] = [[],[Callback_List[-1]]]
       if file_msg.document :
         if file_msg.document.file_name.lower().endswith(Image_forms):
           Word = 'الصوتية'
         else :
           Word = 'الصورة'
       elif file_msg.photo :
         Word = 'الصوتية'
       else :
         Word = 'الصورة'
       M_Text = f'الآن أرسل {Word} 🌿'
       Replied = CallbackQuery.edit_message_text(M_Text)
       Merge_Quee[Key][0].append(Replied.id)
      
      elif Method == 'SubAud' :
       if Key in list(Merge_Quee.keys()):
        del Merge_Quee[Key]
       Merge_Quee[Key] = [[],[Callback_List[-1]]]
       M_Text = f'الآن أرسل الصوتية 🌿'
       Replied = CallbackQuery.edit_message_text(M_Text)
       Merge_Quee[Key][0].append(Replied.id)

  elif Method in ('PMake','IMerge','PMerge','AMerge','VMerge','VMerge','Zip') :
    if Method == 'PMerge':
      Word = 'الملفات'
      Cmd = '/P_Finish'
      C_Cmd = '/P_Clear'
    elif Method == 'Zip':
      Word = 'الملفات'
      Cmd = '/Z_Finish'
      C_Cmd = '/Z_Clear'
    elif Method == 'IMerge':
     if Msg_Id in ('SBS','UD') :
      Key = f'IMerge_{User_Id}'
      Msgs_ids = '_'.join(Merge_Quee[Key][1])
      replied = CallbackQuery.edit_message_text(f"جار العمل  ☕️ ")
      multi_method.IMerge(Msgs_ids,User_Id,Msg_Id)
      replied.edit_text('تم')
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
      
    elif Method == 'AMerge':
    
      Word = 'الصوتيات'
      Cmd = '/A_Finish'
      C_Cmd = '/A_Clear'
    
    elif Method == 'VMerge' :
      if User_Id not in Prv_Members : 
        CallbackQuery.edit_message_text(f"هذه الميزة خاصة  ☕ ")
        return
      Word = 'الفيديوهات'
      Cmd = '/V_Finish'
      C_Cmd = '/V_Clear'

    #Clear_Dict(Merge_Quee,User_Id)
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
    
  elif Method in ['Color','Blur','Amplify','Compress','Speeden','Slowen','Convert'] :
   if len(Callback_List) > 2 : 
     if Callback_List[-1] == '2mp4' :
       if file_msg.document :
        if file_msg.document.file_name.lower().endswith('mp4'):
          replied = CallbackQuery.edit_message_text(f"جار العمل ☕")
          File = File_Dl(file_msg,main_dl_path)
          Upld_File(File,file_msg)
          os.remove(File)
          replied.edit_text('تم ✅')
        else :
          replied = CallbackQuery.edit_message_text(f"جار العمل  ☕️ ")
          multi_method.Convert(Msg_Id,User_Id,'2mp4')
          replied.edit_text('تم')
       
     elif Callback_List[-1] == '2ogg' :
        replied = CallbackQuery.edit_message_text(f"جار العمل ☕")
        File = File_Dl(file_msg,main_dl_path)
        if file_msg.document :

          if file_msg.document.file_name.lower().endswith(Video_Forms):
            File = Mp3_Conv(File)
        
        elif file_msg.video :

          File = Mp3_Conv(File)
        
        file_msg.reply_voice(File)
        os.remove(File)
        replied.edit_text('تم ✅')

     else :
      replied = CallbackQuery.edit_message_text(f"جار العمل  ☕️ ")
      if Method == 'Color' :
        multi_method.Color(Msg_Id,User_Id,Callback_List[-1])
      elif Method == 'Blur' :
        multi_method.Blur(Msg_Id,User_Id,Callback_List[-1])
      elif Method == 'Amplify' :
        multi_method.Amplify(Msg_Id,User_Id,Callback_List[-1])
      elif Method == 'Compress' :
        multi_method.Compress(Msg_Id,User_Id,Callback_List[-1])
      elif Method == 'Speeden' :
        multi_method.Speeden(Msg_Id,User_Id,Callback_List[-1])
      elif Method == 'Slowen' :
        multi_method.Slowen(Msg_Id,User_Id,Callback_List[-1])
      elif Method == 'Convert' :
        multi_method.Convert(Msg_Id,User_Id,Callback_List[-1])
      replied.edit_text('تم')

   else : 
    CHOOSE_UR_BUTTONS = []
    CHOOSE_UR_Option = "اختر ما تريد "
    if Method == 'Color':
      Buttons = Color_button
    elif Method == 'Blur':
      Buttons = Photo_Blur_buttons
    elif Method == 'Amplify':
      Buttons = Amplify_Buttons
    elif Method in ('Compress','Convert'):
     
     if Method == 'Convert':
       if file_msg.document :
        if file_msg.document.file_name.lower().endswith(Audio_Forms):
         if file_msg.document.file_name.lower().endswith('ogg'):
           Buttons = Vid_Cov_Ops[1:-1]
         else :
          Buttons = Vid_Cov_Ops[:-2]
        else :
          Buttons = Vid_Cov_Ops
       elif file_msg.audio or file_msg.voice :
         if file_msg.voice :
           Buttons = Vid_Cov_Ops[1:-1]
         else :
          Buttons = Vid_Cov_Ops[:-2]
        #  Callback_Add(CallbackQuery)
        #  return
       else :
          if file_msg.video :
              Buttons = Vid_Cov_Ops[:-1]
     
     elif Method == 'Compress':
      if file_msg.document :
        if file_msg.document.file_name.lower().endswith(Video_Forms):
          replied = CallbackQuery.edit_message_text(f"جار العمل  ☕️ ")
          multi_method.Compress(Msg_Id,User_Id)
          replied.edit_text('تم')
          return
        elif file_msg.document.file_name.lower().endswith(Audio_Forms):
          Buttons = Aud_Comp_Buttons
        elif file_msg.document.file_name.lower().endswith('pdf'):
          replied = CallbackQuery.edit_message_text(f"جار العمل  ☕️ ")
          multi_method.Compress(Msg_Id,User_Id)
          replied.edit_text('تم')
          return 
      elif file_msg.video : 
        replied = CallbackQuery.edit_message_text(f"جار العمل  ☕️ ")
        multi_method.Compress(Msg_Id,User_Id)
        replied.edit_text('تم')
        return
      else :
        Buttons = Aud_Comp_Buttons
    elif Method == 'Speeden':
      Buttons = Speed_Buttons
    elif Method == 'Slowen':
      Buttons = Slow_Buttons
    for method in Buttons : 
       Text = method[0]
       Data = CallbackQuery.data + '_' + method[1]
       CHOOSE_UR_BUTTONS.append([InlineKeyboardButton(Text,callback_data=Data)])
    
    CallbackQuery.edit_message_text(text = CHOOSE_UR_Option,reply_markup = InlineKeyboardMarkup(CHOOSE_UR_BUTTONS))
    
  elif Method in ('Trim','Renm','Frag'):
   bot.delete_messages(User_Id,CallbackQuery.message.id)
   if Method == 'Renm' :
     Text = Renm_msg
   elif Method == 'Trim' :
     if file_msg.document :
       if file_msg.document.file_name.lower().endswith(('pdf','ppt','pptx','mdx')):
         Text = Pdf_Trim_Msg
       elif file_msg.document.file_name.lower().endswith('txt'):
        Text = Txt_Trim_Msg
       else :
         Text = Media_Trim_Msg
     else :
       Text = Media_Trim_Msg
   elif Method == 'Frag' :
     Text = "الآن أرسل عدد الدقائق لكل قطعة صوتية"
   file_msg.reply_text(Text,reply_markup=ForceReply(True),reply_to_message_id=file_msg.id)
  
  elif Method in ('Ocr','2Pdf','Det','Ex','Marg','Unlock','Change','Silence','Mute','ToArch','MRMV') :
    File_Id = Callback_List[-1]
    replied = CallbackQuery.edit_message_text(f"جار العمل  ☕️ ")
    if Method == 'Det':
       multi_method.Det(File_Id,User_Id)
    elif Method == 'Ocr':
       multi_method.Ocr(File_Id,User_Id)

    elif Method == '2Pdf':
       multi_method.toPdf(File_Id,User_Id)

    elif Method == 'Ex':
       multi_method.Ex(File_Id,User_Id)
      
    elif Method == 'Marg':
       multi_method.Marg(File_Id,User_Id)

    elif Method == 'Unlock':
       multi_method.Unlock(File_Id,User_Id)

    elif Method == 'Change':
       multi_method.Change(File_Id,User_Id)
      
    elif Method == 'Silence':
       multi_method.Silence(File_Id,User_Id)

    elif Method == 'Mute':
       multi_method.Mute(File_Id,User_Id)

    elif Method == 'ToArch':
      if User_Id not in Prv_Members : 
        CallbackQuery.edit_message_text(f"هذه الميزة خاصة  ☕ ")
        return
      else :
        multi_method.ToArch(File_Id,User_Id)
    replied.edit_text('تم')

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
    Gemini_Token_Pattern = "^AIzaSy.*"
    # if re.search(Gemini_Token_Pattern,Msg_Text) :
    #   Gemini_Token = Msg_Text.strip()
    #   GTokens = Gemini_Tokens
    #   if Gemini_Token in GTokens : 
    #      reply_msg.reply('التوكن موجود بالفعل ، استعمل غيره 🌿')
    #   else : 
    #       tokentext = f"{User_Id}_{Gemini_Token}_#gtokens"
    #       bot.send_message(-1001655903083,tokentext)
    #       reply_msg.reply('تمت إضافة التوكن لقاعدة البيانات ✅')
    #   reply_msg.delete()
    # else :
    ReplyMsg_Text = reply_msg.text
    reply_msg.delete()
    replied = file_msg.reply(f"جار العمل ☕ ")
    Pdf_Trim_Pattern = r"^\d+(?:[,-/]\d+(?:-\d+)?)*$"
    Media_Trim_Pattern = r"\d{,2}:\d{2}"
    if 'عدد الدقائق' in ReplyMsg_Text :
        Process = 'Frag'
        Text = Msg_Text
    elif re.search(Pdf_Trim_Pattern,Msg_Text) or re.search(Media_Trim_Pattern,Msg_Text) or '~' in Msg_Text  :
        Process = 'Trim'
        Text = Msg_Text.strip()
        if ' ' in Text:
          Text = Msg_Text.replace(' ','|')
        multi_method.Trim(file_id,User_Id,Text)
    else :
        Process = 'Renm'
        Text = Msg_Text.replace(' ','|')
        multi_method.Renm(file_id,User_Id,Text)
    replied.edit_text('تم')
    

bot.run()