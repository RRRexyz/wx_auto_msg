import httpx
import time
from dotenv import load_dotenv
import os
import jwt

# 加载环境变量
load_dotenv()

api_host = os.getenv("API_HOST")
private_key = os.getenv("QWEATHER_PRIVATE_KEY")
qweather_sub = os.getenv("QWEATHER_SUB")
qweather_kid = os.getenv("QWEATHER_KID")

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

def get_location_id(location_name):
    """通过城市名称获取城市ID"""
    # Generate JWT token
    token = jwt.encode(get_payload(), private_key, algorithm='EdDSA', headers=get_headers())
    response = httpx.get(
        f"https://{api_host}/geo/v2/city/lookup?location={location_name}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()["location"][0]["id"]


if __name__ == '__main__':
    location_id =get_location_id("济南")
    print(location_id)