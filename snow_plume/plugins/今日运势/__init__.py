from nonebot import on

from nonebot.adapters import Bot,Event
from nonebot import rule

import random
import time
import re
from snow_plume.mysql import execute_procedure
from snow_plume.handling_message import sending_message


# 插件主体：今日运势
# 用户在对话框输入想要查看今日运势的相关讯息后，轻雪酱会识别并返回抽签的结果

async def message_checker_fortune(event:Event):
    msg = event.get_plaintext()
    pattern0 = re.compile("(运势|运气|手气|签)")    
    pattern1 = [("查","看看","测","抽"),("如何","怎么样","咋样","怎样")]
    if pattern0.findall(msg):       #要触发该功能，语句中必须含有pattern0中的词
        count = 0
        for pattern in pattern1:
            for i in pattern:       #要触发该功能，语句中还必须含有pattern1中的词
                if i in msg:
                    count += 1
                    break
        if count or msg == "今日运势" or msg == "运势":
            rule_result = True
        else:
            rule_result = False
        return rule_result

rule_fortune = rule.Rule(message_checker_fortune)

fortune_matcher = on(type="message",rule=rule_fortune,priority=5,block=True)

@ fortune_matcher.handle()
async def handling(bot:Bot,event:Event):    #要调用api，需要添加Bot对象
    session_id = event.get_session_id().split("_")                  #session_id返回了触发指令的对象信息，包括用户id和所在群组id
    raw_data = await bot.call_api('get_group_member_info',**{       #根据用户id和群组id调用go-cqhttp的“get_group_member_info”API，获取该对象的详细信息
        'group_id': session_id[1],
        'user_id' : session_id[2]
    })                                                              #go-cqhttp API调用：https://docs.go-cqhttp.org/api/
    nickname = raw_data['nickname']                                 #从详细信息中获取{“昵称”：“nickname”}

    # 调用mysql数据库，记录运势
    user = session_id[2]
    args_in = [f'{user}']
    args_out = ['fortune','level_name','greetings','greeting_content','charm_item','charm_content']
    proc_name = 'fortune_get'

    proc = execute_procedure(proc_name,args_in,args_out)
    proc_result = proc.proc()

    if proc_result['Code'] == 1062:         # 返回码为1062说明设置了重复主键，即同一用户在某日请求了多次运势
        proc = execute_procedure('fortune_get_when_duplicated',args_in,args_out)
        proc_result = proc.proc()
        msg_list = [(f"{nickname}： 今天已经抽过签了哟！"),
                    (f"你今天的幸运等级是{proc_result['level_name']} (幸运指数:{proc_result['fortune']})"),
                    (f"今日幸运物：{proc_result['charm_item']}。\n{proc_result['charm_content']}")]
        await sending_message(msg_list)
    else:
        await fortune_matcher.send("要开始抽签了喔！我看看，今天{}的运势……".format(nickname))
        time.sleep(3)
        msg_list = [(f"{proc_result['greetings']}幸运指数是{proc_result['fortune']}，{proc_result['greeting_content']}"),
                    (f"今日幸运物：{proc_result['charm_item']}。\n{proc_result['charm_content']}")]
        await sending_message(msg_list)