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
    command = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {port} {username}@{host} 'curl -s ifconfig.me'"
    try:
        ip = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).strip().decode('utf-8')
        return ip
    except subprocess.CalledProcessError as e:
        return f"Failed to get public IP for {host}: {e.output.decode('utf-8')}"

# Function to check and recover VLESS service
def check_and_recover_vless(username, password, host, port):
    # Ensure the local check_vless.sh file exists
    local_script_path = os.path.join(os.path.dirname(__file__), 'check_vless.sh')
    print(f"{local_script_path=}")
    if not os.path.exists(local_script_path):
        return f"Local script check_vless.sh does not exist at {local_script_path}"

    # Upload new check_vless.sh file
    scp_command = f"sshpass -p '{password}' scp -P {port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {local_script_path} {username}@{host}:~/domains/{username}.serv00.net/vless/check_vless.sh"
    try:
        subprocess.check_output(scp_command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return f"Failed to upload check_vless.sh to {host}:\n{e.output.decode('utf-8')}"

    # Execute recovery command
    restore_command = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {port} {username}@{host} 'cd ~/domains/{username}.serv00.net/vless && ./check_vless.sh'"
    try:
        output = subprocess.check_output(restore_command, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
        return f"Successfully recovered VLESS service on {host}:\n{output}"
    except subprocess.CalledProcessError as e:
        return f"Failed to recover VLESS service on {host}:\n{e.output.decode('utf-8')}"

# Iterate over the server list and perform operations
ip_messages = ""
for server in servers:
    host = server['host']
    port = server['port']
    username = server['username']
    password = server['password']

    # Check and recover VLESS service
    vless_message = check_and_recover_vless(username, password, host, port)
    summary_message += f"\n{vless_message}"

    # Get current public IP address
    current_ip = get_public_ip(username, password, host, port)
    ip_messages += f"\nCurrent public IP address of {host}: {current_ip}"

# Append the IP messages to the summary
summary_message += ip_messages

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
