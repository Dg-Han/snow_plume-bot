from nonebot import get_bot
from time import sleep
from nonebot.adapters import Bot


async def sending_message(msg_list:list, group_id:int = 670404622, auto_escape:bool = False) -> list:    
    '''
    发送消息，返回发送消息的消息ID列表\n
    ----------
    Parameters  
    - msg_list（必填）：待发送的消息（可带CQ码的String格式）
    - group_id：消息送达的群号
    - auto_escape: 是否禁用CQ码解析（默认为False）\n
    ----------
    Returns     
    - message_ID_list: 每条发送消息的对应id（顺序与msg_list一致）   
    '''
    msg_package = []
    msg = {"group_id": group_id,               # 输入群号
        "message" : "",
        "auto_escape": auto_escape}                  # 设置是否不对文本中包含的CQ码进行转换
    # 将消息封装进msg字典后，放入package等待发送
    for msg_seg in msg_list:          
        msg["message"] = msg_seg
        msg_package.append(msg.copy())
    # 发送消息并获取发送消息的消息ID
    bot = get_bot()
    message_ID_list = []                             
    for msg in msg_package:
        msg_ID = await bot.call_api('send_group_msg',**msg)
        message_ID_list.append(msg_ID['message_id'])
        sleep(2)
    return message_ID_list


async def send_forward_msg(bot:Bot,group_id,msg_list):
    msg = []
    for seg in msg_list:
        msg_raw=   {"type":"node",
                "data":{
                    "name":"轻雪酱",
                    "uin":"409932598",
                    "content":seg
                    }}
        msg.append(msg_raw)
    data = {
            'group_id':group_id, # '消息发送的QQ群号'
            'messages':msg
            }

    info = await bot.call_api('send_group_forward_msg',**data)
    return info

async def recall_msg(bot:Bot,message_id:int) -> None:
    '''
    撤回消息\n
    ----------
    Parameters  
    - msg_id（必填）：需要撤回的消息id
    ----------
    Returns     
    - None
    '''
    data = {
            'message_id':message_id
            }
    await bot.call_api('delete_msg',**data)
    