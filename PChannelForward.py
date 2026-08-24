import nest_asyncio
nest_asyncio.apply()
import os,time

#########################################################


Api_Id = os.environ['Api_Id']
Api_Hash = os.environ['Api_Hash']
Session_String = os.environ['Session_String']
Original_Channel = os.environ['Original_Channel']
Forward_Channel = os.environ['Forward_Channel']

#########################################################


from pyrogram import Client,idle
from pyrogram.errors import FloodWait


import asyncio,shutil


Token_Identifier = Session_String.split('-')[0]
Session_file = Token_Identifier +'_session_bot'

bot = Client(Session_file,api_id=Api_Id,api_hash=Api_Hash,session_string=Session_String)


async def Msg_Copy(Msg,Chnl_Id):
  try : 
     Copy = await Msg.copy(str(Chnl_Id))
     return Copy
  except FloodWait as e :
      time.sleep(e.value)
      return await Msg_Copy(Msg,Chnl_Id)
  except Exception as err : 
    await Msg.reply(err)
    pass
  
async def Channel_Arc(Original_Channel,Forward_Channel) :
      Msgs_List = []
      async for Msg in bot.get_chat_history(Original_Channel) :
        Msgs_List.append(Msg)
      for Msg in reversed(Msgs_List):
          Copied = await Msg_Copy(Msg,Forward_Channel)

##############


def main():
    try:
        bot.start()
        asyncio.run(Channel_Arc(Original_Channel,Forward_Channel))
        print("✅ تمت الأرشفة")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()