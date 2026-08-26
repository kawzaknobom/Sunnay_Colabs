import nest_asyncio
nest_asyncio.apply()
import os,time

#########################################################


Api_Id = os.environ['Api_Id']
Api_Hash = os.environ['Api_Hash']
Session_String = os.environ['Session_String']
Original_Channel = os.environ['Original_Channel']
Forward_Channel = os.environ['Forward_Channel']
Start_Msg_Id = int(os.environ['Start_Msg_Id'])


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
    pass
  
async def Channel_Arc(Original_Channel,Forward_Channel,Start_Msg_Id) :
      Msgs_List = []
      async for Msg in bot.get_chat_history(Original_Channel) :
        Msgs_List.append(Msg)
      End_Msg_Id = len(Msgs_List)
      Msgs_List = reversed(Msgs_List)
      if Start_Msg_Id != 0 :
          Start_Msg_Id -= 1

      for ind in range(Start_Msg_Id,End_Msg_Id):
          Copied = await Msg_Copy(Msgs_List[ind],Forward_Channel)
      await bot.send_message(Forward_Channel, f"🟥 {Forward_Channel}_{End_Msg_Id}")

       

##############


def main():
    try:
        bot.start()
        asyncio.run(Channel_Arc(Original_Channel,Forward_Channel,Start_Msg_Id))
        print("✅ تمت الأرشفة")
        idle()
    finally:
        if bot.is_connected:
            bot.stop()

main()