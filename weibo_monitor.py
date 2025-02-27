import requests
import json
import time
import os

USER_ID = ""  # 目标用户 ID
WECHAT_WEBHOOK_URL = "" # Wechat bot hook
BASE_URL = "https://m.weibo.cn/api/container/getIndex"
DATA_FILE = "weibo_history.json"  # 存储微博历史的文件
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Referer": f"https://m.weibo.cn/u/{USER_ID}"
}

def get_weibo_containerid():
    """ 获取微博的 containerid """
    url = f"{BASE_URL}?type=uid&value={USER_ID}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    if "data" in data and "tabsInfo" in data["data"]:
        for tab in data["data"]["tabsInfo"]["tabs"]:
            if tab.get("tab_type") == "weibo":
                return tab["containerid"]
    return None

def send_to_wechat(weibo_data):
    """ 发送新微博到微信机器人 """
    text = weibo_data["text"]  # 微博内容
    url = f"https://m.weibo.cn/status/{weibo_data['id']}"  # 微博链接
    username = weibo_data["user"]["screen_name"]  # 用户昵称

    message = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"**{username} 发布了新微博**\n\n{text}\n\n[点击查看微博]({url})"
        }
    }

    response = requests.post(WECHAT_WEBHOOK_URL, json=message)
    if response.status_code == 200:
        print("微信机器人推送成功！")
    else:
        print("微信推送失败，状态码:", response.status_code, response.text)

def get_latest_weibo():
    """ 获取用户最新的一条微博 """
    containerid = get_weibo_containerid()
    if not containerid:
        print("未找到 containerid，无法获取微博")
        return None

    url = f"{BASE_URL}?type=uid&value={USER_ID}&containerid={containerid}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    if "data" in data and "cards" in data["data"]:
        for card in data["data"]["cards"]:
            if card.get("card_type") == 9:  # 确保是微博内容
                return card["mblog"]
    print("未找到最新微博")
    return None

def load_saved_weibos():
    """ 读取已保存的微博数据 """
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_new_weibo(weibo_data):
    """ 追加新微博到本地文件 """
    weibos = load_saved_weibos()
    
    # 检查是否已有该微博
    if any(w["id"] == weibo_data["id"] for w in weibos):
        print("没有新微博，跳过保存")
        return False

    # 追加新微博
    weibos.insert(0, weibo_data)  # 新微博放在最前面
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(weibos, f, ensure_ascii=False, indent=4)
    
    print(f"发现新微博！微博 ID: {weibo_data['id']} \n 内容：{weibo_data['text']} \n 包含 {weibo_data['pic_num']}张图片 ")
    send_to_wechat(weibo_data)
    return True

def monitor_weibo():
    """ 持续监控微博，每 60 秒检查一次 """
    print("开始监控微博...")
    while True:
        latest_weibo = get_latest_weibo()
        if latest_weibo:
            save_new_weibo(latest_weibo)
        time.sleep(60)  # 每 60 秒检查一次

# 启动微博监控
monitor_weibo()
