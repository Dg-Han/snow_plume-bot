# 获取定时任务模块
from nonebot import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
# 定义事件响应器
from nonebot import on_message,on_command
# 添加处理依赖
from nonebot.params import EventMessage,CommandArg,ArgStr
from nonebot.adapters import Event,Bot,Message
from nonebot.matcher import Matcher
from nonebot import rule
# 添加功能所需模块
from nonebot.adapters.onebot.exception import ActionFailed
from nonebot import get_bot

import snow_plume.plugins.pixiv_crawler as pixiv_crawler
from configs.Config import Config
# import pixiv_crawler

import random
from datetime import datetime,time,timedelta
from time import sleep
import re

from snow_plume.plugins.built_in.mysql import execute_procedure,execute_sql_query
from snow_plume.plugins.built_in.handling_message import sending_message,send_forward_msg,recall_msg
import asyncio
import os
from pypinyin import pinyin
import json
from pathlib import Path

'''
插件功能：当用户在对话框输入想看涩图的信息后，轻雪酱会识别并返回一张涩图
'''
class SetuConfig:
    '''涩图配置'''
    configs = Config("setu")
    ai_allow:dict[str,bool] = configs['allowance']['ai']
    r18_allow = configs['allowance']['r18']
    cache_threshold = configs['cache_threshold']
    subscribe_puser_list:dict[dict] = configs['subscribe_puser_list']

    def __init__(self,group_id:str = 'default'):
        self.ai_allow:bool = self.configs['allowance']['ai'][group_id]
        self.r18_allow:bool = self.configs['allowance']['r18'][group_id]
        self.subscribe_puser_list:dict = self.configs['subscribe_puser_list'][group_id]

    @classmethod
    def puser_subscribe(cls,group_id:str,puser_id:str) -> tuple[int,str]:
        '''在配置中添加关注用户(返回值:(Code,puser_name)'''
        # 检查配置中是否已储存了相同的用户
        puser = ArtworkUser(puser_id)
        try:
            puser_list = cls.configs['subscribe_puser_list'][f'{group_id}']
        except KeyError:   # 没这个群
            # 在config中创建群
            cls.configs.add_config(['subscribe_puser_list',f'{group_id}'],{f'{puser_id}': puser.name})
            # 在json中创建群
            content = cls.read_json('subscribe_puser_list')
            content[f'{group_id}'] = {f'{puser_id}': puser.artwork_list[0]}
            cls.write_json('subscribe_puser_list',content)
            return 200,puser.name 
        except AttributeError:      # 群里没有关注画师
            cls.configs.add_config(['subscribe_puser_list',f'{group_id}',f'{puser_id}'],puser.name)
            content = cls.read_json('subscribe_puser_list')
            content[f'{group_id}'][f'{puser_id}'] = puser.artwork_list[0]
            cls.write_json('subscribe_puser_list',content)
            return 200,puser.name 
        else:
            if puser_id not in puser_list.keys():
                if puser.name:
                    cls.configs.add_config(['subscribe_puser_list',f'{group_id}',f'{puser_id}'],puser.name)
                    content = cls.read_json('subscribe_puser_list')
                    content[f'{group_id}'][f'{puser_id}'] = puser.artwork_list[0]
                    cls.write_json('subscribe_puser_list',content)
                    return 200,puser.name # 成功添加
                else:
                    return 404,None # 画师不存在
            else:
                cls.configs.set_config(['subscribe_puser_list',f'{group_id}',f'{puser_id}'],puser.name)
                return 403,puser.name # 重复添加用户
    
    @classmethod
    def puser_unsubscribe(cls,group_id:str|int,puser_id:str) -> tuple[int,str]:
        '''在配置中移除关注用户'''
        # 检查配置中是否已储存了相同的用户
        if puser_id not in cls.configs['subscribe_puser_list'][f'{group_id}'].keys():
            return 404,None  # 画师不存在
        else:
            user_name = cls.configs.remove_config(['subscribe_puser_list',f'{group_id}',f'{puser_id}'])
            content = cls.read_json('subscribe_puser_list')
            del content[f'{group_id}'][f'{puser_id}']
            cls.write_json('subscribe_puser_list',content)
            return 200,user_name  # 成功删除
    
    @classmethod
    def puser_check(cls,group_id:str|int) -> tuple[str,str]:
        '''查看已关注的用户(返回形式:[(id,name),(id,name),...])'''
        try:
            foo = [tup for tup in cls.subscribe_puser_list[f'{group_id}'].items()]
            result = cls.sort_en_zh_jp(foo) # 排序
        except:
            result = None
        return result

    @staticmethod
    def read_json(json_name:str = 'subscribe_puser_list') -> dict:
        with open(Path()/"data"/"setu"/f"{json_name}.json", "r", encoding="utf-8") as f:
            content = json.load(f)
        return content

    @staticmethod
    def write_json(json_name:str,content:dict) -> None:
        with open(Path()/"data"/"setu"/f"{json_name}.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(content,indent=2,sort_keys=True, ensure_ascii=False))

    @staticmethod
    def sort_en_zh_jp(msg_list:list[tuple[any,str]]):
        '''针对[(foo,msg),(),...]中的msg进行中日英语言的归类和排序'''
        en_list = []
        zh_list = []
        jp_list = []
        # 解包并按语言分类
        for tuple in msg_list:
            if re.findall('[a-zA-Z0-9.(),\']+', tuple[1][0]):   # 识别英文
                en_list.append(tuple)
            elif re.findall(u'[\u4e00-\u9fa5]+',tuple[1][0]):   # 识别中文
                zh_list.append(tuple)
            else:   # 剩余部分为日文
                jp_list.append(tuple)
        # 排序
        en_list.sort(key=lambda x:x[1].lower())
        zh_list.sort(key=lambda x:pinyin(x[1]))
        # 包装
        en_list.extend(zh_list)
        en_list.extend(jp_list)
        return en_list 

class ArtworkFolder:
    '''涩图存放路径的文件管理命令, 控制涩图的下载和删除
    @classmethod
        _replenishment_trigger()    # 监听路径下涩图数量, 触发补充涩图方法\n
        replenishment()             # 补充涩图
    @method
        delete(artwork_id)          # 删除指定id的涩图\n
        get_file_name(artwork_id)   # 获取指定涩图的文件名(发送图片用)
    '''
    path = 'data\\images\\setu\\'
    threshold = SetuConfig.cache_threshold

    def __init__(self):
        pass

    @classmethod
    def _replenishment_trigger(cls) -> dict|int:
        '''当路径下涩图数量小于阈限时, 传递填充需求'''
        # 更新路径下现有文件列表
        file_name_list = os.listdir(cls.path)
        # 统计作品数量
        ai = 0
        r18 = 0
        artwork_id_list = []
        for file_name in file_name_list:
            artwork_id = file_name.split("_")[1]
            if artwork_id not in artwork_id_list:
                special_tag = file_name.split("_")[0]
                if 'ai' in special_tag:
                    ai += 1
                if 'r18' in special_tag:
                    r18 += 1
                artwork_id_list.append(artwork_id)          
        # 若作品数量低于最低限制, 则传递填充需求
        normal = len(artwork_id_list) - ai - r18
        ai_threshold = int(round(cls.threshold * 0.15,0))
        r18_threshold = int(round(cls.threshold * 0.15,0))
        normal_threshold = cls.threshold - ai_threshold - r18_threshold
        if ai < ai_threshold or r18 < r18_threshold or normal < normal_threshold:
            request_dict = {'ai':ai_threshold - ai,'r18':r18_threshold - r18,'normal':normal_threshold - normal}
            return request_dict
        else:
            return 0

    @classmethod
    async def replenishment(cls) -> None:
        '''接收填充需求, 并填充随机涩图至足够数量'''
        request_dict = cls._replenishment_trigger()
        while request_dict:
            for ai in range(request_dict['ai']):
                artwork = Artwork(special_tag_request = 'ai')
                await artwork.download(cls.path)
            for r18 in range(request_dict['r18']):
                artwork = Artwork(special_tag_request = 'r18')
                await artwork.download(cls.path)
            for normal in range(request_dict['normal']):
                artwork = Artwork(special_tag_request = 'normal')
                print(artwork.id)
                await artwork.download(cls.path)
            request_dict = cls._replenishment_trigger()

    async def delete(self,artwork_id:str) -> None:
        file_name_list = os.listdir(self.path)
        for file_name in file_name_list:
            if artwork_id in file_name:
                os.remove(f'{self.path}{file_name}')
        await self.replenishment()    # 及时补充内容

    def get_file_name(self,artwork_id:str = '',restriction:list[str] = []) -> str:
        '''获取已下载作品首张图片的文件名'''
        file_name_list = os.listdir(self.path)
        if artwork_id:
            for file_name in file_name_list:
                if f'{artwork_id}_p0' in file_name.split(".")[0]:
                    name = f'\\setu\\{file_name}'
                    return name
        else:   # 若无目标作品, 则随机返回一个已下载作品的id及其名称
            target_files = [file for file in file_name_list if ('_p0' in file)]
            for restriction_tag in restriction:
                for files in target_files:
                    if restriction_tag in files:
                        target_files.remove(files)
            file_name = target_files[random.randint(0,len(target_files)-1)]
            artwork_id = file_name.split("_")[1]
            name = f'\\setu\\{file_name}'
            return artwork_id,name

class ArtworkMeta:
    '''管理和编辑涩图的元数据
    @staticmethod
        _tag_preprocessing(tag_list)    # 将标签格式化(中文括号转英文,按字符长度正序排列)
    @method
        _popularity_algorithm() # 生成图片的热度信息
        package_intro()         # 生成作品摘要\n
        package_detail()        # 生成作品详情
    '''
    id = None
    title = None
    description = None
    tag_list = None
    user_id = None
    user_name = None
    upload_date = None
    update_from_upload = None
    page_count = None
    like_count = None
    bookmark_count = None
    comment_count = None
    view_count = None
    is_original = None
    is_ai = None
    is_r18 = None
    is_blocked = None
    url_p0 = None
    is_delete = None

    def __init__(self,artwork_id):
        self.id = artwork_id
        # 获取元数据
        if self.id:
            meta = pixiv_crawler.artwork_query(self.id)
            if meta:
                foo,self.title,self.description,self.tag_list,self.user_id,self.user_name,self.upload_date,self.update_from_upload,self.page_count,self.like_count,self.bookmark_count,self.comment_count,self.view_count,self.is_original,self.is_ai,self.is_r18,self.is_blocked,self.url_p0,self.is_delete = tuple(meta.values())
                self.tag_list = self._tag_preprocessing(self.tag_list)
                self.popularity = self._popularity_algorithm()

    @staticmethod
    def _tag_preprocessing(tag_list) -> list:
        '''将标签的中文括号转为英文括号, 并按字符长度正序排列'''
        tag_dict = {}
        for i in range(len(tag_list)):
            tag = tag_list[i]
            tag = tag.replace("（","(")     # 将中文括号转为英文括号
            tag = tag.replace("）",")")
            tag_list[i] = tag               # 替换原有tag
            zh_count = 0                    # 统计中文字符数
            zh = re.findall('[^a-zA-Z0-9.(),\']+', tag)
            for i in zh:
                zh_count += len(i)
            tag_dict[tag]=(len(tag)+zh_count,zh_count)
        tag_temp = sorted(tag_dict.items(),key = lambda x:x[1][1],reverse = True)   # 字符数量相同, 中文字多的排前面(显示长度较短)
        tag_sort = sorted(tag_temp,key = lambda x:x[1][0])
        tag_list = []
        for tag in tag_sort:
            tag_list.append(tag[0])

        return tag_list

    def _popularity_algorithm(self) -> float:
        '''热度算法'''
        if self.is_r18:
            popularity = int(self.bookmark_count) / int(self.view_count) * 1000 * 0.9 / 1.4
        else:
            popularity = int(self.like_count) / int(self.view_count) * 1000

        return popularity

    def package_intro(self) -> str:
        '''整理作品摘要'''
        # 格式化简介
        if self.description:
            description = self.description.replace("\n","\n     ")
        else:
            description = "该作品没有简介            "
        # 生成作品摘要
        intro = f'标题 |   {self.title}\n作者 |   {self.user_name} ({self.user_id})\n\n------------\n{description}\n'
        return intro

    def package_detail(self) -> str:
        '''整理作品详情'''
        # 格式化上传日期
        upload_date = str(self.upload_date).replace("-",".")
        # 格式化特殊标签
        special_tags = ''
        is_ai = "AI作画" if self.is_ai == 1 else ""
        is_r18 = "R18" if self.is_r18 == 1 else ""
        is_original = "原创" if self.is_original == 1 else ""
        special_tuple = (is_ai,is_r18,is_original)
        exists = False
        for special_tag in special_tuple:
            if special_tag:
                if exists:
                    special_tags = ", ".join((special_tags,special_tag))
                else:
                    special_tags = "".join((special_tags,special_tag))
                    exists = True
        # 生成tags字段
        tags = ""
        for tag in self.tag_list:
            tags = "\n     - ".join((tags,tag))
        if special_tags:
            detail = "\n".join((f'• 作品ID       {self.id}',f'• 特殊tag     {special_tags}',f'• 发布时间   {upload_date}',f'• 人气指数   {self.popularity:.2f}',f'• 标签{tags}'))
        else:
            detail = "\n".join((f'• 作品ID       {self.id}',f'• 发布时间   {upload_date}',f'• 人气指数   {self.popularity:.2f}',f'• 标签{tags}'))
        return detail

class Artwork(ArtworkMeta):
    '''储存一张涩图的基本信息
    @classmethod
        _get_random_id()    # 如实例化时未指定涩图id, 则随机创建一张涩图
    @staticmethod
        check_send_log(artwork_id,group_id) # 检查指定作品id在指定群中是否发送过(范围为30天)
    @method
        download(path)      # 将作品下载到指定路径
    '''
    def __init__(self,id:str = '',special_tag_request:str = ''):
        # 若不给定id和特殊tag要求, 则从数据库中随机抽取一个id
        if id:
            self.id = id
        else:
            self.id = self._get_random_id(special_tag_request)
        super(Artwork,self).__init__(self.id)   # 调用父类(ArtworkMeta)的初始化方法获取作品元数据

    @classmethod
    def _get_random_id(cls,special_tag_request:str = '') -> str:
        '''随机获取一张满足special_tag_request条件的涩图'''
        # 获取符合条件的图片总数
        restriction_r18 = 'is_r18 = 1 AND' if special_tag_request == 'r18' else ''
        restriction_ai = 'is_ai = 1 AND' if special_tag_request == 'ai' else ''
        restriction_normal = 'is_r18 = 0 AND is_ai = 0 AND' if special_tag_request == 'normal' else ''
        restriction = restriction_r18 + restriction_ai + restriction_normal + '''
                    (is_blocked = 0 or is_blocked IS NULL)
                    AND
                    (artwork_id NOT IN 
                        (SELECT artwork_id FROM ero_meta em JOIN ero_log el USING (artwork_id) 
                        WHERE
                        ((UNIX_TIMESTAMP(NOW())-UNIX_TIMESTAMP(el.datetime)) / 86400) < 30))
                    '''     # 之前被屏蔽过或30天内发送过的涩图也不再发送
        query_num = f'''
                SELECT count(*) FROM ero_meta 
                WHERE 
                {restriction}
                '''
        mysql = execute_sql_query(query_num)    # 之前被屏蔽或30天内发送过的涩图不再发送
        count = mysql.query()[0][0]             # 返回图库总数
        # 获取作品id
        rand = random.randint(1,count)      # 随机数用于选择图片id
        query_pic = f'''
            SELECT artwork_id FROM ero_meta em 
            WHERE 
            {restriction}
            LIMIT 
            {rand},1
            '''
        mysql = execute_sql_query(query_pic)
        id = mysql.query()[0][0]      
        return id

    @staticmethod
    def check_send_log(artwork_id:str,group_id:str) -> bool:
        '''检查某张作品在近30天内是否发送过(发过为False)'''
        query = f'''
            SELECT 1 FROM ero_log 
            WHERE
            (((UNIX_TIMESTAMP(NOW())-UNIX_TIMESTAMP(datetime)) / 86400) < 30)
            AND
            artwork_id = {artwork_id}
            AND
            group_id = {group_id}
            LIMIT 1
        '''
        sql = execute_sql_query(query)
        result = sql.query()
        try:
            print(f"查找ero_log时报错, 错误代码 {result['Code']}")
        except:
            if result:
                return False     # 查找到内容, 说明30天内发过, 不可放行
            else:
                return True    # 未查找到内容, 说明30天内没发过, 可放行

    async def download(self, path = ArtworkFolder.path) -> None:
        '''将图片下载到本地'''
        if self.title:
            await pixiv_crawler.download_pic(artwork_id=self.id, path=path, url_p0=self.url_p0, is_ai=self.is_ai, is_r18=self.is_r18, page_count=self.page_count)

class ArtworkUser:
    '''储存一个画师的基本信息
    @staticmethod
        _get_first_upload_time(artwork_list)    # 获取作品列表中最初上传作品的上传时间
    @method
        package_intro()     # 生成画师简介
    
    '''
    id = None
    name = None
    description = None
    image:str = None
    artwork_list = None
    pickup_list = None
    first_upload_time:str = None
    focus_tag:list[str] = None

    def __init__(self,id:str):
        self.id = id
        meta = pixiv_crawler.search_user_info(self.id)
        if meta:
            self.name,self.description,self.image = tuple(meta.values())
        artworks = pixiv_crawler.search_user(self.id)
        if Artwork(artworks[0][0]).title:   # 能获取到作品信息, 说明该用户未屏蔽他人
            self.artwork_list,self.pickup_list = artworks
            self.first_upload_time = self._get_first_upload_time(self.artwork_list)
            self.focus_tag = pixiv_crawler.get_focus_tags(self.artwork_list[:50])

    @staticmethod
    def _get_first_upload_time(artwork_list:list) -> str:
        '''根据第一张作品获取首次上传时间(年-月,类中用于获取入站时间)'''
        return (datetime.strftime(Artwork(artwork_list[-1]).upload_date,'%Y-%m'))
        
    def package_intro(self) -> str:
        '''整理画师简介'''
        if 'i.pximg.net' in self.image: # 无头图
            image_CQ = ''
        else:
            image_CQ = f'[CQ:image,file={self.image}]\n'
        focus_tag_list = self.focus_tag[:5]
        focus_msg = ''
        for focus_tag in focus_tag_list:
            focus_msg = '\n    - '.join((focus_msg,focus_tag))
        if self.description:
            description = self.description
        else:
            description = '该画师没有简介'
        msg = f'{image_CQ}画师 |   {self.name} ({self.id})\n入站 |   {self.first_upload_time}\n发布 |   {len(self.artwork_list)} 个作品\n标签 |{focus_msg}\n\n------------------\n{description}'
        return msg

class SendArtwork:
    '''管理涩图发送的相关命令
    @classmethod
        random(bot,group_id,group_user_id)  # 从缓存中随机发送一张涩图, 如人为调用, 则记录调用者日志\n
        paid(artwork_id,bot,group_id)   # 指定作品id, 获取作品图片和详情\n
        puid(user_id,bot,group_id)  # 指定画师id, 获取画师信息及最多3张作品
    @staticmethod
        _packaging_forward(folder,*artworks)    # 将多张作品的图片, 简介和详情包装进合并转发消息中\n
        _sending_forward(bot,msg_list,group_id,*artworks,leading_msg)    # 发送合并转发消息\n
        _log_record(artwork_id,group_user_id,group_id)     # 向数据库写入涩图获取日志\n
        block_record(artwork_id,is_blocked)     # 向数据库写入作品是否被屏蔽 
    '''
    @classmethod
    async def random(cls,bot:Bot,group_id:str,group_user_id:str = '0') -> None:
        '''从数据库中随机选择一张涩图发送至指定群'''
        allowance_ai = SetuConfig(group_id).ai_allow
        allowance_r18 = SetuConfig(group_id).r18_allow
        restriction = ['ai' if allowance_ai == False else '']
        if not allowance_r18:
            restriction.append('r18')
        folder = ArtworkFolder()
        is_send = False
        retry_count = 0
        # 尽最大努力交付图片和图片详情
        while (is_send == False and retry_count < 3):
            artwork_id,file_name = folder.get_file_name(restriction=restriction)
            artwork = Artwork(artwork_id)
            retry_count += 1
            # 发送第一张图片+图片信息(合并转发形式)
            try:        # 发送第一张图片
                await sending_message((f"[CQ:image,file={file_name}]",),group_id)     # 发送本地图片：file_name = "\setu\101393174_p0.png"，存放在/data/images/setu目录下
            except ActionFailed:    # 图被屏蔽
                # 将被屏蔽的信息写入作品元数据, 之后不再发送
                cls.block_record(artwork.id,True)
                url_raw = artwork.url_p0.replace('i.pximg.net','i.pixiv.re')
                url = ''
                for j in range(int(artwork.page_count)):
                    url = url + f"\n{url_raw}"
                    url_raw = url_raw.replace(f"p{j}",f"p{j+1}")
                if retry_count == 1:
                    msg1 = f'呀！这张图发不出来呢...\n主人可以通过下面的链接访问图片喔!\n{url}'
                else:
                    msg1 = f'呀！这张图也发不出来呢...\n主人可以通过下面的链接访问图片喔!\n{url}'
                if retry_count != 3:
                    msg2 = "轻雪酱要再翻翻图库..."
                else:
                    msg2 = "呜呜...怎么全是发不出来的图...轻雪酱想休息一下..."
                await sending_message([msg1,msg2],group_id)
                await folder.delete(artwork.id)
            else:      # 能发出来之后，再以合并转发形式发送图片详情
                log_recorder = group_user_id
                await cls.sending_forward(bot,group_id,log_recorder,[artwork],need_download=False)
                is_send = True

    @classmethod
    async def paid(cls,artwork_id:str,bot:Bot,group_id:str) -> None:
        '''根据作品id查询作品详情'''
        artwork = Artwork(artwork_id)
        if artwork.title:
            message_id_list = await sending_message(('轻雪酱找到该图片啦, 下载可能需要一段时间, 请主人耐心等待吧!',),group_id)
            prompt_id = message_id_list[0]
            log_recorder = '0'
            await cls.sending_forward(bot,group_id,log_recorder,[artwork])
            await recall_msg(bot,prompt_id)
        else:
            await sending_message(('轻雪酱没有找到该作品id, 这幅作品可能已经被删除了',),group_id)
            return None

    @classmethod
    async def puid(cls,user_id:str,bot:Bot,group_id:str) -> None:
        '''根据user_id, 发送画师简介以及该画师的三张作品'''
        user = ArtworkUser(user_id)
        if not user.artwork_list:
            if not user.name:   # 画师不存在
                await sending_message(('轻雪酱没有找到该画师id...请主人确认这个id是否存在喔!',),group_id)
            else: # 没有作品或被屏蔽
                await sending_message(('这位用户没有上传作品呢...也可能是对外屏蔽了...',),group_id)
        else:
            # 发送画师简介
            upload_from_now = (datetime.now() - datetime.strptime(user.first_upload_time,'%Y-%m'))/timedelta(365)
            if upload_from_now < 2:
                comment = ', 是位非常年轻的画师呢!'
            elif upload_from_now > 6:
                comment = ', 是非常有经验的画师呢!'
            else:
                comment = ''
            message_id_list = await sending_message((f'找到啦, 这位画师最早从{user.first_upload_time[:4]}年开始活动, 发布了{len(user.artwork_list)}篇作品{comment}','下载图片可能需要一段时间, 请主人耐心等待吧!',),group_id)
            prompt_id = message_id_list[1]
            # 准备要上传的作品(最多3张,如有精选作品, 则优先选择精选作品)
            artworks:list[Artwork] = []
            for pickup_id in user.pickup_list:
                check = Artwork.check_send_log(pickup_id,group_id)   # 检查30天内是否发送过该作品
                if check:
                    artworks.append(Artwork(pickup_id))    
            discard_list = []
            for artwork_id in user.artwork_list:
                if len(artworks) >= 3:
                    break
                else:
                    check = Artwork.check_send_log(artwork_id,group_id)   # 检查30天内是否发送过该作品
                    if check:
                        artworks.append(Artwork(artwork_id))    
                    else:
                        discard_list.append(Artwork(artwork_id))
                # 若可用的作品数不足3个, 则从已发过的内容中补齐
            for i in range(3-len(artworks)):   
                try:
                    artworks.append(discard_list[i])    
                except:
                    pass
            # 发送合并转发消息
            log_recorder = '0'
            leading_msg = [user.package_intro()]
            await cls.sending_forward(bot,group_id,log_recorder,artworks,leading_msg=leading_msg)
            await recall_msg(bot,prompt_id)
        
    @classmethod
    async def sending_forward(cls,bot:Bot,group_id:str,log_recorder:str,artworks:list[Artwork],leading_msg:list[str] = [],need_download:bool = True) -> None:
        '''发送包含涩图及其详情的合并转发消息'''
        # 下载图片、包装消息
        folder = ArtworkFolder()
        if need_download:
            for artwork in artworks:
                await artwork.download()
        artwork_if_blocked:list[dict[Artwork,bool]] = [{artwork:False} for artwork in artworks]
        forward_msg_list = cls._packaging_forward(folder,artwork_if_blocked,leading_msg)
        # 发送合并转发消息
        try:
            await send_forward_msg(bot,group_id,forward_msg_list)
        # 如果合并转发消息被屏蔽
        except ActionFailed:     
            # 首先检查leading_msg中是否有图片, 如有则先去除图片重试一次
            leading_pic = False
            for msg in leading_msg:
                if '[CQ:image,' in msg:
                    leading_pic = True
                    break
            raw_leading_msg = []
            if leading_pic:
                raw_leading_msg = [re.sub(r'\[CQ:image,.*?\]','',msg) for msg in leading_msg]
                forward_msg_list = cls._packaging_forward(folder,artwork_if_blocked,raw_leading_msg)
                try:
                    await send_forward_msg(bot,group_id,forward_msg_list)
                except ActionFailed:    # 仍然被屏蔽, 说明图片内容一定有问题, 进入图片处理流程
                    pass
                else:   # 成功发送, 结束流程
                    for artwork in artworks:
                        cls.block_record(artwork.id,False)        
                        cls._log_record(artwork.id,log_recorder,group_id)
                        await folder.delete(artwork.id)
                    return None
            # 若不是leading_msg的问题, 则在发送的图片中进行判断
            if len(artworks) > 3:     # 顺序查找成本过高, 容易被风控, 当合并转发作品数 > 3时强制使用简版发送(不发送图片)
                raw_leading_msg = raw_leading_msg + ["呜呜...作品太多轻雪酱找不到哪个作品没过审了, 请主人尽可能把一次发送的作品数量控制在3个以内吧! "]
                artwork_if_blocked = [{artwork:True} for artwork in artworks]
                forward_msg_list = cls._packaging_forward(folder,artwork_if_blocked,raw_leading_msg)
                await send_forward_msg(bot,group_id,forward_msg_list)
            else:   # 使用顺序查找算法多次尝试发送消息, 发出消息并找到被屏蔽的作品
                for i in range(1,2**len(artwork_if_blocked)):
                    artwork_if_blocked = [{artwork:False} for artwork in artworks]
                    for j in range(0,len(artwork_if_blocked)):
                        if (i // 2**j) % 2 == 1:    # 转化为二进制
                            key:Artwork = [artwork for artwork in artwork_if_blocked[j].keys()][0]
                            artwork_if_blocked[j][key] = True
                    forward_msg_list = cls._packaging_forward(folder,artwork_if_blocked,raw_leading_msg)
                    try:
                        await send_forward_msg(bot,group_id,forward_msg_list)
                    except:
                        sleep(random.random())
                    else:
                        for j in range(0,len(artwork_if_blocked)):
                            artwork_id = [artwork for artwork in artwork_if_blocked[j].keys()][0].id
                            if (i // 2**j) % 2 == 1:    
                                cls.block_record(artwork_id,True)
                            else:
                                cls.block_record(artwork_id,False)
                        break
        else:   # 首次即成功发送合并转发消息
            for artwork in artworks:
                cls.block_record(artwork.id,False)
        finally:    # 记录涩图获取日志
            for artwork in artworks:
                cls._log_record(artwork.id,log_recorder,group_id)
                await folder.delete(artwork.id)

    @staticmethod
    def _packaging_forward(folder:ArtworkFolder,artwork_if_blocked:list[dict[Artwork,bool]],leading_msg:list[str] = []) -> list[str]:
        '''将多张图片的详细信息包装进合并转发消息中(需要先下载图片)'''
        forward_msg_list = []
        for msg in leading_msg:
            forward_msg_list.append(msg)
        i = 1
        for artwork_dict in artwork_if_blocked:
            if len(artwork_if_blocked) != 1:
                    forward_msg_list.append(f'=========== {i} ===========')
                    i += 1
            for artwork,is_blocked in artwork_dict.items():
                if is_blocked:      # 对于被屏蔽的作品, 只给出代理链接而不给出图片
                    url_raw = artwork.url_p0.replace('i.pximg.net','i.pixiv.re')
                    url = ''
                    for j in range(int(artwork.page_count)):
                        url = url + f"\n{url_raw}"
                        url_raw = url_raw.replace(f"p{j}",f"p{j+1}")
                    forward_msg_list.append(f'呀！这幅作品被审核吞掉惹...请主人通过下面的链接查看吧！\n{url}')
                else:
                    file_name = folder.get_file_name(artwork.id)
                    for k in range(int(artwork.page_count)):
                        forward_msg_list.append(f"[CQ:image,file={file_name}]")
                        file_name = file_name.replace(f"p{k}",f"p{k+1}")
                intro = artwork.package_intro()
                detail = artwork.package_detail()
                forward_msg_list.extend((intro,detail))

        return forward_msg_list

    @staticmethod
    def _log_record(artwork_id:str,group_user_id:str,group_id:str) -> None:
        '''记录涩图获取日志'''
        proc = execute_procedure("ero_log_update",args_in=[artwork_id,group_user_id,group_id],args_out=[])
        proc.proc()

    @staticmethod
    def block_record(artwork_id:str,is_blocked:bool) -> None:
        '''记录涩图是否被屏蔽'''
        proc = execute_procedure("ero_log_blockupdate",args_in=[artwork_id,is_blocked],args_out=[])
        proc.proc()




'''
功能一：涩图 get 
当用户在对话框发送想看涩图的信息后，轻雪酱会识别并返回一张涩图
'''
# 设置响应规则
async def message_checker_setu_get(event:Event):
    msg = event.get_plaintext()         # 从事件中提取消息纯文本
    # 正则匹配消息文本
    target_pattern_list = ['.*[来整搞][张点](.*)[色涩瑟]图?.?',
                        '[^(不)]*(色色|涩涩|瑟瑟)！?$',
                        '[(让我)(就要)](看看|康康|访问|色色|涩涩)！?$']
    rule_result = False
    for pattern in target_pattern_list:
        if re.match(pattern,msg):
            rule_result = True
            break
    return rule_result
rule_setu_get = rule.Rule(message_checker_setu_get)         # 生成规则（如有多个checker子规则，用逗号隔开）
# 配置事件响应器
setu_get_matcher = on_message(rule=rule_setu_get,priority=5,block=True)
# 功能主体
@ setu_get_matcher.handle()
async def handling(bot:Bot,event:Event,msg: Message = EventMessage()):
    session_id = event.get_session_id().split("_")
    group_id = session_id[1]
    user_id = session_id[2]
    msg = msg.extract_plain_text()          #获取命令信息
    if "！" in msg:       #日常对话
        sleep(1)
        await setu_get_matcher.send("好啦好啦就让你色色吧！")
        await SendArtwork.random(bot,group_id,user_id)
        sleep(6)
        await setu_get_matcher.finish("要注意节制喵")
    else:
        # 每日首次特殊对话
        proc = execute_procedure('ero_log_query',[f'{user_id}',f'{group_id}'],['times_of_ero'])
        times_of_ero = proc.proc()['times_of_ero']
        if not times_of_ero:
            raw_data = await bot.call_api('get_group_member_info',**{      
                'group_id': group_id,
                'user_id' : user_id
                })
            nickname = raw_data['nickname']
            await setu_get_matcher.send(f"检测到{nickname}发出的色色请求！")
        prob = random.random()
        # 禁止涩涩
        if prob <= 0.95-0.94*2**(-18/(times_of_ero+1)):
            await SendArtwork.random(bot,group_id,user_id)
        elif times_of_ero <= 1:
            await setu_get_matcher.finish(f"哼！总之就是不可以色色！")
        else:
            await setu_get_matcher.finish(f"今天你都色色{times_of_ero}次了，不可以再色色！")

'''
功能二：定时任务——随机时间涩涩
每天9点到20点范围内，发起随机1-4次突击涩涩事件
'''
@scheduler.scheduled_job(trigger="cron", hour="01",minute="00",timezone='Asia/Shanghai',id="setu_routine")   
async def setu_schedule():
    # 设定当日突击涩涩时间
    times = random.randint(1,4)                        # 每日1-4次突击涩涩
    hour_list = []
    for i in range(times):
        hour = random.randint(9,19)
        if hour not in hour_list:               # 同一小时最多只出现一次
            ero_time = datetime.combine(datetime.today(),time(hour=hour,minute=random.randint(0,59),second=random.randint(0,59)))
            scheduler.add_job(_pop_ero,trigger="date",run_date=ero_time,timezone='Asia/Shanghai',id=f"ero_time{i}")
            hour_list.extend((hour,hour+1))
        else:
            i = i-1
            continue
    print("<setu> 今日涩涩事件已添加")

async def _pop_ero():
    greetings = [
        "突击涩涩时间！主人工作辛苦啦，工作之余也不要忘记涩涩哦！",
        "主人工作辛苦啦！来张涩图休息一下吧~",
        "千年的人类经验告诉我们，涩涩才是第一生产力喔~来张涩图休息一下吧！",
        "主人工作虽然很努力，也要让眼睛和身体休息一下喔，看完这张涩图，就来和轻雪酱一起做柔软操吧~",
        "♪ ~ ♫ ~ ♬ ~ ♩ ~~~",
        "呀！",
        "涩涩时间到了喔！",
        "要做的事情堆积如山呢，但还是要加油喔！",
        "哇啊...工作超多呢...",
        "加油~~主人~~加油~~",
        "偶尔也要顾虑一下身体啊，我很担心主人的健康呢！",
        "轻雪酱的工作时间到了！",
        "轻雪酱也想协助主人的工作！"
    ]
    msg_list = [greetings[random.randint(0,len(greetings)-1)]]
    await sending_message(msg_list)
    bot = get_bot()
    group_id_tuple = ('670404622',)
    for group_id in group_id_tuple:
        await SendArtwork.random(bot,group_id)

'''
功能三: paid
指定artwork_id, 发送涩图
'''
paid = on_command('paid',priority=5)

@paid.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()):
    artwork_id = args.extract_plain_text()  # 首次发送命令时跟随的参数
    if artwork_id:
        matcher.set_arg("artwork_id",args)  # 如果用户发送了参数则直接赋值

@paid.got("artwork_id", prompt="paid是根据p站作品id查询图片的功能~\n如果主人不了解的话, 可以尝试继续输入下面这个作品id喔:\n\t 87601177")
async def handle_paid(bot:Bot,event:Event,artwork_id:str = ArgStr('artwork_id')):
    try:
        artwork_id = int(artwork_id)
    except:
        await paid.finish("paid的参数是p站的作品id喔, 一般是10位以内的数字\n如果主人不了解的话, 可以尝试输入下面这串指令:\n/paid 87601177")
    else:
        session_id = event.get_session_id().split("_")
        group_id = session_id[1]
        await SendArtwork.paid(str(artwork_id),bot,group_id)

'''
功能四: puid
指定user_id, 发送该用户信息及其涩图
'''
puid = on_command('puid',priority=5)

@puid.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()):
    puser_id = args.extract_plain_text()  # 首次发送命令时跟随的参数
    if puser_id:
        matcher.set_arg("user_id",args)  # 如果用户发送了参数则直接赋值

@puid.got("user_id", prompt="puid是根据p站画师id查询其作品的功能~\n主人如果不了解的话, 可以尝试继续输入下面这个用户id喔:\n446171")
async def handle_puid(bot:Bot,event:Event,puser_id:str = ArgStr('user_id')):
    try:
        puser_id = int(puser_id)
    except:
        await puid.finish("puid的参数是p站的画师id喔, 一般是10位以内的数字~\n主人如果不了解的话, 可以尝试输入下面这串指令:\n/puid 446171")
    else:
        session_id = event.get_session_id().split("_")
        group_id = session_id[1]
        await SendArtwork.puid(str(puser_id),bot,group_id)

'''
功能五: 管理关注列表
增删改关注的画师
'''
# 添加画师
puser_add = on_command('关注画师',priority=5,aliases={'添加画师','puser add'})

@puser_add.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()):
    puser_id = args.extract_plain_text()  # 首次发送命令时跟随的参数
    if puser_id:
        matcher.set_arg("puser_id",args)  # 如果用户发送了参数则直接赋值

@puser_add.got("puser_id", prompt="主人可以输入p站用户id来关注画师, 之后就能收到更新推送啦~\n主人如果不了解的话, 可以尝试继续输入下面这个用户id喔:\n446171")
async def handle_puser_add(event:Event,puser_id:str = ArgStr('puser_id')):
    try:
        puser_id = int(puser_id)
    except:
        await puser_add.finish("puser add的参数是p站的画师id喔, 一般是10位以内的数字~\n主人如果不了解的话, 可以尝试输入下面这串指令:\n/puser add 446171")
    else:
        session_id = event.get_session_id().split("_")
        group_id = session_id[1]
        code,puser_name = SetuConfig.puser_subscribe(group_id,str(puser_id))
        if code == 403: # 重复添加
            await puser_add.finish(f'画师 {puser_name} ({puser_id}) 已经在关注列表中了喔~')
        elif code == 404:   # 画师不存在
            await puser_add.finish(f'画师 {puser_id} 不存在喔! 请主人确认是否是pixiv的用户id吧!')
        elif code == 200:   # 成功添加
            await puser_add.finish(f'成功关注画师 {puser_name} ({puser_id}), 之后会向主人推送这位画师的更新作品喔~')

# 删除画师
puser_remove = on_command('取关画师',priority=5,aliases={'移除画师','puser remove'})

@puser_remove.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()):
    puser_id = args.extract_plain_text()  # 首次发送命令时跟随的参数
    if puser_id:
        matcher.set_arg("puser_id",args)  # 如果用户发送了参数则直接赋值

@puser_remove.got("puser_id", prompt="主人可以输入p站用户id来移除关注画师, 之后就不会收到其作品的更新推送啦~")
async def handle_puser_add(event:Event,puser_id:str = ArgStr('puser_id')):
    try:
        puser_id = int(puser_id)
    except:
        await puser_remove.finish("puser remove的参数是p站的画师id喔, 一般是10位以内的数字~")
    else:
        session_id = event.get_session_id().split("_")
        group_id = session_id[1]
        code,puser_name = SetuConfig.puser_unsubscribe(group_id,str(puser_id))
        if code == 404: # 画师不在列表中
            await puser_remove.finish(f'画师 {puser_id} 不在原有的关注列表中喔~')
        elif code == 200:   # 成功删除
            await puser_remove.finish(f'成功取关画师 {puser_name} ({puser_id}), 之后主人不会再收到这位画师的更新推送啦~')

# 查看画师
puser_check = on_command('查看画师',priority=5,aliases={'查看关注画师','puser check','puser'})

@puser_check.handle()
async def handle_first_receive(event:Event):
    session_id = event.get_session_id().split("_")
    group_id = session_id[1]
    puser_list = SetuConfig().puser_check(group_id)
    if puser_list:
        msg = f"当前共关注画师 {len(puser_list)} 位：\n"
        for puser_id,puser_name in puser_list:
            msg = msg + f'{puser_id}'+(24-len(puser_id)*2)*' '+f'{puser_name}\n'
        await puser_check.finish(msg)
    else:
        await puser_check.finish("本群还没有关注的画师喔, 可以通过/puser add命令来添加画师~")


'''
功能六：定时任务——推送关注画师作品
每天12点整，向群中推送关注画师的更新作品
'''
@scheduler.scheduled_job(trigger="cron", hour="03",minute="00",timezone='Asia/Shanghai',id="subscribe_user_check")   
async def subscribe_user_check():
    # 每日1点获取昨日画师更新情况, 获取待发送的作品list, 并更新json
    json = SetuConfig.read_json('subscribe_puser_list')
    subscribe_artwork_id_dict:dict[str,list] = {}
    for group_id in json.keys():
        artwork_id_list = []
        for puser_id in json[group_id].keys():
            user = ArtworkUser(puser_id)
            for artwork_id in user.artwork_list:
                if artwork_id != json[group_id][puser_id]:
                    artwork_id_list.append(artwork_id)  # 如果迭代的作品id不是json中记录的最新id, 则说明有更新的作品被发表
                else:
                    json[group_id][puser_id] = user.artwork_list[0] # 更新至最新作品
                    break
        subscribe_artwork_id_dict[group_id] = artwork_id_list
    SetuConfig.write_json('subscribe_puser_list',json)
    # 按每个群的ai/r18过滤条件筛选作品list, 并将每个list拆分成3个作品一组
    for group_id,artwork_id_list in subscribe_artwork_id_dict.items():
        for artwork_id in artwork_id_list:
            artwork = Artwork(artwork_id)
            # 过滤作品列表
            if not SetuConfig(group_id).ai_allow:
                if artwork.is_ai == True:
                    artwork_id_list.remove(artwork_id)
            if not SetuConfig(group_id).r18_allow:
                if artwork.is_r18 == True:
                    artwork_id_list.remove(artwork_id)
            # 拆分list至3个一组
            n = 3
            subscribe_artwork_id_dict[group_id] = [artwork_id_list[i:i+n] for i in range(0,len(artwork_id_list),n)]

    # 添加推送事件
    run_time = datetime.combine(datetime.today(),time(hour = 12,minute= 00,second= 00))
    artwork_id_list:list[list[str]] = subscribe_artwork_id_dict[group_id]
    for group_id in json.keys():
        if json[group_id]:  # 群内有关注画师才会进入推送流程
            for num_of_set in range(len(artwork_id_list)):
                scheduler.add_job(_subscribe_puser_send,args=[subscribe_artwork_id_dict[group_id][num_of_set],group_id],trigger="date",run_date = run_time,timezone='Asia/Shanghai',id=f"subcribe_puser_send({group_id}-{num_of_set})")
    print("<setu> 已更新关注画师的昨日作品")

async def _subscribe_puser_send(artwork_id_list,group_id):
    artwork_list = [Artwork(artwork_id) for artwork_id in artwork_id_list]
    if artwork_list == []:
        await sending_message(("本群关注的画师今天都没有更新喔, 使用/puser add功能来添加更多画师吧~",),group_id)
    else:
        bot = get_bot()
        log_recorder = '0'
        await SendArtwork.sending_forward(bot,group_id,log_recorder,artwork_list)
        await sending_message(("滴滴！请主人查收今日关注画师作品~",),group_id)

'''
功能七: ai/r18限制管理
通过/ero ai 或/ero r18命令来限制随机涩图的类型
'''

ero_type_comm = on_command('ero',priority=5,aliases={'涩图'})

@ero_type_comm.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()):
    arg = args.extract_plain_text()  # 首次发送命令时跟随的参数
    if arg:
        type = arg.split()[0]
        matcher.set_arg("type",type)
        allowance = ''
        try:
            allowance = arg.split()[1]
        except:
            pass
        else:
            matcher.set_arg("allowance",allowance)

@ero_type_comm.got("type", prompt='主人已进入涩图管理操作台~在这里可以对随机涩图的类型(ai/r18)进行限制喔!\n例如, 希望能随机到r18图片的话, 请主人输入"r18 1"\n希望不随机到ai生成图片的话, 请输入"ai 0"')
@ero_type_comm.got("allowance", prompt='主人可以继续输入"0"或"1"来表示禁止/允许此类型图片的出现~')
async def handle_puser_add(event:Event,type:str = ArgStr('type'),allowance:str = ArgStr('allowance')):
    group_id = event.get_session_id().split("_")[1]
    config = SetuConfig(group_id).configs
    type = type.lower()
    if type not in ['ai','r18']:
        await ero_type_comm.finish("不准点炒饭, 哼! ")
    if allowance == '0':
        config.set_config(['allowance',type,f'{group_id}'],False)
        await ero_type_comm.finish("设置完毕~")
    elif allowance =='1':
        config.set_config(['allowance',type,f'{group_id}'],True)
        await ero_type_comm.finish("设置完毕~")
    else:
        await ero_type_comm.finish("不准点炒饭, 哼!")







# 启动项
asyncio.run(ArtworkFolder.replenishment())   # 启动时填充涩图
asyncio.run(setu_schedule())        # 启动时更新当日突击涩涩事件
# asyncio.run(subscribe_user_check()) # 启动时更新关注画师作品列表(花费时间较长(每个画师约2-5秒), 建议不自启)


'''
待写：
单个作品图片数量过多的保护机制
根据用户名搜用户的 pname 功能
涩图 get 参数命令
'''


'''
废弃功能：使用nginx反向代理实现涩图发送
'''
# import socket
# async def setu_get(url_p0):
#     my_ip = socket.gethostbyname(socket.gethostname())     # 获取本机ip地址 
#     url_pic0 = "http://" + my_ip + url_p0.replace("https://i.pximg.net","")
#     await sending_message([f"[CQ:image,file={url_pic0}]"],group_id)
