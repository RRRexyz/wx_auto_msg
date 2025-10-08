import httpx
import json
from apscheduler.schedulers.blocking import BlockingScheduler
import time
import jwt
from dotenv import load_dotenv
import os
import sys

# 加载环境变量
load_dotenv()

# 从环境变量获取和风天气相关配置项
api_host = os.getenv("API_HOST")
private_key = os.getenv("QWEATHER_PRIVATE_KEY")
qweather_sub = os.getenv("QWEATHER_SUB")
qweather_kid = os.getenv("QWEATHER_KID")

# 企业微信机器人配置
webhook_url = os.getenv("WECHAT_WEBHOOK_URL")

# 检查必需的环境变量
def check_environment_variables():
    """检查必需的环境变量是否存在"""
    required_vars = {
        "API_HOST": api_host,
        "QWEATHER_PRIVATE_KEY": private_key,
        "QWEATHER_SUB": qweather_sub,
        "QWEATHER_KID": qweather_kid,
        "WECHAT_WEBHOOK_URL": webhook_url
    }
    
    missing_vars = [var_name for var_name, value in required_vars.items() if value is None]
    
    if missing_vars:
        print(f"错误：缺少必需的环境变量: {', '.join(missing_vars)}")
        sys.exit(1)

def get_payload() -> dict:
    """生成JWT payload"""
    assert qweather_sub is not None, "QWEATHER_SUB 不能为 None"
    return {
        'iat': int(time.time()) - 30,
        'exp': int(time.time()) + 900,
        'sub': qweather_sub
    }


def get_headers() -> dict:
    """生成JWT headers"""
    assert qweather_kid is not None, "QWEATHER_KID 不能为 None"
    return {
        'kid': qweather_kid
    }


def get_location_id(location_name: str) -> str:
    """通过城市名称获取城市ID"""
    # Generate JWT token
    assert private_key is not None, "QWEATHER_PRIVATE_KEY 不能为 None"
    assert api_host is not None, "API_HOST 不能为 None"
    token = jwt.encode(get_payload(), private_key, algorithm='EdDSA', headers=get_headers())
    response = httpx.get(
        f"https://{api_host}/geo/v2/city/lookup?location={location_name}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()["location"][0]["id"]


def send_wecom_message(content: str, msg_type: str = "text") -> bool:
    """发送企业微信机器人消息"""
    assert webhook_url is not None, "WECHAT_WEBHOOK_URL 不能为 None"
    headers = {"Content-Type": "application/json"}
    
    payload: dict = {}
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
    else:
        print(f"不支持的消息类型: {msg_type}")
        return False
    
    try:
        response = httpx.post(webhook_url, headers=headers, json=payload)
        return response.json().get("errcode") == 0
    except Exception as e:
        print(f"企业微信推送失败: {str(e)}")
        return False


def daily_weather_report(location_name: str, location_id: str) -> None:
    """通过和风天气API获取未来3天天气预报并发送"""
    # Generate JWT
    assert private_key is not None, "QWEATHER_PRIVATE_KEY 不能为 None"
    assert api_host is not None, "API_HOST 不能为 None"
    encoded_jwt = jwt.encode(get_payload(), private_key, algorithm='EdDSA', headers = get_headers())
    
    weather = httpx.get(
        f"https://{api_host}/v7/weather/3d?location={location_id}",
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
    markdown_content = f"**📊 {location_name}未来三天天气**" + \
        f"\n今天：\n- 日期：{today_weather['日期']}\n- 天气：{today_weather['天气']}\n- 气温：{today_weather['气温']}" + \
        f"\n\n明天：\n- 日期：{tomorrow_weather['日期']}\n- 天气：{tomorrow_weather['天气']}\n- 气温：{tomorrow_weather['气温']}" + \
        f"\n\n后天：\n- 日期：{after_weather['日期']}\n- 天气：{after_weather['天气']}\n- 气温：{after_weather['气温']}"
    send_wecom_message(markdown_content, "markdown")


def now_weather_report(location_name: str, location_id: str) -> None:
    """通过和风天气API获取实时天气并发送"""
    # Generate JWT
    assert private_key is not None, "QWEATHER_PRIVATE_KEY 不能为 None"
    assert api_host is not None, "API_HOST 不能为 None"
    encoded_jwt = jwt.encode(get_payload(), private_key, algorithm='EdDSA', headers = get_headers())
    weather = httpx.get(
        f"https://{api_host}/v7/weather/now?location={location_id}",
        headers={"Authorization": f"Bearer {encoded_jwt}"}
    )

    now_weather = {
        "时间": time.strftime("%Y-%m-%d %H:%M", time.localtime()),
        "天气": weather.json()["now"]["text"],
        "气温": weather.json()["now"]["temp"] + "℃ "
    }
    
    # 构建消息内容
    markdown_content = f"🌤️ **{location_name}实时天气**\n\n" \
            f"📅 时间：{now_weather['时间']}\n" \
            f"☁️ 天气：{now_weather['天气']}\n" \
            f"🌡️ 气温：{now_weather['气温']}"
    send_wecom_message(markdown_content, "markdown")


if __name__ == "__main__":
    # 检查环境变量
    check_environment_variables()
    
    scheduler = BlockingScheduler()
    
    if len(sys.argv) < 2:
        print("Usage: uv run wx_auto_weather_msg.py 'location_name'")
        sys.exit(1)
    
    location_name = sys.argv[1]
    location_id = get_location_id(location_name)
    
    # 每天7：30发送未来3天天气预报
    scheduler.add_job(daily_weather_report, args=[location_name, location_id], trigger='cron', hour=7, minute=30)
    
    # 每天19:30发送未来3天天气预报
    scheduler.add_job(daily_weather_report, args=[location_name, location_id], trigger='cron', hour=19, minute=30)
    
    # 每个整点发送实时天气
    scheduler.add_job(now_weather_report, args=[location_name, location_id], trigger='cron', minute=0)
    
    # 测试消息
    send_wecom_message("定时任务服务已启动 ✅", "text")
    
    print("🟢 企业微信定时推送服务运行中...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("服务已停止")