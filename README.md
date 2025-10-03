# 配置说明

## 环境变量配置
在项目根目录下创建一个`.env`文件，并添加以下内容：
```env
# 和风天气API配置
API_HOST="xxxxxxxxx.re.qweatherapi.com"
QWEATHER_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nxxxxxxxxxxxxxx\n-----END PRIVATE KEY-----"
QWEATHER_SUB="xxxxxxxxxx"
QWEATHER_KID="xxxxxxxxxx"

# 企业微信机器人配置
WECHAT_WEBHOOK_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxxx"
```

## 企业微信消息推送
首先在手机上安装*企业微信*，并登录。

随便创建一个群聊，然后点击群聊右上角的“...”，选择“消息推送”。

在**消息推送**中添加一个自定义消息推送，并保存。此时会获得一个Webhook地址，例如：`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx`。将此地址赋值给`WECHAT_WEBHOOK_URL`变量。

## 和风天气API配置
### 查看API Host
进入控制台的“设置”中，查看`API Host`，例如：`xxxxxxxxx.re.qweatherapi.com`。将API Host赋值给`API_HOST`变量。

### 添加身份认证
打开终端，分别运行以下命令，生成`ed25519`算法的私钥文件和公钥文件。
```bash
openssl genpkey -algorithm ED25519 -out ed25519-private.pem
openssl pkey -pubout -in ed25519-private.pem > ed25519-public.pem
```
将私钥文件中的内容（包含`-----BEGIN PRIVATE KEY-----`和`-----END PRIVATE KEY-----`）赋值给`QWEATHER_PRIVATE_KEY`变量。

### 创建项目并上传凭证
首先进入[和风天气开发服务平台](https://dev.qweather.com/docs/configuration)，点击“项目和凭据”，然后点击“前往控制台-项目管理”，在这里创建一个项目，此时会生成一个项目ID。将项目ID赋值给`QWEATHER_SUB`变量。

在项目管理页面点击“创建凭据”，选择“身份认证”，选择"JSON Web Token"认证方式，将公钥文件中的内容（包含`-----BEGIN PUBLIC KEY-----`和`-----END PUBLIC KEY-----`）添加到“上传公钥”输入框中，然后点击保存。此时会生成一个凭证ID，将凭证ID赋值给`QWEATHER_KID`变量。

## 定时任务配置
打开`wx_auto_weather_msg.py`文件，拉到最下面，找到`scheduler.add_job`方法，按照自己的需求修改定时任务的设置。例如：
```python
scheduler.add_job(daily_weather_report, 'cron', hour=7, minute=30)
```

## 部署
将项目连带`.env`文件上传到服务器，然后运行`wx_auto_weather_msg.py`脚本，带上地名参数，可以用`nohup`命令保活，例如：
```bash
nohup uv run wx_auto_weather_msg.py "济南" &
```

---
完成！