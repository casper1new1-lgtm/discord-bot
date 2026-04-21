import asyncio
import os
import random
import time
import logging

import discord

logging.basicConfig(level=logging.INFO)

# =========================
# CONFIG
# =========================

STATUS_INTERVAL = 30
WATCHDOG_MAX_OFFLINE = 60
SOCKET_DEAD_TIMEOUT = 100

BOTS_CONFIG = [
    {
        "name": "Bot 1",
        "token": os.getenv("TOKEN"),
        "statuses": [
            "🔥 VIP SERVER ADS",
            "⚔️ INQUIRE NOW!",
            "🎮 L2YOURSERVER.COM",
        ],
    },
    {
        "name": "Bot 2",
        "token": os.getenv("TOKEN_2"),
        "statuses": [
            "🔥 VIP SERVER ADS",
            "⚔️ INQUIRE NOW!",
            "🎮 L2YOURSERVER.COM",
        ],
    },
]

BOTS = [b for b in BOTS_CONFIG if b.get("token")]
_clients = {}

WATCHDOG_CHECK = 20


# =========================
# BOT LOGIC
# =========================

async def run_once(name, token, statuses):
    intents = discord.Intents.none()
    client = discord.Client(intents=intents, heartbeat_timeout=30)
    _clients[name] = client

    loop = asyncio.get_running_loop()
    last_socket_data = loop.time()

    @client.event
    async def on_ready():
        print(f"[{name}] ONLINE: {client.user}")

    @client.event
    async def on_disconnect():
        print(f"[{name}] Disconnected")

    @client.event
    async def on_resumed():
        print(f"[{name}] Resumed")

    @client.event
    async def on_socket_raw_receive(msg):
        nonlocal last_socket_data
        last_socket_data = loop.time()

    async def rotate():
        await client.wait_until_ready()
        while not client.is_closed():
            try:
                status = random.choice(statuses)
                await client.change_presence(
                    activity=discord.Game(name=status)
                )
            except Exception as e:
                print(f"[{name}] Status error:", e)

            await asyncio.sleep(STATUS_INTERVAL)

    async def watchdog():
        offline_since = None
        while not client.is_closed():
            await asyncio.sleep(WATCHDOG_CHECK)
            now = loop.time()

            silence = now - last_socket_data
            if silence >= SOCKET_DEAD_TIMEOUT:
                print(f"[{name}] Zombie detected → reconnect")
                await client.close()
                return

            if client.is_ready():
                offline_since = None
            else:
                if offline_since is None:
                    offline_since = now
                elif now - offline_since >= WATCHDOG_MAX_OFFLINE:
                    print(f"[{name}] Not ready → reconnect")
                    await client.close()
                    return

    rotate_task = asyncio.create_task(rotate())
    watchdog_task = asyncio.create_task(watchdog())

    try:
        await client.start(token, reconnect=True)
    except discord.LoginFailure:
        print(f"[{name}] INVALID TOKEN")
        return
    finally:
        rotate_task.cancel()
        watchdog_task.cancel()
        _clients.pop(name, None)


async def bot_loop(name, token, statuses):
    attempt = 0
    while True:
        attempt += 1
        print(f"[{name}] Start attempt #{attempt}")

        try:
            await run_once(name, token, statuses)
        except Exception as e:
            print(f"[{name}] Crash:", e)

        delay = 0 if attempt == 1 else min(2 ** min(attempt - 1, 3), 15)
        await asyncio.sleep(delay if delay else 1)

        if attempt >= 5:
            attempt = 0


async def main():
    if not BOTS:
        raise RuntimeError("No tokens found")

    await asyncio.gather(*[
        bot_loop(b["name"], b["token"], b["statuses"])
        for b in BOTS
    ])


if __name__ == "__main__":
    asyncio.run(main())