import psutil
import ping3
import os
import requests
import subprocess

LAST_IP_FILE = "last_ip.txt"


def check_vpn_connection():
    # Get a list of all network interfaces
    interfaces = psutil.net_if_stats().keys()

    if any("tun" in interface.lower() for interface in interfaces):
        print("[+] Connected to the OpenVPN tunnel.")
        return True
    else:
        print("[-] No active OpenVPN tunnel connection.")
        return False


def check_connectivity(host):
    try:
        response = ping3.ping(host)
        if response is not None:
            response = round(response, 2)
            print(f"[+] There is a connection with the target. Response time: {response} ms")
        else:
            print(f"Failed to ping {host}. Check connectivity.")
            return
    except PermissionError:
        print("[-] Permission denied. Try running the script with elevated privileges.")


def check_ip_forwarding(host):
    global forwarded_url
    global domain
    try:
        # Get the redirect URL (if any) from the IP address
        response = requests.get(f"http://{host}", allow_redirects=False)

        if response.status_code == 301 or response.status_code == 302:
            forwarded_url = response.headers['Location']
            print(f"[+] IP address {host} is forwarding to: {forwarded_url}")

            # Remove everything until and including "//" in the forwarded URL
            domain = forwarded_url.split("//", 1)[-1]

            # Check if the entry already exists in /etc/hosts
            with open("/etc/hosts", "r") as hosts_file:
                hosts_content = hosts_file.read()
                if f"{host} {domain}" not in hosts_content:
                    with open("/etc/hosts", "a") as hosts_file:
                        hosts_file.write(f"{host} {domain}\n")
                        print(f"[+] Entry added to /etc/hosts.")
                else:
                    print("[+] Entry already exists in /etc/hosts.")
        else:
            print(f"[-] IP address {host} is not forwarding to a domain URL.")
    except requests.RequestException:
        print(f"[-] Failed to check IP forwarding for {host}.")


def run_gobuster():
    print("GoBuster")
    try:
        # Run Gobuster command
        subprocess.run(["gobuster", "dir", "-u", forwarded_url, "-w",
                        "/usr/share/wordlists/dirbuster/directory-list-2.3-small.txt", "-o", f"gobuster_{domain}.txt"])

        print("[+] Gobuster command completed successfully.")
    except FileNotFoundError:
        print("[-] Gobuster command not found. Make sure it is installed and in your PATH.")


def save_last_ip(ip):
    with open(LAST_IP_FILE, "w") as last_ip_file:
        last_ip_file.write(ip)


def get_last_ip():
    try:
        with open(LAST_IP_FILE, "r") as last_ip_file:
            return last_ip_file.read().strip()
    except FileNotFoundError:
        return None


if __name__ == "__main__":
    print("Welcome to CTFBuddy\n")

    last_ip = get_last_ip()
    if last_ip:
        use_last_ip = input(f"Do you want to use the last inserted IP address ({last_ip})? (y/n): ").lower()
        if use_last_ip == "y":
            target = last_ip
        else:
            target = input("Target IP address: ")
    else:
        target = input("Target IP address: ")

    check_connectivity(target)
    check_ip_forwarding(target)
    save_last_ip(target)

    while True:
        print("\nTasks:\n1. Run GoBuster dir search on target \n2. Run nmap scan of the target \n3. Terminate script")
        usr_input = input("Choose a task to perform (1/2/3): ")

        if usr_input == "1":
            run_gobuster()
        elif usr_input == "2":
            print("Nmap scan not implemented yet.")
        elif usr_input == "3":
            print("Terminating script. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
