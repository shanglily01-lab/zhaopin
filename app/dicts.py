"""配置/字典映射

数据库中没有独立的字典表，部分字段以 int 编码引用了"配置表"。
根据采样数据 + 字段注释推断含义如下：

t_user.iscom: 0=个人 / 1=企业
t_company.wrks (公司人数), t_resume.edu / exp (学历 / 经验) 等都以 1000+ 为档位。
t_degree.isremote / isall, t_resume.wtype 等 0/1/2 是远程/全职/兼职/不限。
chains 字段 1~10 是主流区块链类型。
"""
from __future__ import annotations

# 公司规模
WRKS = {
    0: "未公开",
    1001: "10 人以下",
    1002: "10-50 人",
    1003: "50-200 人",
    1004: "200-500 人",
    1005: "500-1000 人",
    1006: "1000 人以上",
}

# 公司类型
CTYPE = {
    0: "未分类",
    1: "交易所",
    2: "钱包",
    3: "公链",
    4: "DeFi",
    5: "媒体/资讯",
    6: "投资机构",
    7: "GameFi/NFT",
}

# 主要区块链
CHAINS = {
    "1": "Bitcoin",
    "2": "Ethereum",
    "3": "BNB Chain",
    "4": "Solana",
    "5": "Polygon",
    "6": "TRON",
    "7": "Arbitrum",
    "8": "Optimism",
    "9": "TON",
    "10": "其他",
}

# 学历
EDU = {
    0: "未填",
    1000: "高中",
    1001: "大专",
    1002: "本科",
    1003: "硕士",
    1004: "博士",
}

# 工作经验
EXP = {
    0: "未填",
    1000: "1-3 年",
    1001: "3-5 年",
    1002: "5-10 年",
    1003: "10 年以上",
    1004: "应届/实习",
}

# 是否远程
REMOTE = {0: "线下", 1: "远程", 2: "线下/远程均可"}

# 是否全职
ALLTIME = {0: "兼职", 1: "全职", 2: "实习", 3: "外包"}

# 简历工作类型（resume.wtype）
WTYPE = {0: "线下", 1: "远程", 2: "不限"}

# 是否英语
ISEN = {0: "中文为主", 1: "可英语沟通"}

# 简历可见
ISVIS = {0: "隐藏", 1: "公开"}

# 上下架
ISOPERA = {0: "下架", 1: "上架"}


def label(d: dict, key, default: str = "-") -> str:
    """安全的字典查找。"""
    if key is None:
        return default
    if isinstance(key, str) and key.isdigit():
        key_int = int(key)
        if key_int in d:
            return d[key_int]
    if key in d:
        return d[key]
    return default


def chain_labels(raw: str | None) -> list[str]:
    """chains 字段可能是 "2" 或 "2,3" 这种逗号分隔。"""
    if not raw:
        return []
    out = []
    for part in str(raw).replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        out.append(CHAINS.get(part, part))
    return out


def parse_skills(raw: str | None) -> list[str]:
    """技能栈字段：可能空格、逗号、顿号、中文逗号、分号、斜杠分隔。"""
    if not raw:
        return []
    text = raw
    for sep in ["、", ",", "，", ";", "；", "/", "|"]:
        text = text.replace(sep, " ")
    return [p.strip() for p in text.split() if p.strip()]
