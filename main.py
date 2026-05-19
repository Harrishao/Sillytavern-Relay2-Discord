import asyncio
import configparser
import os

import discord
from discord.ext import commands

import admin
import core

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class RelayBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = False
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.load_extension("cogs.st_commands")
        await self.load_extension("cogs.admin_commands")
        try:
            synced = await self.tree.sync()
            print(f"[bot] 已同步 {len(synced)} 条斜杠命令")
        except Exception as e:
            print(f"[bot] 命令同步失败: {e}")

    async def on_ready(self):
        print(f"[bot] 已登录: {self.user} (ID: {self.user.id})")
        print("[bot] 正在启动浏览器...")
        await core.init_browser()
        print("[bot] 就绪！")

    async def close(self):
        if core.get_page() is not None:
            print("[bot] 正在关闭浏览器...")
            await core.close_browser()
        await super().close()


def main():
    admin.init()

    _cfg = configparser.ConfigParser()
    _cfg.read(os.path.join(BASE_DIR, "config.ini"))
    token = _cfg.get("discord", "bot_token", fallback="")
    if not token:
        print("[bot] 错误: config.ini 中未配置 bot_token")
        return

    bot = RelayBot()
    bot.run(token)


if __name__ == "__main__":
    main()
