import asyncio
import os
import random
import logging
from threading import Thread

import discord
from flask import Flask

logging.basicConfig(level=logging.INFO)

# =========================
# CONFIG
# =========================

STATUS_INTERVAL = 30

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
     {
        "name": "Bot 3",
        "token": os.getenv("TOKEN_3"),
        "statuses": [
            "🔥 HighFive Full PVP",
            "⚔️ Beta - May 09 | Live - May 16",
            "🎮 L2Harmony.com",
        ],
    },
]

BOTS = [b for b in BOTS_CONFIG if b.get("token")]

_clients = {}

# =========================
# WEB SERVER (RENDER REQUIREMENT)
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running", 200


def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# =========================
# DISCORD BOT LOGIC
# =========================

async def run_bot(name, token, statuses):
    intents = discord.Intents.none()
    client = discord.Client(intents=intents)
    _clients[name] = client

    async def rotate_status():
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

    @client.event
    async def on_ready():
        print(f"[{name}] ONLINE: {client.user}")

    try:
        asyncio.create_task(rotate_status())
        await client.start(token, reconnect=True)

    except discord.LoginFailure:
        print(f"[{name}] INVALID TOKEN")
    except Exception as e:
        print(f"[{name}] ERROR:", e)
    finally:
        _clients.pop(name, None)


async def main():
    if not BOTS:
        raise RuntimeError("No valid tokens found")

    await asyncio.gather(*[
        run_bot(b["name"], b["token"], b["statuses"])
        for b in BOTS
    ])


# =========================
# START EVERYTHING
# =========================

if __name__ == "__main__":
    # Start web server (required for Render free web service)
    Thread(target=run_web, daemon=True).start()

    # Start Discord bots
    asyncio.run(main())
