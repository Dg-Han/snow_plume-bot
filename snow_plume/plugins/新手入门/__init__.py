from nonebot import on_command
from nonebot.rule import to_me
from nonebot import rule
from nonebot.matcher import Matcher
from nonebot.adapters import Event,Message
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.params import Depends
from nonebot.params import Arg, CommandArg, ArgPlainText



comm = on_command("test")

async def depend(args: Message = CommandArg()):
    args = args.extract_plain_text()
    print(args)
    if 'add' in args:
        return 1
    elif 'delete' in args:
        return 'abc'
    return None


@comm.handle()
async def add(matcher: Matcher, args: Message = CommandArg()):
    pass

@comm.got('add_city',prompt="请输入要增加的城市")
async def handle1(city_name:str = ArgPlainText("add_city"),x:int = Depends(depend)):
    await comm.finish(f'已添加城市{city_name}')


@comm.got('delete_city',prompt="请输入要删除的城市")
async def handle1(city_name:str = ArgPlainText("delete_city"),x:str = Depends(depend)):
    await comm.finish(f'已删除城市{city_name}')




# weather = on_command("weather_noob", rule=to_me(), aliases={"新手入门_天气", "新手入门_天气预报"}, priority=5)


# @weather.handle()
# async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()):
#     plain_text = args.extract_plain_text()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
#     if plain_text:
#         matcher.set_arg("city", args)  # 如果用户发送了参数则直接赋值


# @weather.got("city", prompt="你想查询哪个城市的天气呢？")
# async def handle_city(city: Message = Arg(), city_name: str = ArgPlainText("city")):
#     if city_name not in ["北京", "上海"]:  # 如果参数不符合要求，则提示用户重新输入
#         # 可以使用平台的 Message 类直接构造模板消息
#         await weather.reject(city.template("你想查询的城市 {city} 暂不支持，请重新输入！"))

#     city_weather = await get_weather(city_name)
#     await weather.finish(city_weather)


# # 在这里编写获取天气信息的函数
# async def get_weather(city: str) -> str:
#     return f"{city}的天气是..."