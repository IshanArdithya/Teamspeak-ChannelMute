import socket
import time
import re

# connection details
SERVER_IP = "128.199.83.243"
QUERY_PORT = 10011  # default 10011
USERNAME = "Among-Us"  # server query connection
PASSWORD = "NOzrTyx4"  # server query connection
TARGET_CHANNEL_ID = 86  # channel id
BOT_NICKNAME = "Among-Us"  # bot name

current_state = None

def send_command(conn, command):
    conn.sendall((command + "\n").encode())
    response = conn.recv(4096).decode()
    return response

def get_bot_client_id(conn, nickname):
    escaped_nickname = re.escape(nickname)

    # get clients list
    response = send_command(conn, "clientlist")
    print("Client list response:", response)

    # match exact nickname with client_type=1 (0 = users, 1 = serverquery)
    match = re.search(rf"clid=(\d+).*?client_nickname={escaped_nickname}\b.*?client_type=1", response)
    if match:
        return match.group(1)
    return None

def escape_message(message):
    return message.replace(" ", "\\s")

def send_message_to_channel(conn, channel_id, message):
    escaped_message = escape_message(message)
    command = f"sendtextmessage targetmode=2 target={channel_id} msg={escaped_message}"
    response = send_command(conn, command)
    print(f"Send message response: {response}")

def process_chat_message(conn, message):
    global current_state

    # changeable
    if "Mute" in message and current_state != "Muted":
        talk_power = 100
        action = "Muted"
        color = "red"
        current_state = "Muted"
    elif "Unmute" in message and current_state != "Unmuted":
        talk_power = 0
        action = "Unmuted"
        color = "green"
        current_state = "Unmuted"
    else:
        return

    talk_power_command = f"channeledit cid={TARGET_CHANNEL_ID} channel_needed_talk_power={talk_power}"
    talk_power_response = send_command(conn, talk_power_command)
    print(f"Talk power adjustment response: {talk_power_response}")

    send_message_to_channel(conn, TARGET_CHANNEL_ID, f"[color=#55aaff]Channel has been [/color][color={color}][b]{action}[/b][/color]")

def main():
    try:
        # connection to ts
        with socket.create_connection((SERVER_IP, QUERY_PORT)) as conn:
            response = send_command(conn, "login {} {}".format(USERNAME, PASSWORD))
            print("Login response:", response)

            response = send_command(conn, "use 1")
            print("Use response:", response)

            # 3 attempts to get bot client ID
            for attempt in range(3):
                bot_client_id = get_bot_client_id(conn, BOT_NICKNAME)
                if bot_client_id:
                    response = send_command(conn, f"clientmove cid={TARGET_CHANNEL_ID} clid={bot_client_id}")
                    print(f"Move to target channel response: {response}")
                    break
                else:
                    print(f"Attempt {attempt + 1}: Bot client ID not found.")
                    time.sleep(2)
            else:
                print("Client ID not found. Check if the BOT_NICKNAME is correct.")
                return

            initial_message = "[color=green][b]Connected Successfully![/b][/color]"
            send_message_to_channel(conn, TARGET_CHANNEL_ID, initial_message)

            response = send_command(conn, "servernotifyregister event=textchannel")
            print("Registered for textchannel notifications:", response)

            while True:
                response = send_command(conn, "servernotifyregister event=textchannel")
                print("Channel notifications response:", response)

                if "msg=" in response:
                    messages = re.findall(r"msg=(.*?)\n", response)
                    for msg in messages:
                        process_chat_message(conn, msg)

                time.sleep(5)  # adjust time to avoid flooding

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
