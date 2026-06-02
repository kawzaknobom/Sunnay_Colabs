import os
g_langs = [ 'العربية | ar','الإنجليزية | en','الفرنسية | fr','الألمانية | de','العبرية iw  |  iw','العبرية he | he','اليونانية | el','الأمهرية | am','الباسك | eu','البنغالية | bn','البرتغالية  | pt','البلغارية | bg','الكتالانية | ca','الشيروكية | chr','الكرواتية | hr','التشيكية | cs','الدنماركية | da','الهولندية | nl','الإستونية | et','الفلبينية | fil','الفنلندية | fi','الغوجاراتية | gu','الهندية |  hi','المجرية | hu','الأيسلندية | is ','الإندونيسية | id','الإيطالية | it','اليابانية | ja','الكانادا  | kn','الكورية | ko','اللاتفية | lv','الليتوانية | lt','الماليزية |  ms','المالايالامية | ml','الماراثية |  mr','النرويجية | no','البولندية | pl','الرومانية | ro','الروسية | ru','الصربية | sr','الصينية  | zh-cn','الصينية TW | zh-tw','السلوفاكية | sk','السلوفينية | sl','الإسبانية | es','السواحيلية | sw','السويدية | sv','التاميلية | ta','التيلوغوية | te','التايلاندية | th','التركية|  tr','الأوردية | ur','الأوكرانية | uk','الفيتنامية | vi' ,'الويلزية | cy','الأفريكانية | af', 'الأرمينية | hy','الألبانية | sq','الأذريبيجانية | az','البيلاروسية | be','البوسنية | bs','السبيونوية | ceb','الشيشوانية | ny','الكورسيكية | co', 'الهولندية | nl','الاسبرانتو | eo','الاستوانية | et','الفلبينية | tl','الزولو | zu ','يوروبا | yo','اليديشية | yi','xhosa | xh','الأوزبكية | uz ','أويغور | ug','طاجيكية | tg','السودانية | su','الصومالية | so','السنهالية | si','السندية | sd','شونا | sn','سيسوتو | st','الغيلية | gd','ساموا | sm','رومانية | ro','بنجابية | pa' ,'فارسية | fa','باشتو | ps','أوديا | or','نرويجية | no' ,'نيبالية | ne','ميانمارية | my','منغولية | mn','ماورية | mi','مالطية | mt','قيرغيزستانية | ky','كردية | ku','الخميرية | km','الكازخستانية | kk','الجاوية | jw','الأيرلندية | ga','الإندونيسية | id', 'الإيغبو | ig', 'المجرية | hu', 'همونغ | hmn','هاواي | haw','هاوسا | ha','الكريولية | ht' ,'الجورجية | ka','الجاليكية | gl','الفريزية | fy','لاوية | lo', 'لاتينية | la', 'ليتوانية | lt', 'لوكسمبورغية | lb','المقدونية | mk', 'الملغاشية | mg']

Audio_Forms = (".mp3",".ogg",".m4a",".aac",".flac",".wav",".wma",".opus",".3gpp")

Video_Forms = (".mp4",".mkv",".mov",".avi",".wmv",".avchd",".webm",".flv")

Image_forms = (".jpg",".png",'.tif','webp')

Coloration_File = '/content/Sunnay_Colabs/coloration'
seg_per_sec = 1200
count = 0
T_linebreak = '\n\n ◾ــــــــــــــ◾ \n\n'
line_break = '\n\n'
Small_line_break = '\n'
Full_linebreak = '\n\n 🌹ــــــــــــــ🌹 \n\n'
Api_Id = 15952578
Api_Hash = '3600ce5f8f9b9e18cba0f318fa0e3600'


##### Media Ops 

# ,['إزالة المعازف','MRMV']
Translate_Opts = [['ترجمة','Trans']]
Photo_Audio_Ops = [['منتجة','Montaj']]
Compress_Op = [['ضغط','Compress']]
Trim_Op = [['قص','Trim']]
Other_Opts = [['رفع لأرشيف','ToArch'],['Zip','Zip']]
Other_Options = [['تسمية','Renm'],['تفاصيل','Det']] + Other_Opts
Media_Options = [['تضخيم','Amplify'],['تسريع','Speeden'],['تبطيئ','Slowen'],['تحويل','Convert'],['تغيير الصوت','Change'],['تفريغ','Trac']] + Compress_Op + Trim_Op +Other_Options
Video_Options = Media_Options + [['بلور','Blur'],['كتم الصوت','Mute'],['إبدال الصوت','SubAud'],['دمج','VMerge']]
Audio_Options = Media_Options + Photo_Audio_Ops +  [['دمج','AMerge'],['إزالة الصمت','Silence'],['تقطيع','Frag']]

Aud_Comp_Buttons = [['10k','10'],['20k','20'],['30k','30'],['40k','40'],['50k','50']]
Amplify_Buttons = [['05db','05'],['10db','10'],['15db','15'],['20db','20'],['25db','25']]
Speed_Buttons =[['x1.25','1.25'],['x1.5','1.5'],['x1.75','1.75'],['x2','2']]
Slow_Buttons = [['x0.75','0.75'],['x0.5','0.5']]

Media_Trim_Msg = "الآن أرسل نقطة البداية والنهاية بهذه الصورة \n\n hh:mm:ss-hh:mm:ss"
Audio_Multi_Options = ['AMerge']

##### Photo Ops 

Photo_Options = [['دمج','IMerge'],['تلوين','Color'],['بلور','Blur']] + Photo_Audio_Ops  + Other_Opts + Translate_Opts
Photo_Multi_Options = ['IMerge','PMake']
Photo_Blur_buttons = [['05','05'],['10','10'],['15','15'],['20','20'],['25','25'],['30','30']]

##### Pdf Ops 
Ex_Opt = [['استخراج','Ex']]
Cbx_Option =  Ex_Opt + Other_Options + Translate_Opts
Ex_Pdf_Limit = str(500)

#Cbx_Option

To_Pdf_Opt = [['Conv to Pdf ','2Pdf']]
Pdf_Options = [['دمج','PMerge'],['بلا حواشي','Marg']]  + Cbx_Option + Trim_Op
Ppf_Opts = Pdf_Options + To_Pdf_Opt
Pdf_Txt_Option = Other_Options + Trim_Op + Translate_Opts
Epub_Opts = Cbx_Option 
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

Working_Options = [['ضغط','Compress'],['عكس','Rev'],['تجانب','Sbs'],['تلوين','Color']]
#####
#[['رمادي','g']]
Color_button = [['أحمر','r'],['أصفر','y'],['أزرق فاتح','b'],['أرجواني','p']]
Renm_msg = "الآن أدخل الاسم الجديد "

Vid_Cov_Ops = [['To ogg','2ogg'],['To Mp3','2mp3'],['To Mp4','2mp4']]

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

S_Process_Ops = ['Trans','Det','Blur','IMerge','PMerge','Color','Ocr','PMake','Ex','TxtPdf','Renm','Trim'] 

