# 定义事件响应器
from nonebot import on_command

# 添加处理依赖
from nonebot.params import CommandArg, ArgStr
from nonebot.matcher import Matcher
from nonebot.adapters import Message

# 添加功能所需模块
import re
import gacha_exp_calc as gacha
from gacha_exp_calc.gacha_func import input2nlist

__plugin_des__ = "简单的抽卡期望计算"
__plugin_cmd__ = "[抽卡/gacha] [卡池类型] [抽数] [期望结果]"
__plugin_version__ = "0.1.0rc1"
__plugin_author__ = "Dg_Han"

gacha_cmd = on_command("gacha", aliases={"抽卡"})

@gacha_cmd.handle()
async def handle_first_receive(matcher: Matcher, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    #args顺序: 卡池类型 + 抽数 + 期望
    if args:
        matcher.set_arg("mode", args[0])
        if len(args)>1:
            matcher.set_arg("n", args[1])
        if len(args)>2:
            matcher.set_arg("e", args[2])

@gacha_cmd.got("mode", prompt="请选择卡池类型: \n1: 原神\n2: 明日方舟(单up池)\n3: 明日方舟(双up池)\n0: DIY卡池参数")
@gacha_cmd.got("n", prompt="请输入准备的抽数：")
@gacha_cmd.got("e", prompt="请输入期望抽到up角色的数量（多up请以英文逗号分隔）：")
async def handling(mode: str=ArgStr("mode"), n: str=ArgStr("n"), e: str=ArgStr("e")):
    if mode == "自定义" or mode == "0":
        await gacha_cmd.reject_arg("mode","请输入自定义卡池参数，输入格式为“pool 最高稀有度出率 up出率占比 up个数 触发保底抽数 保底抽数 大保底信息”：")
    if mode == "原神" or mode == "1":
        pool = gacha.step(0.006,0.5,1,73,90,1)
    elif mode == "明日方舟单up" or mode == "2":
        pool = gacha.step(0.02,0.5,1,50,0.02,0)
    elif mode == "明日方舟双up" or mode == "3":
        pool = gacha.step(0.02,0.7,2,50,99,0)
    else:
        #diy_pattern: 关键词 + 最高稀有度出率 + up出率占比 + up个数 + 触发保底抽数 + 保底抽数 + 大保底信息
        pool_diy_pattern = r"^(?:pool)\s(0?\.\d+|[01]\.?0*|100\%|\d{0,2}\.\d*\%|\d{0,2}\%)\s(0?\.\d+|[01]\.?0*|100\%|\d{0,2}\.\d*\%|\d{0,2}\%)\s([1-9]\d*)\s([1-9]\d*)\s([1-9]\d*)\s(\d+)$"
        '''
        概率正则表达式: (0?\.\d+|[01]\.?0*|100\%|\d{0,2}\.\d*\%|\d{0,2}\%)
        正整数正则表达式： ([1-9]\d*)
        '''
        checker = re.match(pool_diy_pattern, mode)
        if checker:
            pool = gacha.step(*[eval(_) for _ in mode.strip().split()[1:]])
        else:
            await gacha_cmd.reject_arg("mode","非法卡池类型！请选择上面列表中已有的卡池类型，或按照“pool 最高稀有度出率 up出率占比 up个数 触发保底抽数 保底抽数 大保底信息”的格式输入自定义卡池信息。")

    try:
        n = eval(n)
    except:
        await gacha_cmd.reject_arg("n","抽数格式错误！请输入正整数。")

    try:
        e = input2nlist(e)
        if len(e)!= pool.ups:
            await gacha_cmd.reject_arg("e", "期望up角色数量错误！请输入与卡池up角色个数相等数量的正整数。")
    except:
        await gacha_cmd.reject_arg("e","期望结果输入错误！请输入以英文逗号为分隔的正整数。")
    
    result = await gacha_calc(pool, n, e)
    await gacha_cmd.finish(result)

async def gacha_calc(pool: gacha.step, n: int, e: list):
    if n>1999:
        return "计算量太大，轻雪酱算不过来了呜呜呜..."
    elif n>300:
        await gacha_cmd.send("由于抽数较多，计算消耗较多时间，请耐心等待...")

    if max(e)>10:
        return "多余的抽卡资源可以给有需要的人"
    else:
        result = pool.calc(n,e) if len(e)==1 else pool.smlt(n,e,times=30000)
        return f"{n}抽达到期望结果{e}的概率是{result:.1%}"
