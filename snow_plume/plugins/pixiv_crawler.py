import requests
import re
import time
import random
import urllib3
import html
from datetime import datetime,date
from snow_plume.mysql import execute_procedure,execute_sql_query
import os
from urllib.parse import quote
from math import ceil
import sys
import traceback
import asyncio

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # 让控制台忽视verify warning


# 方法地图

''' 0-通用方法
    __sleep_interval__
        功能: 涉及请求服务器的方法需要调用此方法来添加随机间隔访问时间，防止对服务器造成损害
        参数: 
            - mode: Retry (0.3-0.5s) (用于服务器Network Error的重试) | Crawler (1.5-2.5s) (用于获取信息后的停顿)
            - avg, jitter: 用于调整Crawler的时间间隔 (调整为avg±jitter秒)
        统计: 
            - t_Retry: 记录所有Retry累计的总时长

    __print_info__
        功能: 各方法调用此方法以在控制台中打印运行过程信息, Error类型的信息会被记录并在结束时统一输出
        参数: 
            - status: 状态代码, 分INFO、WARNING、ERROR、SUCCESS四类
            - info: 内容信息

'''

''' 1-根据作品id获取作品元数据的方法
    __get_text_artwork__
        功能: (仅第1类方法内部使用) 根据artwork_id获取artwork源代码text_artwork
        特殊情况处理：
            - artwork_id不存在
            - 请求过于频繁 (封ip风险)

    __get_title__
        功能: 根据源代码text_artwork, 提取作品元数据title,description
        特殊情况处理：
            - 处理标题的unicode编码和html字符实体, 处理描述的html字符实体
            - 标题限制长度255, 描述限制长度1024

    __get_popularity__
        功能: 根据源代码text_artwork, 提取作品元数据page_count(作品包含几张图片),like_count,bookmark_count,comment_count,view_count,is_original(作品是否包含'原创'标签)

    __get_upload__
        功能: 根据源代码text_artwork, 提取作品元数据user_id,user_name,upload_date,is_ai
        特殊情况处理：
            - 处理画师名的unicode编码和html字符实体

    __get_tags__
        功能：根据源代码text_artwork, 提取作品元数据tags及其译名trans, 以包含若干(tag,trans)的列表形式返回

    __get_url_p0__
        功能：根据源代码text_artwork, 提取作品元数据url_p0(首张图片的原图链接)
'''

''' 2-业务直接调用的方法
    download_pic
        功能: 根据url_p0,artwork_id和page_count, 将指定作品的原图下载到本地(以"{artwork_id}_p{i}.png"文件名存储到py所在文件夹)
        特殊情况处理：
            - 因网络原因造成的下载失败，将会不断尝试重新下载
        无出参

    search_user
        功能: 根据user_id, 返回其作品id列表及其精选作品id列表
        特殊情况处理：
            - 若user_id不存在, 则user_artwork_list为空
            - pickup_list可能为空
        出参格式: tuple(list)

    search_user_info
        功能: 根据user_id, 返回用户描述信息
        特殊情况处理：
            - 若user_id不存在, 则user_info为空
        出参格式: dict

    __search_tag_info__
        功能: 根据tag名称, 返回该标签的translation, description(日文), parent_tag, siblings_tags列表和children_tags列表, 同时将数据入库
        特殊情况处理:
            - 所有字段均有可能为空(返回空值)
        数据库操作: 
            - ero_tag_info_insert: 将tag, translation, description, parent_tag信息存入/更新到 ero_tags 表中
            - ero_tag_children_insert: 首先在ero_tags表中存入children_tag名称, 再将tag, children_tag信息存入ero_tags_children表
            - ero_tag_siblings_insert: 首先在ero_tags表中存入siblings_tag名称, 再将tag, siblings_tag信息存入ero_tags_siblings表
        出参格式: json

    __search_tag_top_list__
        功能: 根据tag名称, 返回该标签的热门作品id列表, 分permanent(长期热门,一般6条)和recent(近一周热门,一般7条)两种类型
        特殊情况处理:
            - 所有字段均有可能为空(返回空值)
        出参格式: json

    __search_tag_artwork_list__
        功能: 根据tag名称和指定检索结果页码page, 返回标签的作品总数count和该页的作品编号列表artwork_list(每页最多60条)
        特殊情况处理:
            - 所有字段均有可能为空(返回空值)
        出参格式: json

    __gather_meta_artwork__
        功能: 根据artwork_id, 调用第1类方法的所有函数, 向服务器请求作品元数据并写入数据库, 返回collect(作品是否入库)和artwork_meta
        参数: popularity_filter: 是否开启热度过滤模式(默认为True), 如不开启, 则数据不会入库
        特殊情况处理:
            - 热度过滤算法排除低质量作品
        数据库操作:
            - ero_meta_insert: 将artwork_id及其所有元数据(除标签外)存入 ero_meta 表中
            - ero_tag_insert_from_meta: 将artwork_id及标签数据(tag,trans)存入 ero_tags 表和 ero_meta_tag 链接表
        出参格式: collect: bool, artwork_meta: json (包括if_exists和包含所有元数据的content)

    __update_meta_artwork__
        功能: 根据artwork_id(必须为meta库中已有的id), 更新user_name, 标题描述以及热度信息(并且当该内容被删除时更新 is_delete 字段)
        特殊情况处理:
            - 当源代码为空时, 将 ero_meta 表中 is_delete 字段更新为 True
        数据库操作: 
            - ero_meta_update: 将 ero_meta 表中该作品的title,description,user_name,like_count,bookmark_count,comment_count,view_count,update_from_upload,is_delete字段更新到最新
        无出参
'''

''' 3-爬虫程序

    __pixiv_crawler_executor__
        功能: 根据artwork_id_list, 爬取每个作品元数据, 调用__(gather/update)_meta_artwork__方法以新增或更新入库, 统计并返回爬行数据
        特殊情况处理: 
            - 爬取单个作品前, 读取并执行同文件夹下crawler_command文本文档中的Pause和End指令, 若指令要求停止, 则跳转至__pixiv_crawler_end__方法
            - 爬取单个作品前, 检查 pixiv_crawler_discard 表中是否存有该作品, 若在丢弃日志内则直接跳过
            - 爬取单个作品前, 检查 ero_meta 表中是否存有该作品, 以决定是新增入库还是更新原有数据
            - 新增入库前, 默认开启热度过滤模式
            - 若作品不存在, 则会被记录在error_artwork变量中, 等待最后输出
            - 发布超过14天且未达到热度指标的作品会被放入丢弃日志并不再会被爬取, 从而节省爬行资源
        统计:
            - 捕获数量 spot_num (被爬虫捕获的新作品总数,即网络上未被历史丢弃日志或meta数据库记录的作品)
            - 入库数量 insert_num (被加入 meta 表的作品总数)
            - 更新数量 update_num (meta 表中原有并被再次爬取和更新的作品总数)
            - 重复数据 duplicate_num (因在历史丢弃日志中而被爬虫跳过的作品总数)

    pixiv_crawler
        功能: 根据artwork_id_list, user_id_list和tag_list, 将内容拆包并调用对应search函数获取作品id, 随后依次调用executor爬取数据并入库
        特殊情况处理:
            - executor发出End指令时, 进入end流程并结束程序
                - 结束前记录并输出尚未进行的爬取指令(uncrawled变量)
            - 持续传递executor中每次获取的统计数据
            - 若search函数检查到user_id或tag不存在, 则记录在相应的error变量中, 最后同executor负责记录的error_artwork变量一起输出
            - 爬取tag前, 首先查询该tag的历史爬取记录, 导出作品id时回避之前爬取过的内容, 从而节省爬行资源            
            - 爬取tag时, 支持使用tag_page_start参数从某一页开始爬取 (使用该功能时请勿放入其他tag, 此功能通常用于单个tag的断点续爬)
        数据库操作: 
            - pixiv_crawler_tag_query: 从 pixiv_crawler_log_tags 表中查询待爬tag的历史爬取记录, 如有记录, 则
                获取当时爬取的作品总数artwork_count, 并在此次获取的作品总数中直接扣除 (这么做是因为p站搜索默认是按时间倒序排列)
            - pixiv_crawler_tag_update: tag爬取结束时, 在 pixiv_crawler_log_tags 表中写入爬取记录, 下次爬取同一tag时可查询
        参数: 
            - tag_page_start: 所有tag都从该页开始继续爬取
            - if_log: 是否在控制台打印爬取过程日志, 默认为True, 若为False则不打印

    __pixiv_crawler_end__
        功能: 输出本次爬取耗费时间、爬取信息统计(num变量)、错误日志(error变量)和被中断的爬取指令(uncrawled变量)，并结束程序
'''

''' 4-业务方法
    paid
    puid
    setu_get
'''


t_retry = 0
def __sleep_interval__(mode:str = 'R',avg:float = 2, jitter:float = 0.5) -> float:
    '''
    给爬虫添加随机间隔访问时间，防止对服务器造成损害\n
    其值为： avg ± jitter 范围中的随机数\n
    两种模式：R(Retry)模式(固定0.3-0.5秒)；C(Crawler)模式(默认2 ± 0.5秒)
    '''
    global t_retry
    if mode == 'R':
        interval = 0.4 + random.random()*0.1      # 固定在0.3-0.5秒内重试
        __print_info__('INFO',f"将在 {interval:.2f} 秒后重试...")
        t_retry += interval
        time.sleep(interval)
    elif mode == 'C':
        interval = avg + random.random()*jitter*2-jitter
        time.sleep(interval)
    return None

err = []
logging = True
def __print_info__(status:str = "INFO",info:str = ""):
    '''
    爬虫过程中打印过程信息用\n
    四种状态代码：INFO、WARNING、ERROR、SUCCESS\n
    参数示例： "ERROR", f"{artwork_id}：服务器返回了错误代码 {resp.status_code}"\n
    输出示例： <ERROR>   102655324：服务器返回了错误代码 403
    '''
    global err,logging
    if logging:
        print(f"<{status}>".ljust(9," "),f"{info}")
    if status == 'ERROR':
        err.append(info)

    return None

def __get_text_artwork__(artwork_id:str) -> str:
    '''
    根据url_artwork返回网页源代码\n
    (图片url标准格式：https://www.pixiv.net/artworks/#)
    '''
    headers = {
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accpet-Encoding":"gzip, deflate, br",
    "Accept-Language":"zh-CN,zh;q=0.9",
    "Connection":"keep-alive",
    "Cookie":"first_visit_datetime_pc=2022-12-16+22:10:32; p_ab_id=7; p_ab_id_2=5; p_ab_d_id=756704511; yuid_b=IpaUJhA; _gcl_au=1.1.1482174104.1671196256; device_token=ef9d2812486e5adb9031af3a18538145; c_type=23; privacy_policy_notification=0; b_type=1; privacy_policy_agreement=5; __utmv=235335808.|2=login ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=16674673=1^9=p_ab_id=7=1^10=p_ab_id_2=5=1^11=lang=zh=1; login_ever=yes; __utmz=235335808.1672322617.12.2.utmcsr=accounts.pixiv.net|utmccn=(referral)|utmcmd=referral|utmcct=/; _fbp=fb.1.1672495113421.430903723; a_type=1; _gid=GA1.2.1331476772.1673511569; QSI_S_ZN_5hF4My7Ad6VNNAi=v:0:0; __utmc=235335808; tag_view_ranking=Lt-oEicbBr~RTJMXD26Ak~_EOd7bsGyl~7dpqkQl8TH~4QveACRzn3~0xsDLqCEW6~oDcj90OVdf~xk-ZKrS2fa~qkC-JF_MXY~-98s6o2-Rp~7YNsdVv1xN~ziiAzr_h04~tgP8r-gOe_~azESOjmQSV~Yw6zHqltKg~EZQqoW9r8g~Ie2c51_4Sp~HY55MqmzzQ~0ArgFc_Uqc~K8esoIs2eW~KN7uxuR89w~-LBOt020Wk~RcahSSzeRf~P-laY91iQ1~2RR-Wztsl7~MwT2M45J6E~KOnmT1ndWG~Y9WAU0P3Ii~JrZT530U46~faHcYIP1U0~CrFcrMFJzz~QaiOjmwQnI~jH0uD88V6F~y3NlVImyly~ti_E1boC1J~MSNRmMUDgC~1Cu1TkXAKa~IJi4h9ABZq~nQRrj5c6w_~sFPxX8lk4q~99-dVV-h9A~Ltq1hgLZe3~_pwIgrV8TB~5oPIfUbtd6~zyKU3Q5L4C~uW5495Nhg-~eVxus64GZU~aKhT3n4RHZ~OUF2gvwPef~MnGbHeuS94~-7RnTas_L3~k_6Tbz5i0P~GNcgbuT3T-~-sp-9oh8uv~U-RInt8VSZ~rsb55I7upx~65aiw_5Y72~BSlt10mdnm~9ODMAZ0ebV~nIjJS15KLN~lxKly3SVNW~_bee-JX46i~txZ9z5ByU7~b_rY80S-DW~HffPWSkEm-~kdkWnz2DyL~qIDsnltE2o~DAWvkZA06J~0Sds1vVNKR~VeANpZNF_V~Ewxa3CZumI~QwUeUr8yRJ~jk9IzfjZ6n~GT9SxC6pVi~v3nOtgG77A~2R7RYffVfj~kj6L5xhc-l~E99HasFxYj~ZldurqefWy~VN4hvfPTzG~q303ip6Ui5~6rYZ-6JKHq~Itu6dbmwxu~Cr3jSW1VoH~RolC8IrBVO~nRp2ZLPLbj~BtXd1-LPRH~RZFNHsnAvv~YRDwjaiLZn~dg_40nEhSE~rOnsP2Q5UN~NGpDowiVmM~fIMPtFR8GH~I5npEODuUW~Ed_W9RQRe_~_Jc3XITZqL~1yIPTg75Rl~m3EJRa33xU~qAXue2fzEZ~Hvc3ekMyyh; __utma=235335808.816433562.1671196257.1673961160.1673964769.69; __utmt=1; _gat_UA-1830249-3=1; _gat_gtag_UA_76252338_1=1; PHPSESSID=16674673_iS5aA9lyOUB8bX27yI61dwbGRe8fkGiP; _ga_MZ1NL4PHH0=GS1.1.1673965315.4.0.1673965324.0.0.0; _ga_75BBYNYN9J=GS1.1.1673964768.82.1.1673965325.0.0.0; _ga=GA1.1.816433562.1671196257; __utmb=235335808.3.10.1673964769",
    "sec-ch-ua":'"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    "Host":"www.pixiv.net",
    "sec-ch-ua-mobile":"?0",
    "sec-ch-ua-platform":"Windows",
    "Sec-Fetch-Dest":"document",
    "Sec-Fetch-Mode":"navigate",
    "Sec-Fetch-Site":"none",
    "Sec-Fetch-User":"?1",
    "Upgrade-Insecure-Requests":"1",
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    url_artwork = f"https://www.pixiv.net/artworks/{artwork_id}"
    text_get = False
    __print_info__('INFO',f"正在获取 {artwork_id} 作品源代码...")
    while text_get == False:
        try:
            resp = requests.get(url=url_artwork,headers=headers,verify=False)
        except:
            __print_info__('WARNING',f"请求 {artwork_id} 源代码失败！")
            __sleep_interval__()
        else:
            if resp.status_code == 200:         # 请求成功
                text_artwork = resp.text
            elif resp.status_code == 404:       # artwork不存在
                __print_info__('ERROR',f"{artwork_id}：该url指向的内容不存在！\n{url_artwork}")
                text_artwork = ""
            elif resp.status_code == 429:       # 请求次数过多
                __print_info__('ERROR',f'{artwork_id}：服务器返回了错误代码 429，请求过于频繁，建议增加爬取间隔')
                raise Warning("服务器阻止了过于频繁的请求，建议增加爬取间隔")
            else:
                __print_info__('ERROR',f'{artwork_id}：服务器返回了错误代码 {resp.status_code}')
                text_artwork = "" 
            text_get = True
            resp.close()
            if text_artwork:
                __print_info__('INFO',f'作品 {artwork_id} 源代码获取成功！')

    return text_artwork

def __get_title__(artwork_id:str,text_artwork:str) -> tuple:
    '''
    获取图片标题和简介
    '''
    pattern = re.compile(f'"illustId":"{artwork_id}","illustTitle":"(?P<title>.*?)","illustComment":"(?P<description>.*?)","id"',re.S)
    result = pattern.finditer(text_artwork)
    for res in result:
        title = res.group("title")
        try:
            title = eval("u"+"\'"+title+"\'")                       # 将unicode编码转换为中文
        except:
            pass                                                    # title里有引号, 则不转换(少数情况)
        title = html.unescape(title)                                # 转换(&amp;#39)等html字符实体
        title = html.unescape(title)

        description = res.group("description")
        description = html.unescape(description)
        description = html.unescape(description)                    
        description = description.replace("<br />","\n")            # 将html语言"<br />"转义为换行
        pattern_strong = re.compile(r'<strong>(.*?)</strong>',re.S) # 将html语言"<strong>"转义为"<>"
        description = pattern_strong.sub(r' <\1> ',description)
        pattern_url = re.compile(r'<a href=.*?>(.*?)</a>',re.S)     # 将html语言"<a href=''>"转义为链接
        description = pattern_url.sub(r'\1',description)

        title = title[:255]                 # 标题限制长度255
        description = description[:1024]    # 描述限制长度1024

    return (title,description)

def __get_popularity__(text_artwork:str) -> tuple:
    '''
    获取图片页数、点赞/收藏/评论/浏览次数信息以及是否原创角色
    '''
    pattern = re.compile(r'likeData.*?"pageCount":(?P<page_count>.*?),"bookmarkCount":(?P<bookmark_count>.*?),"likeCount":(?P<like_count>.*?),"commentCount":(?P<comment_count>.*?),.*?,"viewCount":(?P<view_count>.*?),.*?,"isOriginal":(?P<is_original>.*?),',re.S)
    result = pattern.finditer(text_artwork)
    for res in result:
        page_count = res.group("page_count")
        bookmark_count = res.group("bookmark_count")
        like_count = res.group("like_count")
        comment_count = res.group("comment_count")
        view_count = res.group("view_count")
        if res.group("is_original") == "true":
            is_original = True
        else:
            is_original = False

    return (page_count,like_count,bookmark_count,comment_count,view_count,is_original)

def __get_upload__(artwork_id:str,text_artwork:str) -> tuple:
    '''
    获取画师的id，昵称，图片上传日期以及是否AI作画
    '''
    pattern = re.compile(f'{{"id":"{artwork_id}".*?"userId":"(?P<UserId>.*?)","userName":"(?P<UserName>.*?)".*?"updateDate":"(?P<UpdateDate>.*?)T.*?"aiType":(?P<AiType>\d)',re.S)
    result = pattern.finditer(text_artwork)
    for res in result:
        user_id = res.group("UserId")
        user_name = res.group("UserName")
        try:
            user_name = eval("u"+"\'"+user_name+"\'")                       # 将unicode编码转换为中文
        except:
            pass                                                            # user_name里有引号, 则不转换(少数情况)
        user_name = html.unescape(user_name)                                # 转换(&amp;#39)等html字符实体
        user_name = html.unescape(user_name)
        upload_date = res.group("UpdateDate")
        if res.group("AiType") == "2":
            is_ai = True
        else:
            is_ai = False
    
    return (user_id,user_name,upload_date,is_ai)

def __get_tags__(artwork_id:str,text_artwork:str) -> list:
    '''
    获取tags及其译名，返回包含若干(tag,trans)的列表
    '''
    pattern_raw = re.compile(f'"illust":{{"{artwork_id}".*?"tags":\[(?P<tags>.*?)\]',re.S)
    result_raw = pattern_raw.finditer(text_artwork)
    for raw in result_raw:
        raw_text = raw.group("tags")
    raw_text_list = raw_text.split("},{")       #e.g. ['{"tag":"R-18","locked":true,"deletable":false,"userId":"68331109","userName":"ゴゴムゴーン"', '"tag":"おんなのこ","locked":true,"deletable":false,"userId":"68331109","translation":{"en":"girl"},"userName":"ゴゴムゴーン"', '"tag":"異種姦","locked":true,"deletable":false,"userId":"68331109","translation":{"en":"异种姦"},"userName":"ゴゴムゴーン"', '"tag":"ゴブリン","locked":true,"deletable":false,"userId":"68331109","translation":{"en":"哥布林"},"userName":"ゴゴムゴーン"}']
    tag_list_raw = []
    for raw_text in raw_text_list:
        if raw_text:
            tag_pattern = re.compile(r'"tag":"(?P<tag>.*?)"',re.S)
            trans_pattern = re.compile(r'"translation":{.*?:"(?P<trans>.*?)"',re.S)     
            raw_tag = tag_pattern.finditer(raw_text)
            raw_trans = trans_pattern.finditer(raw_text)
            tag = None
            trans = None
            for tg in raw_tag:
                tag = tg.group("tag")
                tag = tag.replace("\\u0027","'")     # 将tag的unicode编码转为符号'
            for trs in raw_trans:
                trans = trs.group("trans")
                trans = trans.replace("\\u0027","'")
            tag_list_raw.append((tag,trans))
        else:
            tag_list_raw = []

    return tag_list_raw

def __get_url_p0__(text_artwork:str) -> str:
    '''
    获取首张原图链接
    '''
    pattern = re.compile(r'"original":"(?P<url_p0>.*?)"',re.S)
    result = pattern.finditer(text_artwork)
    for res in result:
        url_p0 = res.group("url_p0")

    return url_p0

async def download_pic(artwork_id:str,path:str = 'data\\setu\\',url_p0:str = '',page_count:str = '',is_ai:int = None,is_r18:int = None,if_log:bool = False) -> bool:
    '''
    根据url_p0,artwork_id和page_count, 将指定作品的原图下载到本地
    '''
    global logging
    logging = if_log    # 决定是否要在控制台打印日志
    # 获取必要信息url_p0和page_count
    # 首先查询数据库中是否有相应信息
    if not (url_p0 and page_count and is_ai and is_r18):
        proc = execute_procedure("ero_meta_fetch",args_in=[f'{artwork_id}'],args_out=['title','description','user_id','user_name','upload_date','update_from_upload','url_p0','page_count','like_count','bookmark_count','comment_count','view_count','is_original','is_ai','is_r18','is_blocked','is_delete'])
        result = proc.proc()
        if result['Code'] == 200:
            if result['title']:
                is_ai = result['is_ai']
                is_r18 = result['is_r18']
                url_p0 = result['url_p0']
                page_count = result['page_count']
            else:   # 如没有则调用__gather_meta_artwork__方法访问服务器获取信息
                foo,meta = __gather_meta_artwork__(artwork_id)
                is_ai = meta['is_ai']
                is_r18 = meta['is_r18']
                url_p0 = meta['url_p0']
                page_count = meta['page_count']
    
    # 请求服务器
    headers = {
        "Accept":"image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accpet-Encoding":"gzip, deflate, br",
        "Accept-Language":"zh-CN,zh;q=0.9",
        "Connection":"keep-alive",
        "Host":"i.pximg.net",
        "Referer":"https://www.pixiv.net/",
        "Cookie":"first_visit_datetime_pc=2022-12-16+22:10:32; p_ab_id=7; p_ab_id_2=5; p_ab_d_id=756704511; yuid_b=IpaUJhA; _gcl_au=1.1.1482174104.1671196256; device_token=ef9d2812486e5adb9031af3a18538145; c_type=23; privacy_policy_notification=0; b_type=1; privacy_policy_agreement=5; __utmv=235335808.|2=login ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=16674673=1^9=p_ab_id=7=1^10=p_ab_id_2=5=1^11=lang=zh=1; login_ever=yes; __utmz=235335808.1672322617.12.2.utmcsr=accounts.pixiv.net|utmccn=(referral)|utmcmd=referral|utmcct=/; _fbp=fb.1.1672495113421.430903723; a_type=1; _gid=GA1.2.1331476772.1673511569; QSI_S_ZN_5hF4My7Ad6VNNAi=v:0:0; __utmc=235335808; tag_view_ranking=Lt-oEicbBr~RTJMXD26Ak~_EOd7bsGyl~7dpqkQl8TH~4QveACRzn3~0xsDLqCEW6~oDcj90OVdf~xk-ZKrS2fa~qkC-JF_MXY~-98s6o2-Rp~7YNsdVv1xN~ziiAzr_h04~tgP8r-gOe_~azESOjmQSV~Yw6zHqltKg~EZQqoW9r8g~Ie2c51_4Sp~HY55MqmzzQ~0ArgFc_Uqc~K8esoIs2eW~KN7uxuR89w~-LBOt020Wk~RcahSSzeRf~P-laY91iQ1~2RR-Wztsl7~MwT2M45J6E~KOnmT1ndWG~Y9WAU0P3Ii~JrZT530U46~faHcYIP1U0~CrFcrMFJzz~QaiOjmwQnI~jH0uD88V6F~y3NlVImyly~ti_E1boC1J~MSNRmMUDgC~1Cu1TkXAKa~IJi4h9ABZq~nQRrj5c6w_~sFPxX8lk4q~99-dVV-h9A~Ltq1hgLZe3~_pwIgrV8TB~5oPIfUbtd6~zyKU3Q5L4C~uW5495Nhg-~eVxus64GZU~aKhT3n4RHZ~OUF2gvwPef~MnGbHeuS94~-7RnTas_L3~k_6Tbz5i0P~GNcgbuT3T-~-sp-9oh8uv~U-RInt8VSZ~rsb55I7upx~65aiw_5Y72~BSlt10mdnm~9ODMAZ0ebV~nIjJS15KLN~lxKly3SVNW~_bee-JX46i~txZ9z5ByU7~b_rY80S-DW~HffPWSkEm-~kdkWnz2DyL~qIDsnltE2o~DAWvkZA06J~0Sds1vVNKR~VeANpZNF_V~Ewxa3CZumI~QwUeUr8yRJ~jk9IzfjZ6n~GT9SxC6pVi~v3nOtgG77A~2R7RYffVfj~kj6L5xhc-l~E99HasFxYj~ZldurqefWy~VN4hvfPTzG~q303ip6Ui5~6rYZ-6JKHq~Itu6dbmwxu~Cr3jSW1VoH~RolC8IrBVO~nRp2ZLPLbj~BtXd1-LPRH~RZFNHsnAvv~YRDwjaiLZn~dg_40nEhSE~rOnsP2Q5UN~NGpDowiVmM~fIMPtFR8GH~I5npEODuUW~Ed_W9RQRe_~_Jc3XITZqL~1yIPTg75Rl~m3EJRa33xU~qAXue2fzEZ~Hvc3ekMyyh; __utma=235335808.816433562.1671196257.1673961160.1673964769.69; __utmt=1; _gat_UA-1830249-3=1; _gat_gtag_UA_76252338_1=1; PHPSESSID=16674673_iS5aA9lyOUB8bX27yI61dwbGRe8fkGiP; _ga_MZ1NL4PHH0=GS1.1.1673965315.4.0.1673965324.0.0.0; _ga_75BBYNYN9J=GS1.1.1673964768.82.1.1673965325.0.0.0; _ga=GA1.1.816433562.1671196257; __utmb=235335808.3.10.1673964769",
        "sec-ch-ua":'"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        "sec-ch-ua-mobile":"?0",
        "sec-ch-ua-platform":"Windows",
        "Sec-Fetch-Dest":"image",
        "Sec-Fetch-Mode":"no-cors",
        "Sec-Fetch-Site":"cross-site",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    error_list = []
    page_count = int(page_count)
    __print_info__('INFO',f'作品 {artwork_id} 包含 {page_count} 张图片，开始下载...')
    for i in range(page_count):
        if i != 0:
            url_p0 = url_p0.replace(f'{artwork_id}_p{i-1}',f'{artwork_id}_p{i}')
        try:
            resp = requests.get(url=url_p0,headers=headers,verify=False)
        except:
            error_list.append(url_p0)  # 如爬取失败，则将url暂存至error_list等待重新爬取
            __print_info__('WARNING',f'图片爬取失败！待重试...错误链接：{url_p0}')
        else:
            # 文件名格式: 特殊标签_作品ID_第n页.png
            file_name = f"_{artwork_id}_p{i}"
            if is_ai:
                file_name = "ai" + file_name
            if is_r18:
                if is_ai:
                    file_name = "r18&" + file_name
                else:
                    file_name = "r18" + file_name
            with open(f"{path}{file_name}.png","wb+") as f:
                f.write(resp.content)
            await asyncio.sleep(random.random()+1)
            __print_info__('INFO',f'图片爬取成功！剩余 {page_count-i-1} 张图片')
            resp.close()
    # 重新爬取失败的内容
    while error_list:
        __print_info__('INFO',f'正在处理爬取失败列表，待爬取列表如下：\n{error_list}')
        for url_p0_error in error_list:
            try:
                resp = requests.get(url=url_p0_error,headers=headers,verify=False)
            except:
                __print_info__('WARNING',f'爬取图片失败！错误链接：{url_p0_error}')
                __sleep_interval__()
                continue
            else:
                file_name = "_" + url_p0_error.split("/")[-1].split(".")[0]
                if is_ai:
                    file_name = "ai" + file_name
                if is_r18:
                    if is_ai:
                        file_name = "r18&" + file_name
                    else:
                        file_name = "r18" + file_name
                with open(f"{path}{file_name}.png","wb+") as f:
                    f.write(resp.content)
                error_list.remove(url_p0_error)
                __print_info__('INFO',f'重新爬取图片成功！剩余 {len(error_list)} 张图片')
                resp.close()
                await asyncio.sleep(random.random()+1)
    __print_info__('SUCCESS',f'作品 {artwork_id} 原图下载完毕！共下载 {page_count} 张图片')

    return True

def get_focus_tags(artwork_id_list,if_log=False) -> list:
    '''
    根据画师(最多)前五十张作品id, 获取其常见标签
    '''
    global logging
    logging = if_log

    url = 'https://www.pixiv.net/ajax/tags/frequent/illust?'
    headers = {
        "Accept":"application/json",
        "Accpet-Encoding":"gzip, deflate, br",
        "Accept-Language":"zh-CN,zh;q=0.9",
        "Connection":"keep-alive",
        "Host":"www.pixiv.net",
        "Referer":f"https://www.pixiv.net/",
        "Cookie":"first_visit_datetime_pc=2022-12-16+22:10:32; p_ab_id=7; p_ab_id_2=5; p_ab_d_id=756704511; yuid_b=IpaUJhA; _gcl_au=1.1.1482174104.1671196256; device_token=ef9d2812486e5adb9031af3a18538145; c_type=23; privacy_policy_notification=0; b_type=1; privacy_policy_agreement=5; __utmv=235335808.|2=login ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=16674673=1^9=p_ab_id=7=1^10=p_ab_id_2=5=1^11=lang=zh=1; login_ever=yes; __utmz=235335808.1672322617.12.2.utmcsr=accounts.pixiv.net|utmccn=(referral)|utmcmd=referral|utmcct=/; _fbp=fb.1.1672495113421.430903723; a_type=1; _gid=GA1.2.1331476772.1673511569; QSI_S_ZN_5hF4My7Ad6VNNAi=v:0:0; __utmc=235335808; tag_view_ranking=Lt-oEicbBr~RTJMXD26Ak~_EOd7bsGyl~7dpqkQl8TH~4QveACRzn3~0xsDLqCEW6~oDcj90OVdf~xk-ZKrS2fa~qkC-JF_MXY~-98s6o2-Rp~7YNsdVv1xN~ziiAzr_h04~tgP8r-gOe_~azESOjmQSV~Yw6zHqltKg~EZQqoW9r8g~Ie2c51_4Sp~HY55MqmzzQ~0ArgFc_Uqc~K8esoIs2eW~KN7uxuR89w~-LBOt020Wk~RcahSSzeRf~P-laY91iQ1~2RR-Wztsl7~MwT2M45J6E~KOnmT1ndWG~Y9WAU0P3Ii~JrZT530U46~faHcYIP1U0~CrFcrMFJzz~QaiOjmwQnI~jH0uD88V6F~y3NlVImyly~ti_E1boC1J~MSNRmMUDgC~1Cu1TkXAKa~IJi4h9ABZq~nQRrj5c6w_~sFPxX8lk4q~99-dVV-h9A~Ltq1hgLZe3~_pwIgrV8TB~5oPIfUbtd6~zyKU3Q5L4C~uW5495Nhg-~eVxus64GZU~aKhT3n4RHZ~OUF2gvwPef~MnGbHeuS94~-7RnTas_L3~k_6Tbz5i0P~GNcgbuT3T-~-sp-9oh8uv~U-RInt8VSZ~rsb55I7upx~65aiw_5Y72~BSlt10mdnm~9ODMAZ0ebV~nIjJS15KLN~lxKly3SVNW~_bee-JX46i~txZ9z5ByU7~b_rY80S-DW~HffPWSkEm-~kdkWnz2DyL~qIDsnltE2o~DAWvkZA06J~0Sds1vVNKR~VeANpZNF_V~Ewxa3CZumI~QwUeUr8yRJ~jk9IzfjZ6n~GT9SxC6pVi~v3nOtgG77A~2R7RYffVfj~kj6L5xhc-l~E99HasFxYj~ZldurqefWy~VN4hvfPTzG~q303ip6Ui5~6rYZ-6JKHq~Itu6dbmwxu~Cr3jSW1VoH~RolC8IrBVO~nRp2ZLPLbj~BtXd1-LPRH~RZFNHsnAvv~YRDwjaiLZn~dg_40nEhSE~rOnsP2Q5UN~NGpDowiVmM~fIMPtFR8GH~I5npEODuUW~Ed_W9RQRe_~_Jc3XITZqL~1yIPTg75Rl~m3EJRa33xU~qAXue2fzEZ~Hvc3ekMyyh; __utma=235335808.816433562.1671196257.1673961160.1673964769.69; __utmt=1; _gat_UA-1830249-3=1; _gat_gtag_UA_76252338_1=1; PHPSESSID=16674673_iS5aA9lyOUB8bX27yI61dwbGRe8fkGiP; _ga_MZ1NL4PHH0=GS1.1.1673965315.4.0.1673965324.0.0.0; _ga_75BBYNYN9J=GS1.1.1673964768.82.1.1673965325.0.0.0; _ga=GA1.1.816433562.1671196257; __utmb=235335808.3.10.1673964769",
        "sec-ch-ua":'"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        "sec-ch-ua-mobile":"?0",
        "sec-ch-ua-platform":"Windows",
        "Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors",
        "Sec-Fetch-Site":"same-origin",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    for artwork_id in artwork_id_list:
        url = url + f'ids%5B%5D={artwork_id}&'
    url = url + 'lang=zh'
    focus_tag_list = []
    result_get = False
    __print_info__('INFO',f'正在获取常见标签...')
    while result_get == False:
        try:
            resp = requests.get(url=url,headers=headers,verify=False,)
        except:
            __print_info__('WARNING',f'请求常见标签失败！')
            __sleep_interval__()
        else:
            result = resp.json()
            resp.close()
            if result["error"] == True:
                __print_info__('ERROR',f'常见标签不存在！')
                break
            else:
                # 获取常见标签
                focus_tags = result['body']
                for tag_dict in focus_tags:
                    if tag_dict['tag_translation']:
                        focus_tag_list.append(f"{tag_dict['tag']}({tag_dict['tag_translation']})")
                    else:
                        focus_tag_list.append(f"{tag_dict['tag']}")
            result_get = True
            __print_info__('INFO',f'常见标签获取成功！')

    return focus_tag_list

def search_user(user_id:str, if_log:bool = False) -> tuple:
    '''
    根据作者id，返回作者是否存在及其作品id的list
    '''
    global logging
    logging = if_log    # 决定是否要在控制台打印日志

    user_artwork_list = []
    pickup_list = []
    url_user = f"https://www.pixiv.net/ajax/user/{quote(user_id)}/profile/all?lang=zh"
    headers = {
        "Accept":"application/json",
        "Accpet-Encoding":"gzip, deflate, br",
        "Accept-Language":"zh-CN,zh;q=0.9",
        "Connection":"keep-alive",
        "Host":"www.pixiv.net",
        "Referer":f"https://www.pixiv.net/users/{quote(user_id)}",
        "Cookie":"first_visit_datetime_pc=2022-12-16+22:10:32; p_ab_id=7; p_ab_id_2=5; p_ab_d_id=756704511; yuid_b=IpaUJhA; _gcl_au=1.1.1482174104.1671196256; device_token=ef9d2812486e5adb9031af3a18538145; c_type=23; privacy_policy_notification=0; b_type=1; privacy_policy_agreement=5; __utmv=235335808.|2=login ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=16674673=1^9=p_ab_id=7=1^10=p_ab_id_2=5=1^11=lang=zh=1; login_ever=yes; __utmz=235335808.1672322617.12.2.utmcsr=accounts.pixiv.net|utmccn=(referral)|utmcmd=referral|utmcct=/; _fbp=fb.1.1672495113421.430903723; a_type=1; _gid=GA1.2.1331476772.1673511569; QSI_S_ZN_5hF4My7Ad6VNNAi=v:0:0; __utmc=235335808; tag_view_ranking=Lt-oEicbBr~RTJMXD26Ak~_EOd7bsGyl~7dpqkQl8TH~4QveACRzn3~0xsDLqCEW6~oDcj90OVdf~xk-ZKrS2fa~qkC-JF_MXY~-98s6o2-Rp~7YNsdVv1xN~ziiAzr_h04~tgP8r-gOe_~azESOjmQSV~Yw6zHqltKg~EZQqoW9r8g~Ie2c51_4Sp~HY55MqmzzQ~0ArgFc_Uqc~K8esoIs2eW~KN7uxuR89w~-LBOt020Wk~RcahSSzeRf~P-laY91iQ1~2RR-Wztsl7~MwT2M45J6E~KOnmT1ndWG~Y9WAU0P3Ii~JrZT530U46~faHcYIP1U0~CrFcrMFJzz~QaiOjmwQnI~jH0uD88V6F~y3NlVImyly~ti_E1boC1J~MSNRmMUDgC~1Cu1TkXAKa~IJi4h9ABZq~nQRrj5c6w_~sFPxX8lk4q~99-dVV-h9A~Ltq1hgLZe3~_pwIgrV8TB~5oPIfUbtd6~zyKU3Q5L4C~uW5495Nhg-~eVxus64GZU~aKhT3n4RHZ~OUF2gvwPef~MnGbHeuS94~-7RnTas_L3~k_6Tbz5i0P~GNcgbuT3T-~-sp-9oh8uv~U-RInt8VSZ~rsb55I7upx~65aiw_5Y72~BSlt10mdnm~9ODMAZ0ebV~nIjJS15KLN~lxKly3SVNW~_bee-JX46i~txZ9z5ByU7~b_rY80S-DW~HffPWSkEm-~kdkWnz2DyL~qIDsnltE2o~DAWvkZA06J~0Sds1vVNKR~VeANpZNF_V~Ewxa3CZumI~QwUeUr8yRJ~jk9IzfjZ6n~GT9SxC6pVi~v3nOtgG77A~2R7RYffVfj~kj6L5xhc-l~E99HasFxYj~ZldurqefWy~VN4hvfPTzG~q303ip6Ui5~6rYZ-6JKHq~Itu6dbmwxu~Cr3jSW1VoH~RolC8IrBVO~nRp2ZLPLbj~BtXd1-LPRH~RZFNHsnAvv~YRDwjaiLZn~dg_40nEhSE~rOnsP2Q5UN~NGpDowiVmM~fIMPtFR8GH~I5npEODuUW~Ed_W9RQRe_~_Jc3XITZqL~1yIPTg75Rl~m3EJRa33xU~qAXue2fzEZ~Hvc3ekMyyh; __utma=235335808.816433562.1671196257.1673961160.1673964769.69; __utmt=1; _gat_UA-1830249-3=1; _gat_gtag_UA_76252338_1=1; PHPSESSID=16674673_iS5aA9lyOUB8bX27yI61dwbGRe8fkGiP; _ga_MZ1NL4PHH0=GS1.1.1673965315.4.0.1673965324.0.0.0; _ga_75BBYNYN9J=GS1.1.1673964768.82.1.1673965325.0.0.0; _ga=GA1.1.816433562.1671196257; __utmb=235335808.3.10.1673964769",
        "sec-ch-ua":'"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        "sec-ch-ua-mobile":"?0",
        "sec-ch-ua-platform":"Windows",
        "Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors",
        "Sec-Fetch-Site":"same-origin",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    paras = {"lang":"zh"}
    list_get = False
    __print_info__('INFO',f'正在获取用户 {user_id} 作品列表...')
    while list_get == False:
        try:
            resp = requests.get(url=url_user,headers=headers,params=paras,verify=False,)
        except:
            __print_info__('WARNING',f'请求用户 {user_id} 作品列表失败！')
            __sleep_interval__()
        else:
            result = resp.json()
            resp.close()
            if result["error"] == True:
                __print_info__('ERROR',f'用户 {user_id} 不存在！')
                break
            else:
                # 获取作品列表
                if result["body"]["illusts"]:
                    user_artwork_list = list(result["body"]["illusts"].keys())
                    # 获取精选作品列表(可能为空)
                    if result["body"]["pickup"]:
                        for pickup_artwork in result["body"]["pickup"]:
                            if "id" in pickup_artwork:
                                pickup_list.append(pickup_artwork["id"])
                    __print_info__('INFO',f'用户 {user_id} 作品列表获取成功！共 {len(user_artwork_list)} 篇作品')
                else:
                    __print_info__('ERROR',f'用户 {user_id} 没有作品！')
            list_get = True

    return user_artwork_list,pickup_list

def search_user_info(user_id:str,if_log:bool = False) -> dict:
    global logging
    logging = if_log    # 决定是否要在控制台打印日志

    user_info = {}
    url_user_info = f"https://www.pixiv.net/ajax/user/{quote(user_id)}/profile/top"
    headers = {
        "Accept":"application/json",
        "Accpet-Encoding":"gzip, deflate, br",
        "Accept-Language":"zh-CN,zh;q=0.9",
        "Connection":"keep-alive",
        "Host":"www.pixiv.net",
        "Referer":f"https://www.pixiv.net/users/{quote(user_id)}",
        "Cookie":"first_visit_datetime_pc=2022-12-16+22:10:32; p_ab_id=7; p_ab_id_2=5; p_ab_d_id=756704511; yuid_b=IpaUJhA; _gcl_au=1.1.1482174104.1671196256; device_token=ef9d2812486e5adb9031af3a18538145; c_type=23; privacy_policy_notification=0; b_type=1; privacy_policy_agreement=5; __utmv=235335808.|2=login ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=16674673=1^9=p_ab_id=7=1^10=p_ab_id_2=5=1^11=lang=zh=1; login_ever=yes; __utmz=235335808.1672322617.12.2.utmcsr=accounts.pixiv.net|utmccn=(referral)|utmcmd=referral|utmcct=/; _fbp=fb.1.1672495113421.430903723; a_type=1; _gid=GA1.2.1331476772.1673511569; QSI_S_ZN_5hF4My7Ad6VNNAi=v:0:0; __utmc=235335808; tag_view_ranking=Lt-oEicbBr~RTJMXD26Ak~_EOd7bsGyl~7dpqkQl8TH~4QveACRzn3~0xsDLqCEW6~oDcj90OVdf~xk-ZKrS2fa~qkC-JF_MXY~-98s6o2-Rp~7YNsdVv1xN~ziiAzr_h04~tgP8r-gOe_~azESOjmQSV~Yw6zHqltKg~EZQqoW9r8g~Ie2c51_4Sp~HY55MqmzzQ~0ArgFc_Uqc~K8esoIs2eW~KN7uxuR89w~-LBOt020Wk~RcahSSzeRf~P-laY91iQ1~2RR-Wztsl7~MwT2M45J6E~KOnmT1ndWG~Y9WAU0P3Ii~JrZT530U46~faHcYIP1U0~CrFcrMFJzz~QaiOjmwQnI~jH0uD88V6F~y3NlVImyly~ti_E1boC1J~MSNRmMUDgC~1Cu1TkXAKa~IJi4h9ABZq~nQRrj5c6w_~sFPxX8lk4q~99-dVV-h9A~Ltq1hgLZe3~_pwIgrV8TB~5oPIfUbtd6~zyKU3Q5L4C~uW5495Nhg-~eVxus64GZU~aKhT3n4RHZ~OUF2gvwPef~MnGbHeuS94~-7RnTas_L3~k_6Tbz5i0P~GNcgbuT3T-~-sp-9oh8uv~U-RInt8VSZ~rsb55I7upx~65aiw_5Y72~BSlt10mdnm~9ODMAZ0ebV~nIjJS15KLN~lxKly3SVNW~_bee-JX46i~txZ9z5ByU7~b_rY80S-DW~HffPWSkEm-~kdkWnz2DyL~qIDsnltE2o~DAWvkZA06J~0Sds1vVNKR~VeANpZNF_V~Ewxa3CZumI~QwUeUr8yRJ~jk9IzfjZ6n~GT9SxC6pVi~v3nOtgG77A~2R7RYffVfj~kj6L5xhc-l~E99HasFxYj~ZldurqefWy~VN4hvfPTzG~q303ip6Ui5~6rYZ-6JKHq~Itu6dbmwxu~Cr3jSW1VoH~RolC8IrBVO~nRp2ZLPLbj~BtXd1-LPRH~RZFNHsnAvv~YRDwjaiLZn~dg_40nEhSE~rOnsP2Q5UN~NGpDowiVmM~fIMPtFR8GH~I5npEODuUW~Ed_W9RQRe_~_Jc3XITZqL~1yIPTg75Rl~m3EJRa33xU~qAXue2fzEZ~Hvc3ekMyyh; __utma=235335808.816433562.1671196257.1673961160.1673964769.69; __utmt=1; _gat_UA-1830249-3=1; _gat_gtag_UA_76252338_1=1; PHPSESSID=16674673_iS5aA9lyOUB8bX27yI61dwbGRe8fkGiP; _ga_MZ1NL4PHH0=GS1.1.1673965315.4.0.1673965324.0.0.0; _ga_75BBYNYN9J=GS1.1.1673964768.82.1.1673965325.0.0.0; _ga=GA1.1.816433562.1671196257; __utmb=235335808.3.10.1673964769",
        "sec-ch-ua":'"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        "sec-ch-ua-mobile":"?0",
        "sec-ch-ua-platform":"Windows",
        "Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors",
        "Sec-Fetch-Site":"same-origin",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    paras = {"lang":"zh"}
    info_get = False
    __print_info__('INFO',f'正在获取用户 {user_id} 描述信息...')
    while info_get == False:
        try:
            resp = requests.get(url=url_user_info,headers=headers,params=paras,verify=False)
        except:
            __print_info__('WARNING',f'请求用户 {user_id} 描述信息！')
            __sleep_interval__()
        else:
            result = resp.json()
            resp.close()
            if result["error"] == True:
                __print_info__('ERROR',f'用户 {user_id} 不存在！')
                break
            else:
                # 获取用户描述
                info = result["body"]["extraData"]["meta"]["ogp"]
                user_info['user_name'] = info['title']
                user_info['description'] = info['description']
                user_info['image'] = info['image']

            info_get = True
            __print_info__('INFO',f'用户 {user_id} 描述信息获取成功! ')

    return user_info

def __search_tag_info__(tag:str) -> dict:
    '''
    获取并返回tag的基本信息，同时将tag信息写入数据库\n
    ----------
    返回示例(各字段可能为空)：\n
    {'translation': 'Nijika Ijichi',\n
     'description': '『ぼっち・ざ・ろっく！』の登場人物で、「結束バンド」の陽キャ(？)ドラマーである。',\n
     'parent_tag': 'ぼっち・ざ・ろっく!',\n
     'siblings_tags': ['後藤ひとり', '喜多郁代'],\n
     'children_tags': []}
    '''
    tag_info = {
        "translation":"",
        "description":"",
        "parent_tag":"",
        "siblings_tags":[],
        "children_tags":[]
        }

    url_info = "https://www.pixiv.net/ajax/search/tags/" + quote(tag)
    headers = {
        "accept":"application/json",
        "Accept-Encoding":"gzip, deflate, br",
        "Accept_Language":"zh-CN,zh;q=0.9",
        "Connection":"keep-alive",
        "Host":"www.pixiv.net",
        "Referer":"https://www.pixiv.net/tags/"+quote(tag),
        "Cookie":"first_visit_datetime_pc=2022-12-16+22:10:32; p_ab_id=7; p_ab_id_2=5; p_ab_d_id=756704511; yuid_b=IpaUJhA; _gcl_au=1.1.1482174104.1671196256; device_token=ef9d2812486e5adb9031af3a18538145; c_type=23; privacy_policy_notification=0; b_type=1; privacy_policy_agreement=5; __utmv=235335808.|2=login ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=16674673=1^9=p_ab_id=7=1^10=p_ab_id_2=5=1^11=lang=zh=1; login_ever=yes; __utmz=235335808.1672322617.12.2.utmcsr=accounts.pixiv.net|utmccn=(referral)|utmcmd=referral|utmcct=/; _fbp=fb.1.1672495113421.430903723; a_type=1; _gid=GA1.2.1331476772.1673511569; QSI_S_ZN_5hF4My7Ad6VNNAi=v:0:0; __utmc=235335808; tag_view_ranking=Lt-oEicbBr~RTJMXD26Ak~_EOd7bsGyl~7dpqkQl8TH~4QveACRzn3~0xsDLqCEW6~oDcj90OVdf~xk-ZKrS2fa~qkC-JF_MXY~-98s6o2-Rp~7YNsdVv1xN~ziiAzr_h04~tgP8r-gOe_~azESOjmQSV~Yw6zHqltKg~EZQqoW9r8g~Ie2c51_4Sp~HY55MqmzzQ~0ArgFc_Uqc~K8esoIs2eW~KN7uxuR89w~-LBOt020Wk~RcahSSzeRf~P-laY91iQ1~2RR-Wztsl7~MwT2M45J6E~KOnmT1ndWG~Y9WAU0P3Ii~JrZT530U46~faHcYIP1U0~CrFcrMFJzz~QaiOjmwQnI~jH0uD88V6F~y3NlVImyly~ti_E1boC1J~MSNRmMUDgC~1Cu1TkXAKa~IJi4h9ABZq~nQRrj5c6w_~sFPxX8lk4q~99-dVV-h9A~Ltq1hgLZe3~_pwIgrV8TB~5oPIfUbtd6~zyKU3Q5L4C~uW5495Nhg-~eVxus64GZU~aKhT3n4RHZ~OUF2gvwPef~MnGbHeuS94~-7RnTas_L3~k_6Tbz5i0P~GNcgbuT3T-~-sp-9oh8uv~U-RInt8VSZ~rsb55I7upx~65aiw_5Y72~BSlt10mdnm~9ODMAZ0ebV~nIjJS15KLN~lxKly3SVNW~_bee-JX46i~txZ9z5ByU7~b_rY80S-DW~HffPWSkEm-~kdkWnz2DyL~qIDsnltE2o~DAWvkZA06J~0Sds1vVNKR~VeANpZNF_V~Ewxa3CZumI~QwUeUr8yRJ~jk9IzfjZ6n~GT9SxC6pVi~v3nOtgG77A~2R7RYffVfj~kj6L5xhc-l~E99HasFxYj~ZldurqefWy~VN4hvfPTzG~q303ip6Ui5~6rYZ-6JKHq~Itu6dbmwxu~Cr3jSW1VoH~RolC8IrBVO~nRp2ZLPLbj~BtXd1-LPRH~RZFNHsnAvv~YRDwjaiLZn~dg_40nEhSE~rOnsP2Q5UN~NGpDowiVmM~fIMPtFR8GH~I5npEODuUW~Ed_W9RQRe_~_Jc3XITZqL~1yIPTg75Rl~m3EJRa33xU~qAXue2fzEZ~Hvc3ekMyyh; __utma=235335808.816433562.1671196257.1673961160.1673964769.69; __utmt=1; _gat_UA-1830249-3=1; _gat_gtag_UA_76252338_1=1; PHPSESSID=16674673_iS5aA9lyOUB8bX27yI61dwbGRe8fkGiP; _ga_MZ1NL4PHH0=GS1.1.1673965315.4.0.1673965324.0.0.0; _ga_75BBYNYN9J=GS1.1.1673964768.82.1.1673965325.0.0.0; _ga=GA1.1.816433562.1671196257; __utmb=235335808.3.10.1673964769",
        "sec-ch-ua":'"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        "sec-ch-ua-mobile":"?0",
        "sec-ch-ua-platform":"Windows",
        "Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors",
        "Sec-Fetch-Site":"same-origin",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    paras = {"lang":"zh"}
    info_get = False
    __print_info__('INFO',f'正在获取标签 {tag} 基本信息...')
    while info_get == False:
        try:
            resp = requests.get(url=url_info,headers=headers,params=paras,verify=False)
        except:
            __print_info__('WARNING',f"请求 {tag} 标签信息失败！")
            __sleep_interval__()
        else:
            result_description = resp.json()
            resp.close()
            # 获取译名
            try:
                translation = result_description['body']['tagTranslation'][f'{tag}']
            except:
                translation = ''
            else:
                if 'zh' in translation and translation['zh']:
                    translation = translation['zh']
                elif 'zh_tw' in translation and translation['zh_tw']:
                    translation = translation['zh_tw']
                elif 'en' in translation and translation['en']:
                    translation = translation['en']
                if not translation:
                    __print_info__("WARNING",f"标签 {tag} 没有相应描述")
            # 获取日文标签描述
            try:
                description = result_description['body']['pixpedia']['abstract']
            except :
                description = ''
            # 获取父标签
            try:
                parent_tag = result_description['body']['pixpedia']['parentTag']
            except:
                parent_tag = ''
            # 获取姊妹标签集
            try:
                siblings_tags = result_description['body']['pixpedia']['siblingsTags']
            except:
                siblings_tags = []
            # 获取子标签集
            try:
                children_tags = result_description['body']['pixpedia']['childrenTags']
            except:
                children_tags = []
            # 输出标签基本信息
            tag_info = {
                "translation":translation,
                "description":description,
                "parent_tag":parent_tag,
                "siblings_tags":siblings_tags,
                "children_tags":children_tags
                }
            info_get = True
            __print_info__("SUCCESS",f"标签 {tag} 信息获取成功！")
            # 将tag基本信息、相关标签信息写入数据库
            error = False
            proc = execute_procedure('ero_tag_info_insert',args_in=[tag,translation,description,parent_tag],args_out=None)
            proc_result = proc.proc()
            if proc_result:
                __print_info__("ERROR",f"写入标签 {tag} 信息时出错，错误代码：{proc_result['Code']}")
                error = True
            for children_tag in children_tags:
                proc = execute_procedure('ero_tag_children_insert',args_in=[tag,children_tag],args_out=None)
                proc_result = proc.proc()
                if proc_result:
                    __print_info__("ERROR",f"写入 {tag} 子标签 {children_tag} 时出错，错误代码：{proc_result['Code']}")
                    error = True
            for siblings_tag in siblings_tags:
                proc = execute_procedure('ero_tag_siblings_insert',args_in=[tag,siblings_tag],args_out=None)
                proc_result = proc.proc()
                if proc_result:
                    __print_info__("ERROR",f"写入 {tag} 姊妹标签 {siblings_tag} 时出错，错误代码：{proc_result['Code']}")     
                    error = True           
            if error == False:
                __print_info__("SUCCESS",f"标签 {tag} 的信息已写入")

    return tag_info

def __search_tag_top_list__(tag:str) -> dict:
    '''
    获取并返回包含tag的热门作品id(包括6条历史热门permanent和7条近一周热门recent)\n
    ----------
    返回示例(各字段可能为空)：\n
    {'permanent': ['89516463',..., '81064128'],\n
     'recent': ['104222730',..., '104174977']}
    '''
    tag_top_list = {'permanent':[],'recent':[]}

    url_artwork = "https://www.pixiv.net/ajax/search/artworks/" + quote(tag)
    headers = {
        "accept":"application/json",
        "Accept-Encoding":"gzip, deflate, br",
        "Accept_Language":"zh-CN,zh;q=0.9",
        "Connection":"keep-alive",
        "Host":"www.pixiv.net",
        "Referer":"https://www.pixiv.net/tags/"+quote(tag),
        "Cookie":"first_visit_datetime_pc=2022-12-16+22:10:32; p_ab_id=7; p_ab_id_2=5; p_ab_d_id=756704511; yuid_b=IpaUJhA; _gcl_au=1.1.1482174104.1671196256; device_token=ef9d2812486e5adb9031af3a18538145; c_type=23; privacy_policy_notification=0; b_type=1; privacy_policy_agreement=5; __utmv=235335808.|2=login ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=16674673=1^9=p_ab_id=7=1^10=p_ab_id_2=5=1^11=lang=zh=1; login_ever=yes; __utmz=235335808.1672322617.12.2.utmcsr=accounts.pixiv.net|utmccn=(referral)|utmcmd=referral|utmcct=/; _fbp=fb.1.1672495113421.430903723; a_type=1; _gid=GA1.2.1331476772.1673511569; QSI_S_ZN_5hF4My7Ad6VNNAi=v:0:0; __utmc=235335808; tag_view_ranking=Lt-oEicbBr~RTJMXD26Ak~_EOd7bsGyl~7dpqkQl8TH~4QveACRzn3~0xsDLqCEW6~oDcj90OVdf~xk-ZKrS2fa~qkC-JF_MXY~-98s6o2-Rp~7YNsdVv1xN~ziiAzr_h04~tgP8r-gOe_~azESOjmQSV~Yw6zHqltKg~EZQqoW9r8g~Ie2c51_4Sp~HY55MqmzzQ~0ArgFc_Uqc~K8esoIs2eW~KN7uxuR89w~-LBOt020Wk~RcahSSzeRf~P-laY91iQ1~2RR-Wztsl7~MwT2M45J6E~KOnmT1ndWG~Y9WAU0P3Ii~JrZT530U46~faHcYIP1U0~CrFcrMFJzz~QaiOjmwQnI~jH0uD88V6F~y3NlVImyly~ti_E1boC1J~MSNRmMUDgC~1Cu1TkXAKa~IJi4h9ABZq~nQRrj5c6w_~sFPxX8lk4q~99-dVV-h9A~Ltq1hgLZe3~_pwIgrV8TB~5oPIfUbtd6~zyKU3Q5L4C~uW5495Nhg-~eVxus64GZU~aKhT3n4RHZ~OUF2gvwPef~MnGbHeuS94~-7RnTas_L3~k_6Tbz5i0P~GNcgbuT3T-~-sp-9oh8uv~U-RInt8VSZ~rsb55I7upx~65aiw_5Y72~BSlt10mdnm~9ODMAZ0ebV~nIjJS15KLN~lxKly3SVNW~_bee-JX46i~txZ9z5ByU7~b_rY80S-DW~HffPWSkEm-~kdkWnz2DyL~qIDsnltE2o~DAWvkZA06J~0Sds1vVNKR~VeANpZNF_V~Ewxa3CZumI~QwUeUr8yRJ~jk9IzfjZ6n~GT9SxC6pVi~v3nOtgG77A~2R7RYffVfj~kj6L5xhc-l~E99HasFxYj~ZldurqefWy~VN4hvfPTzG~q303ip6Ui5~6rYZ-6JKHq~Itu6dbmwxu~Cr3jSW1VoH~RolC8IrBVO~nRp2ZLPLbj~BtXd1-LPRH~RZFNHsnAvv~YRDwjaiLZn~dg_40nEhSE~rOnsP2Q5UN~NGpDowiVmM~fIMPtFR8GH~I5npEODuUW~Ed_W9RQRe_~_Jc3XITZqL~1yIPTg75Rl~m3EJRa33xU~qAXue2fzEZ~Hvc3ekMyyh; __utma=235335808.816433562.1671196257.1673961160.1673964769.69; __utmt=1; _gat_UA-1830249-3=1; _gat_gtag_UA_76252338_1=1; PHPSESSID=16674673_iS5aA9lyOUB8bX27yI61dwbGRe8fkGiP; _ga_MZ1NL4PHH0=GS1.1.1673965315.4.0.1673965324.0.0.0; _ga_75BBYNYN9J=GS1.1.1673964768.82.1.1673965325.0.0.0; _ga=GA1.1.816433562.1671196257; __utmb=235335808.3.10.1673964769",
        "sec-ch-ua":'"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        "sec-ch-ua-mobile":"?0",
        "sec-ch-ua-platform":"Windows",
        "Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors",
        "Sec-Fetch-Site":"same-origin",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    page = 1
    paras = {"word":tag,"order":"date_d","mode":"all","p":page,"s_mode":"s_tag_full","type":"all","lang":"zh"}
    top_list_get = False
    __print_info__('INFO',f'正在获取标签 {tag} 热门作品列表...')
    while top_list_get == False:
        try:
            resp = requests.get(url=url_artwork,headers=headers,params=paras,verify=False)
        except:
            __print_info__('WARNING',f"请求 {tag} 热门作品列表失败！")
            __sleep_interval__()
        else:
            result_top_list = resp.json()
            resp.close()
            recent_list = result_top_list['body']['popular']['recent']
            permanent_list = result_top_list['body']['popular']['permanent']
            if not recent_list:
                __print_info__('WARNING',f"标签 {tag} 不存在热门作品列表！")
            else:
                # 获取近期热门作品id
                recent = []
                for seg in recent_list:
                    recent.append(seg['id'])
                # 获取历史热门作品id
                permanent = []
                for seg in permanent_list:
                    permanent.append(seg['id'])
                tag_top_list = {'permanent':permanent,'recent':recent}
                __print_info__('SUCCESS',f"标签 {tag} 热门作品列表获取成功！")
            top_list_get = True

    return tag_top_list

def __search_tag_artwork_list__(tag:str,page:int = 1) -> dict:
    '''
    获取并返回tag的作品总数和第page页的作品id(每页60条)\n
    ----------
    返回示例(各字段可能为None)：\n
    {'count': 10886,\n
     'artwork_list': ['104320764', '104317948',...,'104215074']}
    '''
    tag_artwork_list = {"count":None,"artwork_list":None}

    url_artwork = "https://www.pixiv.net/ajax/search/artworks/" + quote(tag)
    headers = {
        "accept":"application/json",
        "Accept-Encoding":"gzip, deflate, br",
        "Accept_Language":"zh-CN,zh;q=0.9",
        "Connection":"keep-alive",
        "Host":"www.pixiv.net",
        "Referer":"https://www.pixiv.net/tags/"+quote(tag),
        "Cookie":"first_visit_datetime_pc=2022-12-16+22:10:32; p_ab_id=7; p_ab_id_2=5; p_ab_d_id=756704511; yuid_b=IpaUJhA; _gcl_au=1.1.1482174104.1671196256; device_token=ef9d2812486e5adb9031af3a18538145; c_type=23; privacy_policy_notification=0; b_type=1; privacy_policy_agreement=5; __utmv=235335808.|2=login ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=16674673=1^9=p_ab_id=7=1^10=p_ab_id_2=5=1^11=lang=zh=1; login_ever=yes; __utmz=235335808.1672322617.12.2.utmcsr=accounts.pixiv.net|utmccn=(referral)|utmcmd=referral|utmcct=/; _fbp=fb.1.1672495113421.430903723; a_type=1; _gid=GA1.2.1331476772.1673511569; QSI_S_ZN_5hF4My7Ad6VNNAi=v:0:0; __utmc=235335808; tag_view_ranking=Lt-oEicbBr~RTJMXD26Ak~_EOd7bsGyl~7dpqkQl8TH~4QveACRzn3~0xsDLqCEW6~oDcj90OVdf~xk-ZKrS2fa~qkC-JF_MXY~-98s6o2-Rp~7YNsdVv1xN~ziiAzr_h04~tgP8r-gOe_~azESOjmQSV~Yw6zHqltKg~EZQqoW9r8g~Ie2c51_4Sp~HY55MqmzzQ~0ArgFc_Uqc~K8esoIs2eW~KN7uxuR89w~-LBOt020Wk~RcahSSzeRf~P-laY91iQ1~2RR-Wztsl7~MwT2M45J6E~KOnmT1ndWG~Y9WAU0P3Ii~JrZT530U46~faHcYIP1U0~CrFcrMFJzz~QaiOjmwQnI~jH0uD88V6F~y3NlVImyly~ti_E1boC1J~MSNRmMUDgC~1Cu1TkXAKa~IJi4h9ABZq~nQRrj5c6w_~sFPxX8lk4q~99-dVV-h9A~Ltq1hgLZe3~_pwIgrV8TB~5oPIfUbtd6~zyKU3Q5L4C~uW5495Nhg-~eVxus64GZU~aKhT3n4RHZ~OUF2gvwPef~MnGbHeuS94~-7RnTas_L3~k_6Tbz5i0P~GNcgbuT3T-~-sp-9oh8uv~U-RInt8VSZ~rsb55I7upx~65aiw_5Y72~BSlt10mdnm~9ODMAZ0ebV~nIjJS15KLN~lxKly3SVNW~_bee-JX46i~txZ9z5ByU7~b_rY80S-DW~HffPWSkEm-~kdkWnz2DyL~qIDsnltE2o~DAWvkZA06J~0Sds1vVNKR~VeANpZNF_V~Ewxa3CZumI~QwUeUr8yRJ~jk9IzfjZ6n~GT9SxC6pVi~v3nOtgG77A~2R7RYffVfj~kj6L5xhc-l~E99HasFxYj~ZldurqefWy~VN4hvfPTzG~q303ip6Ui5~6rYZ-6JKHq~Itu6dbmwxu~Cr3jSW1VoH~RolC8IrBVO~nRp2ZLPLbj~BtXd1-LPRH~RZFNHsnAvv~YRDwjaiLZn~dg_40nEhSE~rOnsP2Q5UN~NGpDowiVmM~fIMPtFR8GH~I5npEODuUW~Ed_W9RQRe_~_Jc3XITZqL~1yIPTg75Rl~m3EJRa33xU~qAXue2fzEZ~Hvc3ekMyyh; __utma=235335808.816433562.1671196257.1673961160.1673964769.69; __utmt=1; _gat_UA-1830249-3=1; _gat_gtag_UA_76252338_1=1; PHPSESSID=16674673_iS5aA9lyOUB8bX27yI61dwbGRe8fkGiP; _ga_MZ1NL4PHH0=GS1.1.1673965315.4.0.1673965324.0.0.0; _ga_75BBYNYN9J=GS1.1.1673964768.82.1.1673965325.0.0.0; _ga=GA1.1.816433562.1671196257; __utmb=235335808.3.10.1673964769",
        "sec-ch-ua":'"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        "sec-ch-ua-mobile":"?0",
        "sec-ch-ua-platform":"Windows",
        "Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors",
        "Sec-Fetch-Site":"same-origin",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    paras = {"word":tag,"order":"date_d","mode":"all","p":page,"s_mode":"s_tag","type":"all","lang":"zh"}
    artwork_list_get = False
    __print_info__('INFO',f'正在获取标签 {tag} 作品列表(第{page}页)...')
    while artwork_list_get == False:
        try:
            resp = requests.get(url=url_artwork,headers=headers,params=paras,verify=False)
        except:
            __print_info__('WARNING',f"请求 {tag} 作品列表(第{page}页)失败！")
            __sleep_interval__()
        else:
            result_artwork_list = resp.json()
            resp.close()
            # 获取作品总数
            tag_artwork_list["count"] = int(result_artwork_list['body']['illustManga']['total'])
            # 获取作品id
            if not tag_artwork_list["count"]:
                __print_info__('ERROR',f"标签 {tag} 作品列表为空！")
            else:
                artwork_raw_list = result_artwork_list['body']['illustManga']['data']
                artwork_list = []
                for artwork in artwork_raw_list:
                    artwork_list.append(artwork['id'])
                tag_artwork_list["artwork_list"] = artwork_list
            artwork_list_get = True

    return tag_artwork_list

def __gather_meta_artwork__(artwork_id:str,popularity_filter:bool = True):
    '''
    功能: 根据artwork_id, 向服务器请求作品元数据并写入数据库, 返回collect(作品是否入库)和artwork_meta\n
    参数: popularity_filter: 是否开启热度过滤模式(默认为True), 如不开启, 则数据不会入库
    '''
    artwork_meta = {}
    text_artwork = __get_text_artwork__(artwork_id)
    # 如能获取到源代码
    collect = False
    if text_artwork:
        title,description = __get_title__(artwork_id,text_artwork)
        if title:   # 内容存在
            page_count,like_count,bookmark_count,comment_count,view_count,is_original = __get_popularity__(text_artwork)
            user_id,user_name,upload_date,is_ai = __get_upload__(artwork_id,text_artwork)
            tag_list_raw = __get_tags__(artwork_id,text_artwork)
            url_p0 = __get_url_p0__(text_artwork)
            is_blocked = None
            is_delete = False
            # 检查是否含有R-18标签
            is_r18 = False
            for tag,trans in tag_list_raw:
                if tag == "R-18":
                    is_r18 = True
                    break
            # 整理update_from_upload字段
            upload_date = datetime.date(datetime.strptime(upload_date,'%Y-%m-%d'))
            update_from_upload = date.today()-upload_date
            update_from_upload = update_from_upload.days
            # 组合tag及其译名
            tag_list = []
            for tag,trans in tag_list_raw:
                if trans:
                    tag = tag + "(" + trans + ")"
                tag_list.append(tag)
            # 热度过滤
            if popularity_filter:   
                threshold_augment = 0.9993**int(view_count)+1       # 浏览量越低，阈值越高(1000浏览时阈值约为1.5倍，3000浏览时约为1.125倍)
                if is_r18:          # 入库阈值：R-18内容——收藏/浏览>0.14，AI作画——点赞/浏览>0.11，普通内容——点赞/浏览>0.09
                    if int(bookmark_count)/int(view_count) > 0.14*threshold_augment:
                        collect = True
                elif is_ai:
                    if int(like_count)/int(view_count) > 0.11*threshold_augment:
                        collect = True                
                else:
                    if int(like_count)/int(view_count) > 0.09*threshold_augment:
                        collect = True
                if collect:
                    # 向数据库中写入信息
                    proc = execute_procedure("ero_meta_insert",args_in=[artwork_id,title,description,user_id,user_name,upload_date,update_from_upload,url_p0,page_count,like_count,bookmark_count,comment_count,view_count,is_original,is_ai,is_r18],args_out=None)
                    proc_result = proc.proc()
                    if proc_result:
                        __print_info__('ERROR',f"作品 {artwork_id} 写入数据库失败！错误代码 {proc_result['Code']}")
                    else:
                        __print_info__('SUCCESS',f'作品 {artwork_id} 数据已写入数据库')
                    # tag_list_raw解包后写入数据库
                    for tag,trans in tag_list_raw:
                        proc = execute_procedure("ero_tag_insert_from_meta",args_in=[artwork_id,tag,trans],args_out=None)
                        proc_result = proc.proc()
                        if proc_result:
                            __print_info__('ERROR',f"作品 {artwork_id} 的标签写入数据库失败！错误代码 {proc_result['Code']}")
            # 以下内容为作品元数据标准格式
            artwork_meta = {
                'artwork_id':artwork_id,
                'title':title,
                'description':description,
                'tag_list':tag_list,
                'user_id':user_id,
                'user_name':user_name,
                'upload_date':upload_date,
                'update_from_upload':update_from_upload,
                'page_count':page_count,
                'like_count':like_count,
                'bookmark_count':bookmark_count,
                'comment_count':comment_count,
                'view_count':view_count,
                'is_original':is_original,
                'is_ai':is_ai,
                'is_r18':is_r18,
                'is_blocked':is_blocked,
                'url_p0':url_p0,
                'is_delete':is_delete
                }
        else:   # 内容不存在
            artwork_meta = {}
    else:   # 无法获取源代码
        artwork_meta = {}
    
    return collect,artwork_meta

def __update_meta_artwork__(artwork_id):
    '''
    根据artwork_id(必须为meta库中已有的id), 更新user_name, 标题描述以及热度信息(并且当该内容被删除时更新 is_delete 字段)
    '''
    text_artwork = __get_text_artwork__(artwork_id)
    # 如能获取到源代码
    if text_artwork:
        is_delete = False
        title,description = __get_title__(artwork_id,text_artwork)
        foo,like_count,bookmark_count,comment_count,view_count,foo = __get_popularity__(text_artwork)
        foo,user_name,upload_date,foo = __get_upload__(artwork_id,text_artwork)
        # 处理发布日期至今天数
        upload_date = datetime.date(datetime.strptime(upload_date,'%Y-%m-%d'))
        update_from_upload = date.today()-upload_date
        update_from_upload = update_from_upload.days
        proc = execute_procedure("ero_meta_update",args_in=[artwork_id,title,description,user_name,like_count,bookmark_count,comment_count,view_count,update_from_upload,is_delete],args_out=None)
        proc_result = proc.proc()
        if proc_result:
            __print_info__("ERROR",f"更新作品 {artwork_id} 时出错，错误代码：{proc_result['Code']}")
        else:
            __print_info__("SUCCESS",f"作品 {artwork_id} 的信息已更新")
    # 如内容已删除
    else:
        is_delete = True
        query = f"UPDATE ero_meta e SET e.is_delete = {is_delete} WHERE e.artwork_id = {artwork_id}"
        mysql = execute_sql_query(query)
        error_code = mysql.query()
        if error_code:
            __print_info__("ERROR",f"更新作品 {artwork_id} 时出错，错误代码：{error_code['Code']}")
        else:
            __print_info__("SUCCESS",f"已更新作品 {artwork_id} 的删除信息")
    
    return None

def artwork_query(artwork_id:str,if_log:bool = False) -> dict:
    '''    
    根据artwork_id, 通过寻找数据库和爬取源代码获取元数据\n
    '''
    global logging
    logging = if_log
    
    artwork_meta = {}
    # 首先查询数据库中是否有相应信息，如有，则直接返回元数据
    proc = execute_procedure("ero_meta_fetch",args_in=[f'{artwork_id}'],args_out=['title','description','user_id','user_name','upload_date','update_from_upload','url_p0','page_count','like_count','bookmark_count','comment_count','view_count','is_original','is_ai','is_r18','is_blocked','is_delete'])
    result = proc.proc(if_log)
    if result['Code'] == 200:
        if result['title']:
            title = result['title']
            description = result['description']
            user_id = result['user_id']
            user_name = result['user_name']
            upload_date = result['upload_date']
            upload_date = datetime.date(datetime.strptime(upload_date,'%Y-%m-%d'))
            update_from_upload = result['update_from_upload']
            url_p0 = result['url_p0']
            page_count = result['page_count']
            like_count = result['like_count']
            bookmark_count = result['bookmark_count']
            comment_count = result['comment_count']
            view_count = result['view_count']
            is_original = result['is_original']
            is_ai = result['is_ai']
            is_r18 = result['is_r18']
            is_blocked = result['is_blocked']
            is_delete = result['is_delete']
            # 通过sql语句获取tag
            query = f"select t.tag_name,t.tag_name_trans from ero_meta_tag e JOIN ero_tags t on e.tag_id = t.tag_id where e.artwork_id = {artwork_id}"
            mysql = execute_sql_query(query)
            tag_list_raw = mysql.query()
            # 组合tag及其译名
            tag_list = []
            for tag,trans in tag_list_raw:
                if trans:
                    tag = tag + "(" + trans + ")"
                tag_list.append(tag)
            # 写入数据
            artwork_meta = {
                'artwork_id':artwork_id,
                "title" : title,
                "description" : description,
                "tag_list" : tag_list,
                "user_id" : user_id,
                "user_name" : user_name,
                "upload_date" : upload_date,
                "update_from_upload" : update_from_upload,
                "page_count" : page_count,
                "like_count" : like_count,
                "bookmark_count" : bookmark_count,
                "comment_count" : comment_count,
                "view_count" : view_count,
                "is_original" : is_original,
                "is_ai" : is_ai,
                "is_r18" : is_r18,
                "is_blocked" : is_blocked,
                "url_p0" : url_p0,
                "is_delete" : is_delete
                }
        else:   # 如数据库中没有信息, 则向服务器请求数据
            foo,artwork_meta = __gather_meta_artwork__(artwork_id,popularity_filter=True)       

    return artwork_meta

def __pixiv_crawler_end__(t1,spot_num,insert_num,update_num,duplicate_num,error_artwork,error_user,error_tag,uncrawled_user:list = [],uncrawled_tag:list = [],interrupted:bool = False):
    '''
    (仅供爬虫程序使用)输出爬取信息统计和错误日志，并结束程序
    '''
    t2 = time.time()
    total = duplicate_num + spot_num + update_num
    print('<END>'.ljust(9," "),f'爬取完毕！本次爬取工程共查找作品 {total} 个, 其中:\n\t捕获新作品 {spot_num} 个 (捕获效率{(spot_num*100/total):.1f}%)\n\t录入新作品 {insert_num} 个 (入库比例{(insert_num*100/spot_num):.1f}%)\n\t更新旧作品 {update_num} 个 (更新比例{(update_num*100/total):.1f}%)\n\t总计用时: {(t2-t1)/60:.1f} 分钟 (爬取速度{total/((t2-t1)/3600):.1f}个/小时, 请求重试占比{(t_retry*100/(t2-t1)):.1f}%)')
    print('<END>'.ljust(9," "),f'以下是内容为空的爬取名单：\n\t作品：{error_artwork}\n\t用户：{error_user}\n\t标签：{error_tag}')
    if interrupted:
        print('<END>'.ljust(9," "),f'以下是因中断而尚未完成爬取的内容名单：\n\t用户：{uncrawled_user}\n\t标签：{uncrawled_tag}')
    if err:
        print('<END>'.ljust(9," "),f"本次爬取共发生错误 {len(err)} 个，错误信息如下：")
        i = 0
        for er in err:
            i += 1
            print(f"{i}. ",er)

    # 正常退出程序
    input("爬取完毕！按回车键退出")
    sys.exit()

def __pixiv_crawler_executor__(artwork_list:list = [],error_artwork:list = [],spot_num:int = 0,insert_num:int = 0,update_num:int = 0,duplicate_num:int = 0):
    '''
    (仅供爬虫程序使用)根据artwork_list，爬取内容、热度过滤，将作品数据和丢弃日志写入数据库\n
    返回此次爬取的无效artwork_id以及爬行统计数据
    '''
    # 根据artwork_list，不断爬取内容
    for artwork_id in artwork_list:
        # 手动修改配置文件暂停或结束程序
        with open("crawler_command.txt","r",encoding='utf-8') as f:
            command = f.readline()
            if command == "Pause\n":
                os.system("pause")
            if command == "End\n":
                return spot_num,insert_num,update_num,duplicate_num
        # 检查该artwork是否在丢弃日志中，若在则跳过，若不在则进入写入流程，并记录爬取信息
        query = f'select 1 from pixiv_crawler_discard d where d.artwork_id = {artwork_id} limit 1'
        mysql = execute_sql_query(query)
        result = mysql.query()
        if not result:  # 不在丢弃日志中
            # 检查meta表中是否存有该作品，如果有则更新，没有则热度过滤后写入meta
            query = f'select 1 from ero_meta e where e.artwork_id = {artwork_id} limit 1'
            mysql = execute_sql_query(query)
            result = mysql.query()
            if not result: # 如不在meta数据库中，则热度过滤后写入数据
                collect,artwork_meta = __gather_meta_artwork__(artwork_id,popularity_filter=True)
                if collect:
                    insert_num += 1   # 不在先前丢弃日志中且被写入meta：记录入库数据insert_num
                if not artwork_meta:
                    error_artwork.append(artwork_id)    # 记录不存在的artwork_id
                else:
                    spot_num += 1     # 不在先前丢弃日志中：记录捕获数据spot_num
                __sleep_interval__('C')
                # 发布超过14天且未达到热度指标的作品会被丢弃并不再被爬取
                update_from_upload = artwork_meta['update_from_upload']
                if not collect and int(update_from_upload) > 14:
                    query = f'insert into pixiv_crawler_discard() values({artwork_id},now());'
                    mysql = execute_sql_query(query)
                    result = mysql.query()
            else:           # 如已有信息，则更新数据
                __update_meta_artwork__(artwork_id)
                update_num += 1         # 已经在meta中的数据重复获取：记录更新数据update_num
                __sleep_interval__('C')
        else:   # 之前爬取过并被丢弃，则直接跳过该id
            duplicate_num += 1      # 在先前丢弃日志中：记录重复数据duplicate_num
            continue

    return error_artwork,spot_num,insert_num,update_num,duplicate_num

t1 = time.time()
def pixiv_crawler(artwork_id_list:list = [], user_id_list:list = [], tag_list:list = [], tag_page_start:int = 1, if_log:bool = True):
    '''
    给定artwork_id,user_id和tag名称，将对应的元数据爬取到数据库
    '''
    global err,t1,logging
    logging = if_log    # 决定是否要在控制台打印日志
    if not if_log:
        print(f"待获取列表: {*artwork_id_list,*user_id_list,*tag_list}")
        print("正在获取数据......")

    t1 = time.time()
    error_artwork = []
    error_user = []
    error_tag = []
    spot_num = 0
    insert_num = 0
    update_num = 0
    duplicate_num = 0

    # 1. 处理artwork_list
    result = __pixiv_crawler_executor__(artwork_id_list,error_artwork,spot_num,insert_num,update_num,duplicate_num)
    if len(result) == 5:
        error_artwork,spot_num,insert_num,update_num,duplicate_num = result
    elif len(result) == 4:  # 被中断
        spot_num,insert_num,update_num,duplicate_num = result
        uncrawled_user = user_id_list
        uncrawled_tag = tag_list
        __pixiv_crawler_end__(t1,spot_num,insert_num,update_num,duplicate_num,error_artwork,error_user,error_tag,uncrawled_user,uncrawled_tag,interrupted = True)
    artwork_id_list = []   # 清空artwork_id_list，为后续爬取腾出空间

    # 2. 处理user_id_list
    crawled_user_id_list = []
    for user_id in user_id_list:
        user_artwork_list, foo = search_user(user_id,if_log)
        if user_artwork_list:
            for artwork in user_artwork_list:
                artwork_id_list.append(artwork)    # 将作者作品id写入artwork_list，准备爬取
            
            result = __pixiv_crawler_executor__(artwork_id_list,error_artwork,spot_num,insert_num,update_num,duplicate_num)
            if len(result) == 5:
                error_artwork,spot_num,insert_num,update_num,duplicate_num = result
            elif len(result) == 4:  # 被中断
                spot_num,insert_num,update_num,duplicate_num = result
                uncrawled_user = set(user_id_list).difference(set(crawled_user_id_list))  # 输入与已爬取的差值
                uncrawled_tag = tag_list
                __pixiv_crawler_end__(t1,spot_num,insert_num,update_num,duplicate_num,error_artwork,error_user,error_tag,uncrawled_user,uncrawled_tag,interrupted = True)
            crawled_user_id_list.append(user_id)
            artwork_id_list = []   # 清空artwork_id_list
        else:   # user_id 作品为空
            error_user.append(user_id)
        __sleep_interval__('C')

    # 3. 处理tag
    crawled_tag_list = []
    for tag in tag_list:
        __search_tag_info__(tag)    # 将标签信息写入数据库（日后可拓展爬虫爬行策略）
        tag_artwork_count = __search_tag_artwork_list__(tag,1)['count']
        if tag_artwork_count:
            # 首先在数据库查找该tag的历史爬取记录
            proc = execute_procedure("pixiv_crawler_tag_query",args_in=[tag],args_out=['artwork_count'])
            in_database = proc.proc()
            if in_database['Code'] == 200:
                # 计算本次爬取需要获取的作品数量和对应页码数量
                task_count = tag_artwork_count - in_database["artwork_count"]  
                page_count = ceil(task_count / 60)
                __print_info__('SUCCESS',f'成功获取标签 {tag} 爬取日志，有 {task_count} 个作品待爬取')
            else:
                __print_info__('ERROR',f"获取标签 {tag} 爬取日志失败！错误代码 {in_database['Code']}")
            # 爬取每一页的作品id,结束后重置artwork_id_list
            for page in range(tag_page_start,page_count+1):            
                tag_artwork = __search_tag_artwork_list__(tag,page)
                artwork_id_list = tag_artwork['artwork_list']

                result = __pixiv_crawler_executor__(artwork_id_list,error_artwork,spot_num,insert_num,update_num,duplicate_num)
                if len(result) == 5:
                    error_artwork,spot_num,insert_num,update_num,duplicate_num = result
                elif len(result) == 4:  # 被中断
                    spot_num,insert_num,update_num,duplicate_num = result
                    uncrawled_user = [] 
                    uncrawled_tag = set(tag_list).difference(set(crawled_tag_list))  # 输入与已爬取的差值
                    __pixiv_crawler_end__(t1,spot_num,insert_num,update_num,duplicate_num,error_artwork,error_user,error_tag,uncrawled_user,uncrawled_tag,interrupted = True)
            crawled_tag_list.append(tag)
            artwork_id_list = []
            # 记录本次爬取的tag名称以及作品数量，避免再次爬取同一tag时消耗重复资源
            proc = execute_procedure("pixiv_crawler_tag_update",args_in=[tag,tag_artwork_count],args_out=None)
            proc_result = proc.proc()
            if proc_result:
                __print_info__("ERROR",f"写入标签 {tag} 爬取日志时出错，错误代码：{proc_result['Code']}")
            else:
                __print_info__('SUCCESS',f'成功记录标签 {tag} 爬取日志')
        else:   # tag 作品列表为空
            error_tag.append(tag)
        __sleep_interval__('C')

    # 处理完毕，结束程序
    __pixiv_crawler_end__(t1,spot_num,insert_num,update_num,duplicate_num,error_artwork,error_user,error_tag)




if __name__ == '__main__':
    # try:
    
    # except:
    #     traceback.print_exc()
    #     __pixiv_crawler_end__    

    # pixiv_crawler(user_id_list = ['57681088', '4364687', '3297691', '86845153', '13274275', '2811210', '2846708', '2642047', '13829843', '34054962', '333556', '24234', '14046928', '10852879', '465133', '22334948', '23291755', '51198160', '446171', '888151', '2156906', '19630602', '267137', '77465110', '8983922', '87710606', '27517', '2750098', '1960050', '8843541', '22298878', '926687', '2827964', '5128504', '70050825', '23338848', '24890072', '8349252', '18054080', '14538670', '67093476', '45249715', '4588267', '6049901', '3388329', '32955491', '15558289', '12227191', '6662895', '20728711', '23098486', '50843589', '12505972', '16985944', '24027989', '7618326', '21739409', '66371932', '212801', '1980643', '17178734', '4816744', '2993192', '346855', '12539859', '9205975', '25760573', '32221908', '28480895', '76749711'],if_log=True)
    pixiv_crawler(tag_list=['バーチャルYouTuber100users入り','バーチャルYouTuber300users入り','バーチャルYouTuber500users入り','バーチャルYouTuber1000users入り','バーチャルYouTuber3000users入り',
    'バーチャルYouTuber5000users入り','バーチャルYouTuber10000users入り','バーチャルYouTuber30000users入り','バーチャルYouTuber50000users入り','バーチャルYouTuber100000users入り','バーチャルYouTuber300000users入り'])
