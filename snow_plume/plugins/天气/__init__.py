# 声明插件依赖
from nonebot import require, on_command
require("nonebot_plugin_apscheduler")

# 从插件中导入scheduler对象

from nonebot_plugin_apscheduler import scheduler

# 添加处理依赖
from nonebot.params import CommandArg, ArgStr
from nonebot.matcher import Matcher
from nonebot.adapters import Bot,Event,Message

# 发送信息
from nonebot import get_bot
from snow_plume.handling_message import sending_message

# 导入定时任务中需要用到的模块
import requests
import json
import re
import os
from time import sleep
from random import gauss,randint
from datetime import datetime,timedelta,time
import asyncio
from pathlib import Path
import yaml

__plugin_des__ = "简单（？）的天气预报插件"
__plugin_cmd__ = "[天气/weather] [类型] [地区/城市名]"
__plugin_author__ = "wadanoharine & Dg_Han"
__plugin_ver__ = "v1.1.1a1"

configs = yaml.load(open(Path()/"configs"/"weather"/"configs.yml","r",encoding="utf-8"), Loader=yaml.FullLoader)
"""
configs读取内容
- group_id: 有权限使用插件的群号列表
  - location: 预报城市的城市代码（代码可从和风天气官网调取"城市搜索"api获取）
- weather_api_key: 和风天气的api_key（可登陆和风天气官网获取）
- paying_user: 是否为和风天气付费用户（默认为False，设置不正确将导致报错） 
"""
if not os.path.exists(Path()/"data"/"weather"):
    os.mkdir(Path()/"data"/"weather")

try:
    with open(Path()/"data"/"weather"/"alarm.json", "r", encoding="utf-8") as f:
        cache = f.readlines()
        jsonstr = "".join([_.strip() for _ in cache])
        alarm_record = json.loads(jsonstr)
except:
    alarm_record = {"time": "No_Record"}
"""
alarm.json存储内容
- time: 上次预警查询时间
- last_warning_list: 上次查询时存储预警信息（与alarm_last_list格式相同）
"""
group_id_list = [int(_) for _ in configs["group_id"].keys()]
weather_api_key = configs["weather_api_key"]
paying_user = configs["paying_user"]

# 时间参数初始化
today = datetime.date(datetime.today())     # 初始化今天日期
weekday = datetime.now().strftime("%A")     # 初始化今天星期
wake_up_time = datetime.now()               # 初始化轻雪酱起床时间


# 通用函数一：每日1点重置参数和事件
@scheduler.scheduled_job(trigger="cron", hour="01",minute="00",timezone='Asia/Shanghai',id="weather_routine")   
async def weather_schedule():
    global today,weekday,jitter
    # 更新时间参数
    today = datetime.date(datetime.today())     # 更新今天日期
    weekday = datetime.now().strftime("%A")     # 更新今天星期
    # 设定当日轻雪酱起床时间
    Sunrise_time = get_api(("三日天气预报",),"101020100")[0]['daily'][0]['sunrise']     # 获取日出时间
    jitter = gauss(0,8)                                                   # 设置起床偏差
    wake_up_time = datetime.combine(datetime.today(),datetime.time(datetime.strptime(Sunrise_time,"%H:%M") + timedelta(minutes=jitter)))     # 日出时间+起床偏差组合成为起床时间
    scheduler.add_job(morning_report,trigger="date",run_date=wake_up_time,timezone='Asia/Shanghai',id="morning_report")                      # 添加当天的晨间预报任务
    print("<weather_report> 今日时间校正完毕")


# 通用函数二：从和风天气api中获取天气数据
def get_api(request_list:tuple, location_id: str) -> list:
    '''
    调取和风天气api，获取天气数据   \n
    ----------
    Parameters  
    - request_list（必填）：以元组/列表形式封装需要调取的接口，如 "('三日天气预报','实时天气预报')"   \n
        -- 可选接口如下：\n
            '三日天气预报'，'实时天气预报'，'逐小时预报'，'实时空气质量'，'空气质量每日预报'，'天气指数预报'，'天气灾害预警', '城市搜索'
    - location / location_id（必填）：所需天气预报地区名称 / 地区代码
        -- 注意：只有城市搜索请求可以填入 location 字符串，其余api请求都只能填入 location_id 九位纯数字字符串
    ----------
    Returns     
    - result_list：接口调取结果（json形式），顺序同request_list
    '''
    url_dict = {
        "三日天气预报":"https://devapi.qweather.com/v7/weather/3d?",
        # 日出日落sunrise/sunset；月出月落moonrise/moonset；月相moonPhase(含moonPhaseIcon)；
        # 最值气温tempMax/tempMin；天气textDay/textNight(含iconDay/iconNight)
        # 风向windDirDay/windDirNight；风力等级windScaleDay/windScaleNight；风速windSpeedDay/windSpeedNight；
        # 当天总降水量precip；紫外线强度指数uvIndex；相对湿度humidity；大气压强pressure；能见度vis；云量cloud
        "实时天气预报":"https://devapi.qweather.com/v7/weather/now?",
        # 当前温度temp；体感温度feelslike；天气text(含icon)
        # 风向windDir；风力windScale；风速windSpeed
        # 相对湿度humidity；当前小时累计降水量precip
        # 大气压强pressure；能见度vis；云量cloud；露点温度dew
        "逐小时预报":"https://devapi.qweather.com/v7/weather/24h?",
        # 预报所处时间fxTime
        # 温度temp；天气text(含icon)
        # 风向windDir；风力windScale；风速windSpeed
        # 相对湿度humidity；当前小时累计降水量precip；当前小时降水概率pop
        # 大气压强pressure；云量cloud；露点温度dew
        "实时空气质量":"https://devapi.qweather.com/v7/air/now?",
        # 空气质量指数aqi；空气质量指数级别category；空气主要污染物primary(空气质量为优时返回NA)
        # PM10:pm10, PM2.5:pm2p5, 二氧化氮:no2, 二氧化硫:so2, 一氧化碳co, 臭氧o3
        "空气质量每日预报":"https://devapi.qweather.com/v7/air/5d?",
        # 预报所处日期fxDate
        # 空气质量指数aqi；空气质量指数级别category；空气主要污染物primary(空气质量为优时返回NA)
        "天气指数预报":"https://devapi.qweather.com/v7/indices/3d?type=0&",
        # type 1-16分别为：1.运动指数 2.洗车指数 3.穿衣指数 4.钓鱼指数 5.紫外线指数 6.旅游指数 7.过敏指数 8.舒适度指数 9.感冒指数 10.空气污染扩散条件指数 11.空调开启指数 12.太阳镜指数 13.化妆指数 14.晾晒指数 15.交通指数 16.防晒指数
        # 预报所处日期date；生活指数类型type；生活指数类型名称name
        # 生活指数预报等级level；等级描述category；详细描述text
        "天气灾害预警":"https://devapi.qweather.com/v7/warning/now?",
        # ID：id
        # 预警发布单位sender；发布时间pubTime；标题title；
        # 预警开始/结束时间startTime/endTime；发布状态status
        # 预警严重等级severity；预警类型名称typeName；预警详细文字描述text
        "城市搜索":"https://geoapi.qweather.com/v2/city/lookup?",
        # name: 行政规划名; id: ID; adm2: 上一级行政区划名称; adm1: 所属一级行政区域
        # lat: 纬度; lon: 经度; tz: 所在时区; utcOffset: 与UTC偏移的小时数; isDst: 是否处于夏令时
        # rank: 内置排名评分
        }
    
    result_list = []
    if paying_user:                                                         # 付费版用户调取的api链接和免费版有差异
        for k in url_dict.keys():
            v_seg = url_dict[k].split("dev")
            url_dict[k] = "".join((v_seg[0],v_seg[1]))
    for req in request_list:
        pattern = "\d{9}"                                                   #判断location_id合法性
        if not re.match(pattern, location_id) and request_list != ("城市搜索", ):
            raise ValueError("请输入城市代码而非城市名称！城市代码可通过本api中的`城市搜索`方式获取")
        
        url = "".join((url_dict[req],"location=",location_id,"&key=",weather_api_key)) # 拼接request的api
        result_raw = requests.get(url)                                      # 发起请求
        result_seg = json.loads(result_raw.text)                            # 将返回结果转为json格式
        result_list.append(result_seg)                                      # 存入result列表中
    return result_list

# 定时任务一：每晚预报次日天气

@scheduler.scheduled_job(trigger="cron",hour="22",minute="00",timezone='Asia/Shanghai',id="night_report")
async def night_report():
    msg_list = []
    greetings_night = {
        "Monday"   : "晚上好！休息的时间到了哟！\n\n    又回到工作的状态了呢，主人今天也辛苦啦~\n    现在就请主人好好地享受休息时间吧！让轻雪酱来为你预报明日天气：",
        "Tuesday"  : "晚上好！休息的时间到了哟！\n\n    顺利结束了一天的工作，现在就好好放松吧~ 轻雪酱会为主人预报明天的天气喔！",
        "Wednesday": "晚上好！休息的时间到了哟！\n\n    主人今天过得如何呢？轻雪酱今天一天都陪伴在主人身边，感觉非常开心呢！如果主人也是这样想的话...\n    好！要开始预报天气了喔：",
        "Thursday" : "晚上好！休息的时间到了哟！\n\n    一天过得真快呢，总感觉今天才刚刚开始，太阳就已经落下了...主人也是这么觉得的吗？\n    好了！接下来是明天的天气预报：",
        "Friday"   : "晚上好！休息的时间到了哟！\n\n    明天开始就是周末了，主人周末里有没有什么安排呢？如果没有其他事的话...可以把时间留给轻雪酱吗？",
        "Saturday" : "晚上好！休息的时间到了哟！\n\n    虽然明天也是休息日，但主人也不要熬夜太晚喔，轻雪酱可是非常关心主人的身体健康呢！",
        "Sunday"   : "晚上好！休息的时间到了哟！\n\n    一周就要结束了，主人过得还充实吗？新的一周也请加油喔，轻雪酱会为你鼓劲的！\n    那么，明天的天气是..."
    }
    # 封装消息I（问候语）
    msg_list.append(greetings_night[weekday])
    # 获取结果
    request_list = ("三日天气预报","天气指数预报")
    for group_id in group_id_list:
        location_list = configs["group_id"][group_id]["location_list"]
        for location in location_list.keys():
            result = get_api(request_list, location_list[location])
            weather_tommorow_Day = result[0]['daily'][1]['textDay']     # 次日白天天气
            weather_tommorow_Night = result[0]['daily'][1]['textNight'] # 次日晚上天气
            temp_Max_tommorow = result[0]['daily'][1]['tempMax']        # 次日最高气温
            temp_Min_tommorow = result[0]['daily'][1]['tempMin']        # 次日最低气温
            wind_tommorow = result[0]['daily'][1]['windScaleDay']       # 次日风力等级
            sport_tommorow = result[1]['daily'][16]['category']         # 次日运动指数
            cold_tommorow = result[1]['daily'][24]['category']          # 次日感冒指数
            # 结果格式化
            if weather_tommorow_Day == weather_tommorow_Night:
                weather_report = f'{today+timedelta(days=1)}\n{location}天气：{weather_tommorow_Day}  ({temp_Min_tommorow}℃~{temp_Max_tommorow}℃)\n风力等级：{wind_tommorow}级\n运动指数：{sport_tommorow}\n感冒指数：{cold_tommorow}'
            else:
                weather_report = f'{today+timedelta(days=1)}\n{location}天气：{weather_tommorow_Day}转{weather_tommorow_Night}  ({temp_Min_tommorow}℃~{temp_Max_tommorow}℃)\n风力等级：{wind_tommorow}级\n运动指数：{sport_tommorow}\n感冒指数：{cold_tommorow}'
            # 封装消息II（天气预报）
            msg_list.append(weather_report)
            # 寒潮/热浪预警
            if float(result[0]['daily'][0]['tempMin']) - float(result[0]['daily'][1]['tempMin']) >= 8:
                msg_list.append(f"{location}明天会冷很多喔！请多加衣服，注意保暖吧！")
            elif float(result[0]['daily'][1]['tempMax']) - float(result[0]['daily'][0]['tempMax']) >= 8:
                msg_list.append(f"{location}明天会比今天热一些喔！请提前搭配好合适的衣物吧！")
        await sending_message(msg_list, group_id)


# 定时任务二：晨间预报当日天气

async def morning_report():

    # 早起/晚起特殊对话
    special_wake_up_bool = False
    special_wake_up = ""
    if jitter > 15.2:       # 触发条件：起床偏差值达到15.2分钟(1.9个标准差，发生概率约2.87%)以上
        special_wake_up = "唔呃呃...不小心睡过头了...得赶快给主人播报天气才行......"
        special_wake_up_bool = True
    elif jitter < -15.2:
        special_wake_up = "轻雪酱和主人说早安啦！诶，主人还在睡梦中？嘿嘿嘿...准备完天气播报，就偷偷拍一张主人睡觉的样子吧！"
        special_wake_up_bool = True
        
    # 日常问候
    greetings_morning = {
        "Monday"   : f'早上好主人！太阳起床了哟~ 今天是{today.month}月{today.day}日，新一周的早安播报要启动了喔！',
        "Tuesday"  : f'早上好主人！太阳起床了哟~ 今天是{today.month}月{today.day}日，是周二喔，开始今天的早安播报吧~',
        "Wednesday": f'早上好主人！太阳起床了哟~ 今天是{today.month}月{today.day}日，是周三喔，开始今天的早安播报吧~',
        "Thursday" : f'早上好主人！太阳起床了哟~ 今天是{today.month}月{today.day}日，是周四喔，开始今天的早安播报吧~',
        "Friday"   : f'早上好主人！太阳起床了哟~ 今天是{today.month}月{today.day}日，也是工作日的最后一天，今天也请提起干劲加油吧！轻雪酱会在背后一直支持主人的！就从今天的早安播报开始~',
        "Saturday" : f'早上好主人！太阳起床了哟~ 今天是{today.month}月{today.day}日，终于到周末了呢，听完今天的早安播报，主人就好好享受假期吧~',
        "Sunday"   : f'早上好主人！太阳起床了哟~ 今天是{today.month}月{today.day}日，是周日喔！可以暂时放下紧张的工作了呢，今天就闲散地度过吧~'
    }

    # 获取天气数据，准备天气播报
    request_list = ("实时天气预报","实时空气质量","逐小时预报")
    for group_id in group_id_list:
        msg_list = []
        # 封装消息I（问候语）
        if special_wake_up_bool:
            msg_list.append(special_wake_up)
        else:
            msg_list.append(greetings_morning[weekday])

        location_list = configs["group_id"][group_id]["location_list"]
        for location in location_list.keys():
            result = get_api(request_list, location_list[location])

            # 1.极端天气状况预警（水平能见度、大风预警）
            warning_bool = False
            warning_report = ""
            # 1.1 水平能见度预警(2km以下)
            vision = float(result[0]['now']['vis'])               # 获取当前水平能见度
            if vision <= 2:
                if vision <= 1:
                    if vision <= 0.5:
                        warning_report = "".join((warning_report,f'唔啊啊..外面伸手不见五指呢...现在{location}的能见度只有{vision*1000:.0f}m了，'))
                    else:
                        warning_report = "".join((warning_report,f'{location}今天的雾有点浓，现在的能见度只有{vision*1000:.0f}m了，'))
                else:
                    warning_report = "".join((warning_report,f'{location}外面视野不太好呢，现在的能见度只有{vision:.0f}km了，'))
                warning_bool = True
            # 1.2 大风预警(4级风及以上)
            wind_speed = float(result[0]['now']['windSpeed'])     # 获取当前风速
            if wind_speed >= 20:
                if warning_bool:
                    warning_report = "".join((warning_report,'而且'))
                if wind_speed >= 29:
                    if wind_speed >= 39:
                        warning_report = "".join((warning_report,f'轻雪酱要被风吹跑啦！现在{location}的风速已经达到{wind_speed}km/h了！'))
                    else:
                        warning_report = "".join((warning_report,f'{location}今天的风超级大！风速已经达到{wind_speed}km/h了！'))
                else:
                    warning_report = "".join((warning_report,f'{location}今天的风有点大呀，风速达到{wind_speed}km/h了，'))        
                warning_bool = True        
            warning_report = "".join((warning_report,f"在{location}的主人如果出门的话，一定要注意安全呀！\n\n接下来是今天的天气情况："))

            # 2.今日天气情况预报（降水情况，空气质量）
            weather_report = f"{location}\n    "
            # 2.1 降水情况预报
            weather_report = "".join((weather_report,"天气方面："))
            weather_of_hour = result[2]['hourly']                 # 获取今日逐小时天气情况
            # 数据预处理1：从结果中提取某时间点的降水量，以(fxTime,precip)形式存放在raw_dict列表中
            raw_dict = []                 
            for seg in weather_of_hour:
                fxTime = int(seg['fxTime'].split("T")[1].split(":")[0])
                precip = float(seg['precip'])
                if fxTime == 0:           # 只统计当日数据
                    fxTime = 24
                    precip_of_hour = (fxTime,precip)
                    raw_dict.append(precip_of_hour)
                    break
                precip_of_hour = (fxTime,precip)
                raw_dict.append(precip_of_hour)
            # 数据预处理2：进一步抽取天气变化情况 (晴->雨 or 雨->晴)，以(time,convert_type)形式存放在weather_change列表中
            weather_change = []             # (convert_type:-1代表由雨转晴，1代表由晴转雨)
            sum = 0
            product = 0
            for i in range(1,len(raw_dict)):
                sum = raw_dict[i][1]+raw_dict[i-1][1]                   
                product = raw_dict[i][1]*raw_dict[i-1][1]
                if sum > 0 and product == 0:                # 如果相邻两数之和>0，而乘积=0，则说明天气有变化
                    if raw_dict[i][1] == 0:
                        time_of_clearing_up = (raw_dict[i][0],-1)
                        weather_change.append(time_of_clearing_up)
                    else:
                        time_of_raining = (raw_dict[i][0],1)
                        weather_change.append(time_of_raining)
            # 分情况将预报对话整理进weather_report字符串
            percip_now = raw_dict[0][1]
            if len(weather_change) == 0:                # 情况一：一整天都下雨/不下雨
                if percip_now:
                    weather_report = "".join((weather_report,"今天下雨会下一整天，主人如果要出门的话，就请带好伞吧！"))
                else:
                    weather_report = "".join((weather_report,"今天一整天都天晴喔，"))
            elif len(weather_change) == 1:              # 情况二：现在下雨，但某个时间后会放晴（现在放晴，但某个时间会下雨）
                if percip_now:
                    weather_report = "".join((weather_report,f'现在虽然在下雨，不过自{weather_change[0][0]}点开始雨就会停。这段时间主人如果要出门的话，就请带好伞吧！'))
                else:
                    weather_report = "".join((weather_report,f'现在虽然天晴，不过自{weather_change[0][0]}点起就会开始下雨。主人如果要出门的话，就请带好伞吧！'))
            elif len(weather_change) >= 2:              # 情况三：天气在一天内多次变化
                if percip_now:                  
                    weather_report = "".join((weather_report,f'现在虽然在下雨，不过{weather_change[0][0]}点后雨会停，随后'))
                else:                 
                    weather_report = "".join((weather_report,'现在虽然天晴，不过'))
                for i in range(len(weather_change)):
                    if weather_change[i][1] == 1:
                        try:
                            weather_report = "".join((weather_report,f'{weather_change[i][0]}-{weather_change[i+1][0]-1}点,'))    
                        except:
                            weather_report = "".join((weather_report,f'{weather_change[i][0]}点之后都-'))
                weather_report = weather_report[:-1]
                weather_report = "".join((weather_report,"会下雨。主人如果要出门的话，就请带好伞吧！"))
            # 2.2 空气质量预报
            weather_report = "".join((weather_report,"\n\n"))
            air_quality = result[1]['now']                      # 获取空气质量

            weather_report = "".join((weather_report,f'    空气质量方面：当前空气质量水平为{air_quality["category"]}，AQI指数为{air_quality["aqi"]}。'))
            if int(air_quality["level"]) >= 3:                  # 空气质量为轻度污染以下的特殊对话
                weather_report = "".join((weather_report,"请主人适当减少户外活动喔！"))
            else:
                weather_report = "".join((weather_report,"新鲜空气是大自然的馈赠~"))
            
            # 封装消息II(天气预警，随后进行天气播报)
            if warning_bool:
                msg_list.append(warning_report)
            
            msg_list.append(weather_report)

            # 发送消息
        await sending_message(msg_list, group_id)


# 定时任务三：天气灾害预警(每10分钟探测一次)

#alarm_last_list = {}
alarm_last_list = alarm_record["last_alarm"] if alarm_record["time"] != "No_Record" else {}
@scheduler.scheduled_job(trigger="interval", minutes = 10, timezone='Asia/Shanghai', id="weather_alarm")
async def weather_alarm():
    global alarm_last_list
    request_list = ("天气灾害预警",)
    alarm_list = {}
    for group_id in group_id_list:
        location_list = configs["group_id"][group_id]["location_list"]
        for location in location_list.keys():
            result = get_api(request_list, location_list[location])
        alarm_list[group_id] = result[0]['warning']
    
        if alarm_list[group_id] == alarm_last_list.get(group_id,[]):       # 如收到的预警信息和十分钟前收到的一致，则不做响应
            pass
        else:     # 如收到的预警信息和十分钟前不同，则进入响应处理流程
            msg_list = []
            new_alarm_list = [_ for _ in alarm_list[group_id] if _ not in alarm_last_list.get(group_id,[])]
            remain_alarm_list = [_ for _ in alarm_list[group_id] if _ in alarm_last_list.get(group_id,[])]
            cancel_alarm_list = [_ for _ in alarm_last_list.get(group_id,[]) if _ not in alarm_list[group_id]]
            last_alarm_info_dict = {}
            for alarm in alarm_last_list.get(group_id,[]):
                last_alarm_info_dict[(alarm["sender"], alarm["typeName"])] = (alarm["level"], alarm["text"])
            alarm_type_list = [(_["sender"], _["typeName"]) for _ in alarm_list[group_id]]
            level_convert = {"蓝色":4, "黄色":3, "橙色":2, "红色":1}

            time_pattern = r"\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时\d{1,2}分"

            if cancel_alarm_list:               # 先处理取消的警报
                alarm_brief = []
                for alarm in cancel_alarm_list:
                    if (alarm["sender"], alarm["typeName"]) not in alarm_type_list:    # 如果某地之前有而现在没有的警报类型不在现有警报中存在，则证明警报解除，而非升级或降级
                        alarm_pubTime = re.search(time_pattern,alarm["text"])[0]
                        alarm_brief.append(f'{alarm["sender"]}于{alarm_pubTime}发布的{alarm["typeName"]}{alarm["level"]}预警')
                if alarm_brief:
                    msg_list.append(f"先前{','.join(alarm_brief)}已解除")
            if new_alarm_list:                  # 再处理新出现的警报
                msg_list.append("滴滴！轻雪酱收到一则天气预警：")
                for alarm in new_alarm_list:
                    if (alarm["sender"], alarm["typeName"]) not in last_alarm_info_dict.keys():    # 如果某地新警报类型不在旧警报类型中，则说明是新警报，而不是旧警报的等级变化
                        msg_list.append(alarm['text'])
                    else:
                        last_alarm_level = last_alarm_info_dict[(alarm["sender"], alarm["typeName"])][0]
                        pre_grade = "升" if level_convert[alarm["level"]] > level_convert[last_alarm_level] else "降"
                        msg_list.append(f'先前{alarm["sender"]}发布的{alarm["typeName"]}{last_alarm_level}预警已经{pre_grade}级为{alarm["typeName"]}{alarm["level"]}预警，当前{alarm["text"]}')
            if remain_alarm_list:               # 再处理保持不变的警报
                alarm_brief = []
                for alarm in remain_alarm_list:
                    alarm_pubTime = re.search(time_pattern,alarm["text"])[0]
                    alarm_brief.append(f'{alarm["sender"]}于{alarm_pubTime}发布的{alarm["typeName"]}{alarm["level"]}预警')
                msg_list.append(f"另外{','.join(alarm_brief)}还没有解除")

            if alarm_list[group_id]:                                          # 最后根据是否仍有预警存在确定结束语
                msg_list.append("主人出门的话，要注意安全喔！")    
            else:
                msg_list.append("滴滴！所有天气预警已解除，天气恢复正常啦~")
            await sending_message(msg_list, group_id)
        # 记录本次预警信息
    alarm_last_list = alarm_list

    with open(Path()/"data"/"weather"/"alarm.json", "w", encoding="utf-8") as f:
        f.write(json.dumps({"time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "last_alarm": alarm_last_list}, indent =2, separators=(",", ": ")))

location_id_dict = {}
async def get_location_id(location: str) -> str:
    global location_id_dict
    request_list = ("城市搜索",)
    result = get_api(request_list, location)
    if result[0]["code"] == "200":                      # 请求成功
        location_id_list = result[0]["location"]        # 提取location字段
        if len(location_id_list) == 0:
            return "NoResult"
        elif len(location_id_list) == 1:                # 有且仅有一个结果时直接返回对应id
            location_id_list = []
            return result[0]["location"][0]["id"]
        else:
            adm2_set = set()                            # 当有多个结果时，对二级行政区域进行判断
            for location in location_id_list:
                adm2_set.add(location["adm2"])
            if len(adm2_set) == 1:                      # 如果只有一个，一般情况为下含子级行政区域，直接返回第一个结果
                return result[0]["location"][0]["id"]
            else:                                       # 如果有多个，需要用户进行选择判断
                for adm2 in adm2_set:
                    for location in location_id_list:
                        if location["adm2"] == adm2:
                            location_id_dict[adm2] = (location["name"], location["id"])
                            break
                return "MultiChoice"
    else:                                               # 请求失败
        return "NoResult"

adm2_cache = []
def get_location_id_dict_plain_text(location_id_dict: dict):
    global adm2_cache
    plain_text_list = []
    adm2_cache = []
    for adm2 in location_id_dict.keys():
        plain_text_list.append(f"{len(adm2_cache)+1}: {adm2}")
        adm2_cache.append(adm2)
    return "\n".join(plain_text_list)

weather_cmd = on_command("weather", aliases={"天气"})

@weather_cmd.handle()
async def handle_first_receive(matcher: Matcher, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    # args顺序： 预报/实时 + 城市名
    if args:
        matcher.set_arg("mode", args[0])
        if len(args)>1:
            matcher.set_arg("location", args[1])

@weather_cmd.got("mode", prompt = "请选择你想获得的天气信息:\n 1: (天气)预报\n 2: 实时(天气)\n 0: all(预报+实时)")
@weather_cmd.got("location", prompt= "请输入你想了解的城市")
async def handling(matcher: Matcher, mode: str = ArgStr("mode"), location: str = ArgStr("location")):
    global location_id_dict
    if (mode in ["停止", "break", "退出"]) or (location in ["停止", "break", "退出"]):          # break判断
        await weather_cmd.finish("已结束当前天气进程")
    if location_id_dict:
        if (location in [str(_) for _ in range(1, len(location_id_dict)+1)]) or (location in location_id_dict.keys()):
            if location.isdigit():
                location = adm2_cache[int(location)-1]
            location_id = location_id_dict[location][1]
            location = location_id_dict[location][0]
            location_id_dict = {}
        else:
            await weather_cmd.reject_arg("location", "呜呜呜轻雪酱听不懂呢...请主人输入上面列表中目标城市所属二级行政区划名称或其序号")
    else:
        id_pattern = "^\d{9}$"
        if not re.match(id_pattern, location):
            location_id = await get_location_id(location)
            if location_id == "NoResult":
                await weather_cmd.reject_arg("location", "未检索到对应城市名/网络请求异常，请检查拼写后重新输入，或稍后再进行尝试")
            elif location_id == "MultiChoice":
                msg = f'当前搜索到{len(location_id_dict)}个结果，请选择{location}所属的二级行政区划\n' + get_location_id_dict_plain_text(location_id_dict)
                await weather_cmd.reject_arg("location", msg)

    if mode not in ["1","预报","天气预报","2","实时","实时天气","0","all"]:
        await weather_cmd.reject_arg("mode", "请求天气信息类型错误！请输入1（天气预报），2（实时天气），或0（天气预报+实时天气）中的一个")
    else:
        msg_list = []
        if mode in ["1","预报","天气预报","0","all"]:
            request_list = ("三日天气预报", "逐小时预报")
            result = get_api(request_list, location_id)
            weather_tommorow_Day = result[0]['daily'][1]['textDay']     # 次日白天天气
            weather_tommorow_Night = result[0]['daily'][1]['textNight'] # 次日晚上天气
            temp_Max_tommorow = result[0]['daily'][1]['tempMax']        # 次日最高气温
            temp_Min_tommorow = result[0]['daily'][1]['tempMin']        # 次日最低气温
            wind_tommorow = result[0]['daily'][1]['windScaleDay']       # 次日风力等级
            # 结果格式化
            if weather_tommorow_Day == weather_tommorow_Night:
                weather_report = f'{today+timedelta(days=1)}\n{location}天气：{weather_tommorow_Day}  ({temp_Min_tommorow}℃~{temp_Max_tommorow}℃)\n风力等级：{wind_tommorow}级'
            else:
                weather_report = f'{today+timedelta(days=1)}\n{location}天气：{weather_tommorow_Day}转{weather_tommorow_Night}  ({temp_Min_tommorow}℃~{temp_Max_tommorow}℃)\n风力等级：{wind_tommorow}级'
            # 封装消息I（明日天气预报）
            msg_list.append(weather_report)

        if mode in ["2","实时","实时天气","0","all"]:
            request_list = ("实时天气预报", "实时空气质量")
            result = get_api(request_list, location_id)
            nowTime = result[0]["now"]["obsTime"].split("T")[1][:5]
            nowTemp = result[0]["now"]["temp"]
            feelTemp = result[0]["now"]["feelsLike"]
            now_weather = result[0]["now"]["text"]
            if int(feelTemp) < 10:
                feel_text = "外面好像很冷呢，主人记得穿得暖和一点再出门哦~"
            elif (16 < int(feelTemp) < 24) and (now_weather in ["多云","晴"]):
                feel_text = "外面气温正好，主人和轻雪酱一起出门活动活动身体吧~"
            elif int(feelTemp) > 30:
                feel_text = "好热...轻雪酱感觉自己要融化了...主人也要注意防暑补充水分哦。"
            else:
                feel_text = ""
            now_wind = (result[0]["now"]["windDir"], result[0]["now"]["windScale"])
            now_vis = result[0]["now"]["vis"]
            now_aqi = result[1]["now"]["aqi"]
            now_aqi_cate = result[1]["now"]["category"]
            now_primary_pollution = result[1]["now"]["primary"]
            now_pp_text = "。" if now_primary_pollution == "NA" else f"，主要空气污染物为{now_primary_pollution}，浓度为{result[1]['now'][now_primary_pollution.replace('.','p').lower()]}。主人出门要注意防护哦~"
            now_report = f"现在轻雪酱{nowTime}观测到{location}的实时气温是{nowTemp}℃，体感气温为{feelTemp}℃。{feel_text}空气质量指数为{now_aqi}，等级为{now_aqi_cate}{now_pp_text}"
            msg_list.append(now_report)
        await sending_message(msg_list)

asyncio.run(weather_schedule())           # 启动时更新当日配置
