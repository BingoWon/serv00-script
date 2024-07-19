import os
import json
import subprocess
import requests

# Load secrets from environment variables
accounts_json = os.getenv('ACCOUNTS_JSON')
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

# Parse JSON string
servers = json.loads(accounts_json)

# Initialize summary message
summary_message = "VLESS Service Status and Public IP Report:\n"

# Function to get the public IP address of a server
def get_public_ip(username, password, host, port):
    command = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {port} {username}@{host} 'curl -s ifconfig.me 2>/dev/null'"
    try:
        ip = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).strip().decode('utf-8')
        return ip
    except subprocess.CalledProcessError as e:
        print(f"Failed to get public IP for {host}: {e.output.decode('utf-8')}")
        return None

# Function to check and recover VLESS service
def check_and_recover_vless(username, password, host, port):
    # Ensure the local check_vless.sh file exists
    local_script_path = os.path.join(os.path.dirname(__file__), 'check_vless.sh')
    if not os.path.exists(local_script_path):
        return f"\nLocal script check_vless.sh does not exist at {local_script_path}"

    # Upload new check_vless.sh file
    scp_command = f"sshpass -p '{password}' scp -P {port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {local_script_path} {username}@{host}:~/domains/{username}.serv00.net/vless/check_vless.sh 2>/dev/null"
    try:
        subprocess.check_output(scp_command, shell=True, stderr=subprocess.STDOUT)
        print(f"Successfully uploaded check_vless.sh to {host}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to upload check_vless.sh to {host}: {e.output.decode('utf-8')}")
        return f"\nFailed to upload check_vless.sh to {host}:\n{e.output.decode('utf-8')}"

    # Execute recovery command
    restore_command = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {port} {username}@{host} 'cd ~/domains/{username}.serv00.net/vless && ./check_vless.sh 2>/dev/null'"
    try:
        output = subprocess.check_output(restore_command, shell=True, stderr=subprocess.STDOUT)
        return f"\nSuccessfully recovered VLESS service on {host}:\n{output.decode('utf-8')}"
    except subprocess.CalledProcessError as e:
        return f"\nFailed to recover VLESS service on {host}:\n{e.output.decode('utf-8')}"

# Iterate over the server list and perform operations
for server in servers:
    host = server['host']
    port = server['port']
    username = server['username']
    password = server['password']

    print(f"Connecting to {host}...")

    # Get current public IP address
    current_ip = get_public_ip(username, password, host, port)
    if current_ip:
        print(f"Current public IP address of {host} is {current_ip}")
        summary_message += f"\nCurrent public IP address of {host}: {current_ip}"
    else:
        summary_message += f"\nFailed to get current public IP address of {host}."

    # Check and recover VLESS service
    vless_message = check_and_recover_vless(username, password, host, port)
    summary_message += vless_message

# Send summary message to Telegram
telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
telegram_payload = {
    "chat_id": telegram_chat_id,
    "text": summary_message,
}

# Print request details
print(f"Telegram request URL: {telegram_url}")
print(f"Telegram request payload: {telegram_payload}")

# Send request to Telegram
response = requests.post(telegram_url, json=telegram_payload)

# Print response status and content
print(f"Telegram request status code: {response.status_code}")
print(f"Telegram request response content: {response.text}")

if response.status_code != 200:
    print("Failed to send Telegram message")
else:
    print("Telegram message sent successfully")
