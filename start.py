import subprocess

SESSION_NAME = "mainframe"
VENV_ACTIVATE = ".venv/bin/activate.fish"
SCRIPTS = ["mainframe.py", "websocket.py", "~/Documents/Kokoro-FastAPI/start-gpu.sh"]


def tmux(cmd):
    subprocess.run(["tmux"] + cmd, check=True)


def setup_tmux_session():
    result = subprocess.run(
        ["tmux", "has-session", "-t", SESSION_NAME], capture_output=True
    )
    if result.returncode == 0:
        print(f"[!] Session '{SESSION_NAME}' already exists. Attaching...")
        subprocess.run(["tmux", "attach-session", "-t", SESSION_NAME])
        return

    first_script = SCRIPTS[0]
    tmux(["new-session", "-d", "-s", SESSION_NAME, run_cmd(first_script)])

    for script in SCRIPTS[1:]:
        tmux(["new-window", "-t", SESSION_NAME, "-n", script, run_cmd(script)])

    print(
        "[+] Mainframe system launched in tmux. Use Use `tmux attach -t mainframe` to view."
    )
    subprocess.run(["tmux", "attach-session", "-t", SESSION_NAME])


def run_cmd(script):
    if script.endswith(".py"):
        return f'fish -c \'source "{VENV_ACTIVATE}"; python "{script}"; exec fish\''
    elif script.endswith(".sh"):
        return f"fish -c 'cd ~/Documents/Kokoro-FastAPI;{script}; exec fish'"
    else:
        return f"fish -c 'echo Unsupported file type: {script}; exec fish'"


if __name__ == "__main__":
    print("[+] Booting Mainframe in tmux mode with Fish shell...")
    setup_tmux_session()
