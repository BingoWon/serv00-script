import os
import json
import subprocess
import requests

# 从环境变量中获取密钥
accounts_json = os.getenv('ACCOUNTS_JSON')
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

# 解析 JSON 字符串
servers = json.loads(accounts_json)

# 初始化汇总消息
summary_message = "serv00-vless 当前公共 IP 地址：\n"

# Function to get the public IP address of a server
def get_public_ip(username, password, host, port):
    command = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -p {port} {username}@{host} 'curl -s ifconfig.me'"
    try:
        ip = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).strip().decode('utf-8')
        return ip
    except subprocess.CalledProcessError as e:
        print(f"无法获取 {host} 的公共 IP：{e.output.decode('utf-8')}")
        return None

# 遍历服务器列表并获取公共 IP 地址
for server in servers:
    host = server['host']
    port = server['port']
    username = server['username']
    password = server['password']

    print(f"连接到 {host}...")

    # 获取当前公共 IP 地址
    current_ip = get_public_ip(username, password, host, port)
    if current_ip:
        print(f"{host} 的当前公共 IP 地址是 {current_ip}")
        summary_message += f"\n{host} 的当前公共 IP 地址是：{current_ip}"
    else:
        summary_message += f"\n无法获取 {host} 的当前公共 IP 地址。"

# 发送汇总消息到 Telegram
telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
telegram_payload = {
    "chat_id": telegram_chat_id,
    "text": summary_message,
}

# 打印请求的详细信息
print(f"Telegram 请求 URL: {telegram_url}")
print(f"Telegram 请求 Payload: {telegram_payload}")

# 发送请求到 Telegram
response = requests.post(telegram_url, json=telegram_payload)

# 打印请求的状态码和返回内容
print(f"Telegram 请求状态码：{response.status_code}")
print(f"Telegram 请求返回内容：{response.text}")

if response.status_code != 200:
    print("发送 Telegram 消息失败")
else:
    print("发送 Telegram 消息成功")
