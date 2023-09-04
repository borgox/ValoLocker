import os
import requests
import ssl
import threading
import json
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedStyle

# Define a global variable to control the main loop
exit_time = False


def run_instalock(nameex):
    while True:
        if exit_time:
            break

        # Construct the path to the Riot Games lockfile
        lockfile_path = "".join(
            [os.getenv("LOCALAPPDATA"), r"\Riot Games\Riot Client\Config\lockfile"]
        )

        # Read the lockfile to get information
        with open(lockfile_path, "r") as lockfile:
            lockfile_data = lockfile.read().split(":")

        # Build the base URL for requests
        base_url = f"{lockfile_data[4]}://127.0.0.1:{lockfile_data[2]}"
        session = requests.Session()
        session.auth = ("riot", lockfile_data[3])

        # Send a GET request to obtain an access token
        response = session.get(
            f"{base_url}/entitlements/v1/token", verify=ssl.CERT_NONE
        )
        if exit_time:
            break

        access_token = response.json()["accessToken"]

        # Send a POST request to obtain an entitlements token
        response2 = requests.post(
            "https://entitlements.auth.riotgames.com/api/token/v1",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )
        if exit_time:
            break
        entitlements_token = response2.json()["entitlements_token"]

        valorant_server = "eu"

        # Send a GET request to obtain user information
        response = requests.get(
            "https://auth.riotgames.com/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )
        if exit_time:
            break
        user_id = response.json()["sub"]

        while True:
            if exit_time:
                break

            # Send a GET request to check the game lobby status
            response = requests.get(
                f"https://glz-{valorant_server}-1.{valorant_server}.a.pvp.net/pregame/v1/players/{user_id}",
                headers={
                    "X-Riot-Entitlements-JWT": entitlements_token,
                    "Authorization": f"Bearer {access_token}",
                },
            )

            if response.status_code == 404:
                print("Waiting for the champion selection screen")
            if response.status_code != 404:
                break

        if exit_time:
            break
        match_id = response.json()["MatchID"]

        agent_name = nameex

        with open("agents.json", "r") as agents_file:
            agents = json.load(agents_file)

        agent_id = agents.get(agent_name)  # Use .get() to handle agent not found

        if agent_id is None:
            print(f"Agent '{agent_name}' not found in the JSON data.")
            break

        # Send POST requests to select an agent in the game lobby
        while True:
            if exit_time:
                break

            response = requests.post(
                f"https://glz-{valorant_server}-1.{valorant_server}.a.pvp.net/pregame/v1/matches/{match_id}/lock/{agent_id}",
                headers={
                    "X-Riot-Entitlements-JWT": entitlements_token,
                    "Authorization": f"Bearer {access_token}",
                },
            )

            if response.status_code == 200:
                break
        if exit_time:
            break


def instalock(agent_name):
    global exit_time
    exit_time = False
    t = threading.Thread(target=run_instalock, args=(agent_name,))
    t.start()


def stop_instalock():
    global exit_time
    exit_time = True


# Create a tkinter window
window = tk.Tk()
window.title("Valorant Instalocker")
window.geometry("1200x800")  # Increase the window size

# Create a themed style
style = ThemedStyle(window)
style.set_theme("equilux")  # Choose a theme (e.g., "equilux")

# Create a label for agent selection with a larger font
agent_label = ttk.Label(window, text="Select Agent:", )
agent_label.pack(pady=20)  # Increase padding

# Load agent data from agents.json
with open("agents.json", "r") as agents_file:
    agents_data = json.load(agents_file)
    agent_names = list(agents_data.keys())

# Create a dropdown menu to select an agent with larger font
agent_var = tk.StringVar(window)
agent_var.set(agent_names[0])  # Set the default agent

# Create a custom style for the Combobox
style.configure(
    "AgentCombo.TCombobox",
    foreground="red",
    fieldbackground="white",
    
)  # Increase font size

agent_dropdown = ttk.Combobox(
    window, textvariable=agent_var, values=agent_names, style="AgentCombo.TCombobox"
)
agent_dropdown.pack(pady=20)  # Increase padding

# Create a Start button to begin the instalocking with larger font
start_button = ttk.Button(
    window,
    text="Start",
    command=lambda: instalock(agent_var.get()),
    style="Start.TButton",
)
start_button.pack(pady=30)  # Increase padding

# Create a Stop button to stop the instalocking with larger font
stop_button = ttk.Button(
    window,
    text="Stop",
    command=stop_instalock,
    style="Stop.TButton",
)
stop_button.pack(pady=20)  # Increase padding
credits_info = "Discord: borgo.xy, Valorant: borgoxy"


# Create a Credits label with the credits information
credits_label = ttk.Label(window, text=credits_info)
credits_label.pack(pady=20)  # Increase padding

def retrieve_dict():
    r = requests.get("https://valorant-api.com/v1/agents")
    filtered = {}
    for agent_info in r.json()["data"]:
        uuid = agent_info["uuid"]
        name = agent_info["displayName"]
        name = name.lower()
        filtered[name] = uuid
    return filtered


def retrieve_and_save_agents():
    # Execute the functionality from agentData.py
    data = retrieve_dict()
    with open("agents.json", "w") as file:
        json.dump(data, file, indent=4)


# Create a button to retrieve and save agents data
retrieve_agents_button = ttk.Button(
    window,
    text="Reload agents.json",
    command=retrieve_and_save_agents,
)
retrieve_agents_button.pack(pady=20)  # Increase padding


window.mainloop()
