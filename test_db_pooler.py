import asyncio
import asyncpg
import socket

regions = [
    "us-east-1", "us-west-1", "us-west-2", "eu-central-1", "eu-west-1", "eu-west-2",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2", "ap-south-1",
    "sa-east-1", "ca-central-1"
]

async def test():
    for region in regions:
        host = f"aws-0-{region}.pooler.supabase.com"
        url = f"postgresql://postgres.zaluzufofkddxnxiqvix:HealthSignal12342@{host}:6543/postgres"
        try:
            # We must use asyncpg directly, timeout 2s
            conn = await asyncpg.connect(url, timeout=3.0)
            print(f"\nSUCCESS! The correct region is {region}")
            print(f"URL: postgresql+asyncpg://postgres.zaluzufofkddxnxiqvix:HealthSignal12342@{host}:6543/postgres\n")
            await conn.close()
            return region, host
        except Exception as e:
            pass
    print("Failed to authenticate with any region.")

if __name__ == "__main__":
    asyncio.run(test())
