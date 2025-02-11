import os
import requests
import re
import json
import datetime

# 获取打新债数据
def get_bond_calendar():
    # 目标 URL
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "callback": "jQuery1123043452537550202197_1739244859794",
        "sortColumns": "PUBLIC_START_DATE,SECURITY_CODE",
        "sortTypes": "-1,-1",
        "pageSize": "50",
        "pageNumber": "1",
        "reportName": "RPT_BOND_CB_LIST",
        "columns": "ALL",
        "quoteType": "0",
        "source": "WEB",
        "client": "WEB"
    }

    # 发送请求
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, params=params, headers=headers)

    # 去除 JSONP 回调函数，提取 JSON 数据
    json_text = re.search(r'jQuery\d+_\d+\((.*)\)', response.text).group(1)
    data = json.loads(json_text)

    # 提取核心数据
    if "result" in data and "data" in data["result"]:
        bonds = data["result"]["data"]
        for bond in bonds[:5]:  # 仅打印前 5 条
            print(f"名称: {bond['SECURITY_NAME_ABBR']}, 代码: {bond['SECURITY_CODE']}, 申购日期: {bond['PUBLIC_START_DATE']}"
                  f", 信用评级: {bond['RATING']}")

    else:
        print("未找到可转债数据")

    return bonds

def get_today_date():
    return datetime.today().strftime('%Y-%m-%d')
    
# 发送 Server 酱通知
def send_to_wechat(bonds):
    server_key = os.getenv("SERVERCHAN_API_KEY")
    if not server_key:
        print("未设置 Server 酱 SendKey")
        return

    url = f"https://sctapi.ftqq.com/{server_key}.send"

    if not bonds:
        title = "📅 今日无可申购新债"
        content = "今天没有可申购的新债。"
    else:
        title = "📅 今日可申购新债"
        content = "\n".join(
            [f"🔹 **{bond['SECURITY_NAME_ABBR']}**（{bond['SECURITY_CODE']}） - 申购日期: {bond['PUBLIC_START_DATE']}  - 信用评级: {bond['RATING']}"
             for bond in bonds]
        )

    payload = {"title": title, "desp": content}
    response = requests.post(url, data=payload)
    print("推送结果:", response.text)


if __name__ == "__main__":
    today_date = get_today_date()  # 获取今天的日期
    bonds = get_bond_calendar()
    # 筛选出申购日期等于今天的债券
    bonds_to_send = [bond for bond in bonds if bond['PUBLIC_START_DATE'] == today_date]

    if bonds_to_send:
        send_to_wechat(bonds_to_send)  # 发送符合条件的债券推送
    else:
        print(f"今天没有申购的新债 ({today_date})")
