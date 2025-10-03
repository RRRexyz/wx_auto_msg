import httpx
import json
from apscheduler.schedulers.blocking import BlockingScheduler
import time
import jwt
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 从环境变量获取和风天气相关配置项
api_host = os.getenv("API_HOST")
private_key = os.getenv("QWEATHER_PRIVATE_KEY")
qweather_sub = os.getenv("QWEATHER_SUB")
qweather_kid = os.getenv("QWEATHER_KID")
qweather_location = os.getenv("QWEATHER_LOCATION")

# 企业微信机器人配置
webhook_url = os.getenv("WECHAT_WEBHOOK_URL")

def get_payload():
    """生成JWT payload"""
    return {
        'iat': int(time.time()) - 30,
        'exp': int(time.time()) + 900,
        'sub': qweather_sub
    }

def get_headers():
    """生成JWT headers"""
    return {
        'kid': qweather_kid
    }

def send_wecom_message(content, msg_type="text"):
    """发送企业微信机器人消息"""
    headers = {"Content-Type": "application/json"}
    
    if msg_type == "text":
        payload = {
            "msgtype": "text",
            "text": {"content": content}
        }
    elif msg_type == "markdown":
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": content}
        }
    
    try:
        # response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
        response = httpx.post(webhook_url, headers=headers, data=json.dumps(payload))
        return response.json().get("errcode") == 0
    except Exception as e:
        print(f"企业微信推送失败: {str(e)}")
        return False

def daily_weather_report():
    """通过和风天气API获取未来3天天气预报并发送"""
    # Generate JWT
    encoded_jwt = jwt.encode(get_payload(), private_key, algorithm='EdDSA', headers = get_headers())
    
    weather = httpx.get(
        f"https://{api_host}/v7/weather/3d?location={qweather_location}&days=3",
        headers={"Authorization": f"Bearer {encoded_jwt}"}
    )

    today = time.strftime("%Y-%m-%d", time.localtime())
    tomorrow = (time.strftime("%Y-%m-%d", time.localtime(time.time() + 24 * 3600)))
    today_weather = dict()
    tomorrow_weather = dict()
    after_weather = dict()

    for item in weather.json()["daily"]:
        if item["fxDate"] == today:
            today_weather = {
                "日期": item["fxDate"],
                "天气": f"{item['textDay']}转{item['textNight']}" if item["textDay"]!= item["textNight"] else item["textDay"],
                "气温": f"{item['tempMin']}~{item['tempMax']}℃"
            }
        elif item["fxDate"] == tomorrow:
            tomorrow_weather = {
                "日期": item["fxDate"],
                "天气": f"{item['textDay']}转{item['textNight']}" if item["textDay"]!= item["textNight"] else item["textDay"],
                "气温": f"{item['tempMin']}~{item['tempMax']}℃"
            }
        else:
            after_weather = {
                "日期": item["fxDate"],
                "天气": f"{item['textDay']}转{item['textNight']}" if item["textDay"]!= item["textNight"] else item["textDay"],
                "气温": f"{item['tempMin']}~{item['tempMax']}℃"
            }
    markdown_content = f"**📊 未来三天天气**" + \
        f"\n今天：\n- 日期：{today_weather['日期']}\n- 天气：{today_weather['天气']}\n- 气温：{today_weather['气温']}" + \
        f"\n\n明天：\n- 日期：{tomorrow_weather['日期']}\n- 天气：{tomorrow_weather['天气']}\n- 气温：{tomorrow_weather['气温']}" + \
        f"\n\n后天：\n- 日期：{after_weather['日期']}\n- 天气：{after_weather['天气']}\n- 气温：{after_weather['气温']}"
    send_wecom_message(markdown_content, "markdown")


def now_weather_report():
    """通过和风天气API获取实时天气并发送"""
    # Generate JWT
    encoded_jwt = jwt.encode(get_payload(), private_key, algorithm='EdDSA', headers = get_headers())
    weather = httpx.get(
        f"https://{api_host}/v7/weather/now?location={qweather_location}",
        headers={"Authorization": f"Bearer {encoded_jwt}"}
    )

    now_weather = {
        "时间": time.strftime("%Y-%m-%d %H:%M", time.localtime()),
        "天气": weather.json()["now"]["text"],
        "气温": weather.json()["now"]["temp"] + "℃ "
    }
    
    # 构建消息内容
    markdown_content = f"🌤️ **实时天气**\n\n" \
            f"📅 时间：{now_weather['时间']}\n" \
            f"☁️ 天气：{now_weather['天气']}\n" \
            f"🌡️ 气温：{now_weather['气温']}"
    send_wecom_message(markdown_content, "markdown")


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    
    # 每天7：30发送未来3天天气预报
    scheduler.add_job(daily_weather_report, 'cron', hour=7, minute=30)
    
    # 每天19:30发送未来3天天气预报
    scheduler.add_job(daily_weather_report, 'cron', hour=19, minute=30)
    
    # 每个整点发送实时天气
    scheduler.add_job(now_weather_report, 'cron', minute=0)
    
    # 测试消息
    send_wecom_message("定时任务服务已启动 ✅", "text")
    
    print("🟢 企业微信定时推送服务运行中...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("服务已停止")