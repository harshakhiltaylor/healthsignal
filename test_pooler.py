import socket

regions = [
    "us-east-1", "us-west-1", "us-west-2", "eu-central-1", "eu-west-1", "eu-west-2",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2", "ap-south-1",
    "sa-east-1", "ca-central-1"
]

project_ref = "zaluzufofkddxnxiqvix"

for region in regions:
    host = f"aws-0-{region}.pooler.supabase.com"
    try:
        # Check if the host resolves to an IPv4 address
        ip = socket.gethostbyname(host)
        # Check if we can connect to 6543
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((ip, 6543))
        if result == 0:
            print(f"Possible pooler: {host} -> {ip}")
        s.close()
    except Exception:
        pass
