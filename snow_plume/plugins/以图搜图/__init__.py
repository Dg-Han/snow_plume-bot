from nonebot import on

from nonebot.adapters import Bot,Event
from nonebot import rule

import time
import re
from saucenao_api import SauceNao

from snow_plume.plugins.setu import SendArtwork


# 可重复用于其他功能的函数

# 1) 发送合并转发消息
# 输入待发送的群号和消息（列表形式），输出调用api时使用的参数
def send_forward_msg(group_id,msg_list):
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
    return data


# 插件主体：以图搜图
# 用户在对话框中发送图片，再发送搜图指令（或在对某张图片的回复中发送搜图指令），轻雪酱就会自动搜图，返回搜图结果并自动搜索该作者创作的其他图片

async def message_checker_search_author(bot:Bot,event:Event):
    msg = event.get_plaintext()
    if "搜" in msg:
        group_id = event.get_session_id().split("_")[1]
        raw_data = await bot.call_api('get_group_msg_history',**{       #调用go-cqhttp的API，返回历史消息列表
            "group_id" : group_id
            })
        CQ_msg = raw_data["messages"][-2]["raw_message"]                #获取上一则消息的内容（如果是图片，那么会返回CQ码）
        pattern = "^\[CQ:image,file=.*\]$"
        if re.match(pattern,CQ_msg):                                    # 如果搜图指令的上一句对话是一张纯图片，那么开始执行程序
            return True
        if "CQ:reply" in raw_data["messages"][-1]["raw_message"]:       # 如果是包含搜图指令的回复消息，则被回复消息中包含图片，那么开始执行程序
            msg_id = int(raw_data["messages"][-1]["raw_message"].split("CQ:reply,id=")[1].split("][CQ:at")[0])
            msg_resp = await bot.call_api('get_msg',**{
                "message_id" : msg_id
                })
            msg = msg_resp["message"]
            pattern = "\[CQ:image,file=.*\]"
            if re.match(pattern,msg):
                return True

        

rule_search_author = rule.Rule(message_checker_search_author)
search_author_matcher = on(type="message",rule=rule_search_author,priority=5,block=True)


@ search_author_matcher.handle()
async def handling(bot:Bot,event:Event):    
    group_id = event.get_session_id().split("_")[1]
    raw_data = await bot.call_api('get_group_msg_history',**{       # 调用go-cqhttp的API，返回历史消息列表
        "group_id" : group_id
        })
    if "CQ:reply" in raw_data["messages"][-1]["raw_message"]:           # 如果是包含搜图指令的回复消息，则获取被回复消息中所包含的图片
        msg_id = int(raw_data["messages"][-1]["raw_message"].split("CQ:reply,id=")[1].split("][CQ:at")[0])
        msg_resp = await bot.call_api('get_msg',**{
            "message_id" : msg_id
            })
        url_msg = msg_resp["message"].split("url=")[1].split("]")[0]    # 从被回复消息的图片CQ码中获取图片url地址(e.g. [CQ:image,file=58321ac06f1d1766bbd81525ace6fb97.image,subType=0,url=https://gchat.qpic.cn/gchatpic_new/516410252/670404622-3042510406-58321AC06F1D1766BBD81525ACE6FB97/0?term=3&amp;is_origin=1])
    else:
        CQ_msg = raw_data["messages"][-2]["raw_message"]                # 如果是发送图片后再发送搜图指令，则从倒数第二条历史消息中获取CQ码
        url_msg = CQ_msg.split("url=")[1].split("]")[0]                 # 从CQ码中获取待搜图片的url地址

    parameters = SauceNao(api_key='97b0ce17066172b0069e037e15dd36c091e6f802',numres=12) # API_key以及请求的搜图结果个数
    try:
        result_raw = parameters.from_url(url_msg).raw                   # 尝试调取SauceNAO的API
    except:
        await search_author_matcher.finish("调取Saucenao_API失败, 可能是搜索太频繁啦！\n（30秒内最多搜索4次，24小时内100次）")
    else:
        result_list = []                                                # 储存搜索结果
        character_possible = {}                                         # 储存输出简报中包含的登场人物及登场作品信息
        similarity_threshold = 80                                       # 相似度阈值，一般为80，低于相似度阈值的不进入结果列表
        if "表情包" in event.get_plaintext():
            similarity_threshold = 45                                   # 搜索表情包时阈值降低到45
        for i in range(0,len(result_raw['results'])):
            # 抽取第i个识图结果
            result = result_raw['results'][i]
            similarity = float(result['header']['similarity'])
            if similarity >= similarity_threshold:                                        # 相似度低于80的不进入结果列表
                # 创建搜索结果字典
                result_dict = {"Primary_Key":0,"Similarity":0,"Thumbnail_URL":None,"Author":None,"URL":None,"Source":None}  # 搜索结果包含字段：序号、相似度、缩略图url、作者、原图链接、来源（P站/其他）
                Pixiv_Source = {"Title":None,"Pixiv_Id":None,"Author":None,"Author_Pixiv_Id":None}                          # P站来源额外字段：图标题、图id、作者、作者id
                Other_Source = {"Author":None,"Theme":None,"Character":None}                                                # 其他来源额外字段：作者、登场作品、登场人物
                try:
                    url = result['data']['ext_urls'][0]  
                except:
                    url = "该数据库未提供链接"       
                finally:
                    # 写入结果
                    result_dict["Similarity"] = similarity                              # 相似度
                    result_dict["Thumbnail_URL"] = result['header']['thumbnail']        # 缩略图（URL形式）
                    result_dict["URL"] = url                                            # 直接访问原图的URL
                    if "www.pixiv.net" in url and "fanbox" not in url:                                          # 图源：P站
                        result_dict["Source"] = "Pixiv"                                 # 图源
                        result_dict["Author"] = result['data']['member_name']           # 作者
                        Pixiv_Source["Title"] = result['data']['title']                 # 图标题
                        Pixiv_Source["Pixiv_Id"] = result['data']['pixiv_id']           # 图ID
                        Pixiv_Source["Author"] = result['data']['member_name']          
                        Pixiv_Source["Author_Pixiv_Id"] = result['data']['member_id']   # 作者ID
                        result_dict["Pixiv_Source"] = Pixiv_Source
                    else:                                                               # 图源：其他（danbooru, yande.re, gelbooru等）
                        result_dict["Source"] = "Other"
                        name_list = ['creator_name','creator','pawoo_user_display_name','member_username','eng_name']   # 不同图源有不同的格式
                        for author_name in name_list:
                            try:
                                result_dict["Author"] = result['data'][author_name]     # 不符合这些图源名称规范的排除
                                result['data'][author_name].split(" ")                  # 图源名称不是字符串的排除
                            except:
                                pass
                            else:
                                Other_Source["Author"] = result['data'][author_name]    # 写入图片作者
                                break
                        try:
                            character = result['data']['characters']                    # （简报）写入图片登场人物
                            theme = result['data']['material']                          # （简报）写入图片登场作品
                        except:
                            pass
                        else:
                            Other_Source["Character"] = character    
                            Other_Source["Theme"] = theme
                            # 整理最有可能的登场人物和登场作品（以元组形式放入字典）
                            if (character,theme) in character_possible:
                                character_possible[(character,theme)] += 1
                            else:
                                character_possible[(character,theme)] = 1
                        result_dict["Other_Source"] = Other_Source
                result_list.append(result_dict)                                             # 结果列表生成
        if result_list:                                                                     # 结果非空
            result_list.sort(key=lambda x:x["Similarity"],reverse=True)                     # 将结果列表按相似度从高到低排序，并加上序号
            for i in range(0,len(result_list)):
                result_list[i]["Primary_Key"] = i+1
            # 整理输出简报
            author_possible = result_list[0]["Author"]                                      # 整理最有可能的图作者
            puser_id = ''
            for result in result_list:
                if result["Source"] == "Pixiv":                                             # 由于后续搜图是在P站图库中搜索，因此作者优先选取P站名称
                    Title_possible = result["Pixiv_Source"]["Title"]
                    author_possible = result["Author"]
                    artwork_id = result["Pixiv_Source"]['Pixiv_Id']
                    puser_id = result["Pixiv_Source"]['Author_Pixiv_Id']
                    break
            
            character_possible_list = sorted(character_possible.items(),key=lambda x:x[1],reverse=True)   # 将登场人物/登场作品字典按命中数倒序排序，放入列表

            msg_list = []
            abstract = f"搜索简报：\n\t搜索到 {len(result_list)} 个相关结果，最高相似度为：{result_list[0]['Similarity']:.2f}\n\n\t作者： {author_possible}\n"
            try:                                                                                           # 总体结果中如包含标题，也加到简报里
                abstract = abstract.replace("作者",f"标题： {Title_possible}\n\t作者")
            except:
                pass
            try:
                abstract = "".join((abstract,f"\n\t登场人物： {character_possible_list[0][0][0]}"))
            except:
                pass
            try:
                abstract = "".join((abstract,f"\n\t登场作品： {character_possible_list[0][0][1]}"))
            except:
                pass

            msg_list.append(abstract)                                                                      # 将简报放入输出列表
            for result in result_list:                                          # 将所有搜索结果格式化，放在一起等待合并转发
                image_url = result['Thumbnail_URL']
                image_CQ = f"[CQ:image,file={image_url}]"                       # 将缩略图url转化为缩略图CQ码
                msg_seg = f"{image_CQ}\n{result['Primary_Key']}.  图源：{result['Source']}  (相似度：{result['Similarity']:.2f})\n作者：{result['Author']}\n链接：{result['URL']}"
                try:                                                                                        # 单个结果中如有标题，则加到输出列表中（下同）
                    msg_seg = msg_seg.replace("作者",f"标题：{result['Pixiv_Source']['Title']}\n作者")
                except:
                    pass
                try:
                    if result['Other_Source']['Character']:
                        msg_seg = msg_seg.replace("链接",f"登场人物：{result['Other_Source']['Character']}\n链接")
                except:
                    pass
                try:
                    if result['Other_Source']['Theme']:
                        msg_seg = msg_seg.replace("链接",f"登场作品：{result['Other_Source']['Theme']}\n链接")
                except:
                    pass
                try:
                    paid = result["Pixiv_Source"]['Pixiv_Id']
                    puid = result["Pixiv_Source"]['Author_Pixiv_Id']
                    if paid:
                        msg_seg = msg_seg.replace("链接",f"作品id：{paid}\n链接")
                    if puid:
                        msg_seg = msg_seg.replace("链接",f"画师id：{puid}\n链接")
                except:
                    pass

                msg_list.append(msg_seg)

            param = send_forward_msg(group_id,msg_list)                                                     # 准备调用发送合并转发API，先准备好参数（群号，要发送的消息内容 -> list）
            await bot.call_api('send_group_forward_msg',**param)
            time.sleep(2)
            if puser_id:
                await SendArtwork.puid(str(puser_id),bot,group_id)
        else:                                                                                               # 无结果
            await search_author_matcher.finish("呜呜...轻雪酱没能找到相关结果QAQ")




