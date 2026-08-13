#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小六壬（六壬时课 / 掐指一算）推算脚本
用法：
    python3 calc.py                 # 用当前系统时间自动起卦
    python3 calc.py 2026-08-13 15   # 指定公历日期 + 小时(24小时制)
    python3 calc.py --test          # 运行算法自检
输出：JSON，包含农历、时辰、最终掌诀、断辞与掌诀图。
"""
import json
import math
import sys
from datetime import datetime

# ============ 农历数据表（1900-2100，每项代表一年） ============
# 位16-20:闰月号(0为无闰月)；位0-15:每月大小(1=大30天,0=小29天)，低位对应正月
LUNAR_INFO = [
    0x04bd8,0x04ae0,0x0a570,0x054d5,0x0d260,0x0d950,0x16554,0x056a0,0x09ad0,0x055d2,#1900-1909
    0x04ae0,0x0a5b6,0x0a4d0,0x0d250,0x1d255,0x0b540,0x0d6a0,0x0ada2,0x095b0,0x14977,#1910-1919
    0x04970,0x0a4b0,0x0b4b5,0x06a50,0x06d40,0x1ab54,0x02b60,0x09570,0x052f2,0x04970,#1920-1929
    0x06566,0x0d4a0,0x0ea50,0x06e95,0x05ad0,0x02b60,0x186e3,0x092e0,0x1c8d7,0x0c950,#1930-1939
    0x0d4a0,0x1d8a6,0x0b550,0x056a0,0x1a5b4,0x025d0,0x092d0,0x0d2b2,0x0a950,0x0b557,#1940-1949
    0x06ca0,0x0b550,0x15355,0x04da0,0x0a5b0,0x14573,0x052b0,0x0a9a8,0x0e950,0x06aa0,#1950-1959
    0x0aea6,0x0ab50,0x04b60,0x0aae4,0x0a570,0x05260,0x0f263,0x0d950,0x05b57,0x056a0,#1960-1969
    0x096d0,0x04dd5,0x04ad0,0x0a4d0,0x0d4d4,0x0d250,0x0d558,0x0b540,0x0b6a0,0x195a6,#1970-1979
    0x095b0,0x049b0,0x0a974,0x0a4b0,0x0b27a,0x06a50,0x06d40,0x0af46,0x0ab60,0x09570,#1980-1989
    0x04af5,0x04970,0x064b0,0x074a3,0x0ea50,0x06b58,0x055c0,0x0ab60,0x096d5,0x092e0,#1990-1999
    0x0c960,0x0d954,0x0d4a0,0x0da50,0x07552,0x056a0,0x0abb7,0x025d0,0x092d0,0x0cab5,#2000-2009
    0x0a950,0x0b4a0,0x0baa4,0x0ad50,0x055d9,0x04ba0,0x0a5b0,0x15176,0x052b0,0x0a930,#2010-2019
    0x07954,0x06aa0,0x0ad50,0x05b52,0x04b60,0x0a6e6,0x0a4e0,0x0d260,0x0ea65,0x0d530,#2020-2029
    0x05aa0,0x076a3,0x096d0,0x04afb,0x04ad0,0x0a4d0,0x1d0b6,0x0d250,0x0d520,0x0dd45,#2030-2039
    0x0b5a0,0x056d0,0x055b2,0x049b0,0x0a577,0x0a4b0,0x0aa50,0x1b255,0x06d20,0x0ada0,#2040-2049
    0x14b63,0x09370,0x049f8,0x04970,0x064b0,0x168a6,0x0ea50,0x06b20,0x1a6c4,0x0aae0,#2050-2059
    0x092e0,0x0d2e3,0x0c960,0x0d557,0x0d4a0,0x0da50,0x05d55,0x056a0,0x0a6d0,0x055d4,#2060-2069
    0x052d0,0x0a9b8,0x0a950,0x0b4a0,0x0b6a6,0x0ad50,0x055a0,0x0aba4,0x0a5b0,0x052b0,#2070-2079
    0x0b273,0x06930,0x07337,0x06aa0,0x0ad50,0x14b55,0x04b60,0x0a570,0x054e4,0x0d160,#2080-2089
    0x0e968,0x0d520,0x0daa0,0x16aa6,0x056d0,0x04ae0,0x0a9d4,0x0a2d0,0x0d150,0x0f252,#2090-2099
    0x0d520,#2100
]
LUNAR_BASE_YEAR = 1900
# 1900-01-31 为农历 1900 年正月初一
SOLAR_BASE = datetime(1900, 1, 31)

TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SHENG_XIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
LUNAR_MONTH = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]
LUNAR_DAY = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
             "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
             "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"]

# 十二时辰（每 2 小时一个时辰），索引=时辰序号-1
SHICHEN = ["子时(23-1)", "丑时(1-3)", "寅时(3-5)", "卯时(5-7)", "辰时(7-9)", "巳时(9-11)",
           "午时(11-13)", "未时(13-15)", "申时(15-17)", "酉时(17-19)", "戌时(19-21)", "亥时(21-23)"]

# 六宫位（按掐指顺数顺序：大安→留连→速喜→赤口→小吉→空亡）
PALACES = ["大安", "留连", "速喜", "赤口", "小吉", "空亡"]  # 索引0-5，实际位序1-6


def leap_month(info):
    """该农历年闰几月，0 表示无闰月（低4位）"""
    return info & 0xf


def leap_days(info):
    """闰月天数，bit16=1 为大月30天，否则29天"""
    return 30 if (info & 0x10000) else 29


def lunar_year_days(info):
    """农历年总天数 = 12个普通月天数 + 闰月天数(若有)"""
    total = 0
    for m in range(1, 13):
        total += 30 if (info & (0x10000 >> m)) else 29
    if leap_month(info) > 0:
        total += leap_days(info)
    return total


def solar_to_lunar(year, month, day):
    """公历转农历，返回 (农历年, 农历月, 农历日, 是否闰月, 干支年, 生肖)"""
    if not (1900 <= year <= 2100):
        raise ValueError("年份超出支持范围(1900-2100)")
    offset = (datetime(year, month, day) - SOLAR_BASE).days

    # 1) 定位农历年
    days_before_year = 0
    lunar_year = LUNAR_BASE_YEAR
    for i in range(LUNAR_BASE_YEAR, 2101):
        yd = lunar_year_days(LUNAR_INFO[i - LUNAR_BASE_YEAR])
        if offset < days_before_year + yd:
            lunar_year = i
            break
        days_before_year += yd

    info = LUNAR_INFO[lunar_year - LUNAR_BASE_YEAR]
    leap = leap_month(info)
    d_in_year = offset - days_before_year  # 该农历年内第几天(0起)

    # 2) 生成该年全部月槽：正常月1..12；闰月插在编号leap之后（编号相同，索引靠后即为闰）
    months = []
    for m in range(1, 13):
        months.append((m, 30 if (info & (0x10000 >> m)) else 29))
        if m == leap and leap > 0:
            months.append((m, leap_days(info)))

    # 3) 定位落在哪个月槽
    lunar_month = months[0][0]
    lunar_day = 1
    is_leap = False
    acc = 0
    for idx, (mnum, mdays) in enumerate(months):
        if d_in_year < acc + mdays:
            is_leap = (idx > 0 and months[idx - 1][0] == mnum)  # 与前一槽同编号则为闰月
            lunar_month = mnum
            lunar_day = d_in_year - acc + 1
            break
        acc += mdays

    # 4) 干支年与生肖（按农历年号）
    ganzhi_idx = (lunar_year - 4) % 60
    return (lunar_year, lunar_month, lunar_day, is_leap,
            TIAN_GAN[ganzhi_idx % 10] + DI_ZHI[ganzhi_idx % 12], SHENG_XIAO[ganzhi_idx % 12])


def hour_to_shichen(hour):
    """24小时制转时辰序号(1-12)"""
    # 子时从 23 点开始
    return ((hour + 1) // 2) % 12 + 1


# ============ 小六壬核心推算 ============
def calc_liuren(lunar_month, lunar_day, shichen_no):
    """月日时三数推算，返回 (最终宫位序号1-6, 每步落宫明细)"""
    steps = {}
    # 1. 起月：从大安(位1)起初月，顺数到所求月
    pos_m = ((1 - 1 + (lunar_month - 1)) % 6) + 1
    steps["月"] = {"数": lunar_month, "落宫": PALACES[pos_m - 1]}
    # 2. 起日：从月落宫起初一，顺数到所求日
    pos_d = ((pos_m - 1 + (lunar_day - 1)) % 6) + 1
    steps["日"] = {"数": lunar_day, "落宫": PALACES[pos_d - 1]}
    # 3. 起时：从日落宫起子时，顺数到所求时辰
    pos_s = ((pos_d - 1 + (shichen_no - 1)) % 6) + 1
    steps["时"] = {"数": shichen_no, "落宫": PALACES[pos_s - 1]}
    return pos_s, steps


# ============ 断辞库 ============
JUDGMENTS = {
    "大安": {
        "吉凶": "大吉", "五行": "木", "神煞": "青龙", "方位": "东方", "颜色": "青",
        "数字": [1, 5, 7],
        "总断": "大安事事昌，求谋在东方，失物不远去，宅舍保安康。行人身未动，病者主无妨。将军回田野，仔细更推详。",
        "事业": "做事安稳顺遂，宜守不宜急，循序渐进自有收获，谋事可成但需耐心。",
        "感情": "感情平稳和谐，关系安定，宜多沟通增进，婚姻可期。",
        "财运": "财运平稳，无大进大出，守成有得，不宜投机。",
        "健康": "身体康健，小病无妨，注意作息即可。",
        "问事": "所问之事顺遂，结局安稳，不必过虑。",
    },
    "留连": {
        "吉凶": "中平偏滞", "五行": "水", "神煞": "玄武", "方位": "北方", "颜色": "黑",
        "数字": [2, 8, 10],
        "总断": "留连事难成，求谋日未明。官事只宜缓，去者未回程。失物南方见，急讨方趁心。更须防口舌，人口且平平。",
        "事业": "诸事拖延难成，宜缓不宜急，谋事多反复，需耐心等待时机。",
        "感情": "感情粘滞不定，易生误会，宜主动沟通，切忌猜疑拖延。",
        "财运": "财运迟滞，求财难成，需防破财，不宜贸然投资。",
        "健康": "小病缠绵，需及时就医，注意调养。",
        "问事": "所问之事多阻滞，欲速则不达，宜静观其变。",
    },
    "速喜": {
        "吉凶": "吉", "五行": "火", "神煞": "朱雀", "方位": "南方", "颜色": "红",
        "数字": [3, 6, 9],
        "总断": "速喜喜来临，求财向南行。失物申未午，逢人路上寻。官事有福德，病者无祸侵。田宅六畜吉，行人有信音。",
        "事业": "喜事将至，谋事可速成，宜把握时机积极进取。",
        "感情": "喜从天降，感情升温，进展迅速，宜趁热打铁。",
        "财运": "财运亨通，求财顺利，偏财亦有喜。",
        "健康": "无大碍，病去如抽丝，将很快康复。",
        "问事": "所问之事有喜讯，快速见成，大好之兆。",
    },
    "赤口": {
        "吉凶": "凶", "五行": "金", "神煞": "白虎", "方位": "西方", "颜色": "白",
        "数字": [4, 7, 10],
        "总断": "赤口主口舌，官非切要防。失物急去寻，行人有惊慌。鸡犬多作怪，病者出西方。更须防咒咀，恐怕染瘟殃。",
        "事业": "多口舌是非，防官非纠纷，宜谨言慎行，退让三分。",
        "感情": "易生口角争执，需忍让克制，谨防关系破裂。",
        "财运": "财运不利，防破财及争执之财，不宜借贷担保。",
        "健康": "须防病灾，遇事及时就医，忌讳讳疾忌医。",
        "问事": "所问之事多是非凶险，宜谨慎应对，缓图化解。",
    },
    "小吉": {
        "吉凶": "大吉", "五行": "水", "神煞": "六合", "方位": "西南", "颜色": "赤",
        "数字": [1, 5, 7],
        "总断": "小吉最吉昌，路上好商量。阳人来报喜，失物在坤方。行人立便至，交关甚是强。凡事皆和合，病者叩穹苍。",
        "事业": "诸事和合顺利，贵人相助，谋事易成，大吉之象。",
        "感情": "感情和美，良缘和合，宜成好事。",
        "财运": "财运旺盛，求财有得，合作生财。",
        "健康": "身体安泰，纵有小恙亦无大碍。",
        "问事": "所问之事和顺吉昌，得贵人扶持，圆满可成。",
    },
    "空亡": {
        "吉凶": "凶", "五行": "土", "神煞": "勾陈", "方位": "中央", "颜色": "黄",
        "数字": [3, 6, 9],
        "总断": "空亡事不长，阴人多乖张。求财无利益，行人有灾殃。失物寻不见，官事主刑伤。病人逢暗鬼，禳解保安康。",
        "事业": "事多空落，劳而无功，宜谨慎行事，莫抱过高期望。",
        "感情": "感情虚无缥缈，难有结果，宜冷静考量勿陷迷局。",
        "财运": "求财无利，防破财落空，不宜投资投机。",
        "健康": "须防隐患暗疾，宜早检查调理。",
        "问事": "所问之事多落空虚妄，结局难料，宜务实看待。",
    },
}

PALACE_POSITION = {
    "大安": "食指根节",
    "留连": "中指根节",
    "速喜": "无名指根节",
    "赤口": "无名指尖节",
    "小吉": "中指指尖节",
    "空亡": "食指指尖节",
}

PALACE_ORDER = {"大安": 1, "留连": 2, "速喜": 3, "赤口": 4, "小吉": 5, "空亡": 6}


def palm_chart(final_palace):
    """生成掌诀图（ASCII，右手掌，标记最终落宫）"""
    mark = lambda name: ("  ★" if name == final_palace else "    ")
    return (
        "         食指          中指          无名指\n"
        "         ▲            ▲            ▲\n"
        "        ┌────────┬────────┬────────┐\n"
        f"  指尖  │ 空亡 {mark('空亡')}│ 小吉 {mark('小吉')}│ 赤口 {mark('赤口')}│\n"
        "        ├────────┼────────┼────────┤\n"
        f"  指根  │ 大安 {mark('大安')}│ 留连 {mark('留连')}│ 速喜 {mark('速喜')}│\n"
        "        └────────┴────────┴────────┘\n"
        "   ★ = 本次所求掌诀"
    )


def build_result(dt):
    """对给定 datetime 计算完整结果并返回 dict"""
    ly, lm, ld, is_leap, ganzhi, shengxiao = solar_to_lunar(dt.year, dt.month, dt.day)
    sc_no = hour_to_shichen(dt.hour)
    final_pos, steps = calc_liuren(lm, ld, sc_no)
    palace = PALACES[final_pos - 1]
    j = JUDGMENTS[palace]
    return {
        "公历": dt.strftime("%Y-%m-%d %H:%M"),
        "农历": f"{ly}年{('闰' if is_leap else '')}{LUNAR_MONTH[lm-1]}月{LUNAR_DAY[ld-1]}（{ganzhi}年·属{shengxiao}）",
        "时辰": SHICHEN[sc_no - 1],
        "起卦": {"月": f"{LUNAR_MONTH[lm-1]}月", "日": LUNAR_DAY[ld-1], "时": f"第{sc_no}个时辰"},
        "推算过程": {k: f"{v['数']} → 落于【{v['落宫']}】" for k, v in steps.items()},
        "结果": {
            "掌诀": palace,
            "位序": PALACE_ORDER[palace],
            "掌诀位置": PALACE_POSITION[palace],
            "吉凶": j["吉凶"], "五行": j["五行"], "神煞": j["神煞"],
            "方位": j["方位"], "颜色": j["颜色"], "主数": j["数字"],
        },
        "断辞": {
            "总断": j["总断"], "事业": j["事业"], "感情": j["感情"],
            "财运": j["财运"], "健康": j["健康"], "问事": j["问事"],
        },
        "掌诀图": palm_chart(palace),
    }


def run_selftest():
    """算法自检：用多个公认春节(正月初一)锚点验证农历转换"""
    anchors = [
        (1990, 1, 27, 1990, 1),   # 1990-01-27 农历正月初一
        (2000, 2, 5, 2000, 1),    # 2000-02-05 农历正月初一
        (2010, 2, 14, 2010, 1),   # 2010-02-14 农历正月初一
        (2024, 2, 10, 2024, 1),   # 2024-02-10 农历正月初一
    ]
    for sy, sm, sd, ly, lm in anchors:
        got = solar_to_lunar(sy, sm, sd)
        assert got[0] == ly and got[1] == lm and got[2] == 1, f"农历锚点失败 {sy}-{sm}-{sd} -> {got}"
    # 时辰边界：23点=子时(序号1)，12点=午时(序号7)
    assert hour_to_shichen(23) == 1
    assert hour_to_shichen(0) == 1
    assert hour_to_shichen(12) == 7
    assert hour_to_shichen(13) == 8
    # 小六壬推算：正月(1)初一(1)子时(1) → 三步都落大安
    pos, steps = calc_liuren(1, 1, 1)
    assert pos == 1 and PALACES[pos - 1] == "大安", "正月正一子时应为大安"
    # 正月(1)初一(1)丑时(2) → 大安→大安→留连
    pos, _ = calc_liuren(1, 1, 2)
    assert pos == 2 and PALACES[pos - 1] == "留连", "丑时应为留连"
    print("✅ 全部自检通过")
    return True


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_selftest()
        return
    if len(sys.argv) >= 3:
        dt = datetime.strptime(sys.argv[1], "%Y-%m-%d")
        hour = int(sys.argv[2])
        if not (0 <= hour <= 23):
            raise ValueError("小时须在0-23")
        dt = dt.replace(hour=hour)
    else:
        dt = datetime.now()
    print(json.dumps(build_result(dt), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
