import asyncio
import os
import traceback

import discord
from discord import app_commands
from discord.ext import commands

import admin
import core


class STCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _check_whitelist(self, interaction: discord.Interaction) -> bool:
        """检查用户是否在白名单中，不在则发送 ephemeral 提示并返回 False"""
        if not admin.is_whitelisted(interaction.user.id):
            await interaction.response.send_message(
                "管理员模式已开启，但你不在白名单中哦...", ephemeral=True
            )
            return False
        return True

    async def _safe_followup(self, interaction: discord.Interaction, *,
                             content: str = None, file_path: str = None,
                             fallback_text: str = None) -> bool:
        """
        安全发送 followup 消息。
        优先发送图片文件，网络错误时尝试发送纯文本回退。
        返回 True 表示发送成功。
        """
        try:
            if file_path and os.path.isfile(file_path):
                await interaction.followup.send(
                    content=content or "", file=discord.File(file_path)
                )
            else:
                await interaction.followup.send(content=content or "")
            return True
        except (discord.HTTPException, OSError) as e:
            print(f"[st_commands] 文件上传失败(网络错误): {e}")
            try:
                fallback = fallback_text or (content or "操作已完成，但截图上传失败，请稍后重试 /lastmsg 查看。")
                await interaction.followup.send(content=fallback)
                return True
            except Exception as e2:
                print(f"[st_commands] 文本回退也失败了: {e2}")
                return False

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        """Cog 级斜杠命令错误处理"""
        # 如果已经发送过响应，尝试 followup 报错
        if interaction.response.is_done():
            try:
                await interaction.followup.send("执行过程中遇到网络波动，请稍后重试...")
            except Exception:
                pass
            return

        # 尚未响应，发送 ephemeral 报错
        try:
            await interaction.response.send_message(
                "执行过程中遇到错误，请稍后重试...", ephemeral=True
            )
        except Exception:
            pass

        print(f"[st_commands] 命令异常: {error}")
        traceback.print_exception(type(error), error, error.__traceback__)

    @app_commands.command(name="st", description="发送消息到酒馆并获取AI回复截图")
    @app_commands.describe(message="要发送的消息内容")
    async def cmd_st(self, interaction: discord.Interaction, message: str):
        if not await self._check_whitelist(interaction):
            return
        if not core.acquire_lock():
            await interaction.response.send_message(
                "有正在处理中的消息，请稍后再试...或使用 /stop 中止当前操作",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        try:
            result = await core.send_message(message)
            if result is None or not result.get("content"):
                await interaction.followup.send("消息发送失败或等待回复超时...")
                return

            path = result.get("screenshot_path")
            if path and os.path.isfile(path):
                await self._safe_followup(interaction, file_path=path)
            else:
                content = result["content"][:1900]
                await interaction.followup.send(f"```\n{content}\n```")
        finally:
            core.release_lock()

    @app_commands.command(name="stop", description="停止当前正在生成的AI回复")

    async def cmd_stop(self, interaction: discord.Interaction):
        if not await self._check_whitelist(interaction):
            return
        await interaction.response.defer()
        ok = await core.cancel_processing()
        core.release_lock()
        if ok:
            await interaction.followup.send("已中止当前生成。")
        else:
            await interaction.followup.send("没有正在进行的生成。")

    @app_commands.command(name="lastmsg", description="截取酒馆最后一条消息")

    async def cmd_lastmsg(self, interaction: discord.Interaction):
        if not await self._check_whitelist(interaction):
            return
        await interaction.response.defer()
        path = await core.capture_screenshot()
        if path and os.path.isfile(path):
            await self._safe_followup(interaction, file_path=path)
        else:
            await interaction.followup.send("截图失败，请稍后重试...")

    @app_commands.command(name="ss", description="全页截取酒馆当前界面")

    async def cmd_ss(self, interaction: discord.Interaction):
        if not await self._check_whitelist(interaction):
            return
        await interaction.response.defer()
        path = await core.capture_full_screenshot()
        if path and os.path.isfile(path):
            await self._safe_followup(interaction, file_path=path)
        else:
            await interaction.followup.send("截图失败，请稍后重试...")

    @app_commands.command(name="rf", description="刷新酒馆页面")

    async def cmd_rf(self, interaction: discord.Interaction):
        if not await self._check_whitelist(interaction):
            return
        await interaction.response.defer()
        ok = await core.refresh_page()
        if not ok:
            await interaction.followup.send("页面刷新失败...")
            return
        path = await core.capture_full_screenshot()
        if path and os.path.isfile(path):
            await self._safe_followup(interaction, content="页面已刷新:", file_path=path)
        else:
            await interaction.followup.send("页面已刷新，但截图失败。")

    @app_commands.command(name="del", description="删除酒馆当前聊天最后N条消息")
    @app_commands.describe(n="删除条数（1或2）")

    async def cmd_del(self, interaction: discord.Interaction, n: int = 1):
        if not await self._check_whitelist(interaction):
            return
        await interaction.response.defer()
        ok = await core.delete_messages(n)
        if not ok:
            await interaction.followup.send("删除消息失败。")
            return
        await asyncio.sleep(1)
        path = await core.capture_screenshot()
        if path and os.path.isfile(path):
            await self._safe_followup(interaction, content=f"已删除最后 {n} 条消息:", file_path=path)
        else:
            await interaction.followup.send(f"已删除最后 {n} 条消息。")

    @app_commands.command(name="left", description="切换到上一个备选回复（左翻页）")

    async def cmd_left(self, interaction: discord.Interaction):
        if not await self._check_whitelist(interaction):
            return
        await interaction.response.defer()
        ok = await core.swipe_left()
        if not ok:
            await interaction.followup.send("左翻页失败，没有更多备选回复或当前不在聊天中。")
            return
        path = await core.capture_screenshot()
        if path and os.path.isfile(path):
            await self._safe_followup(interaction, file_path=path)
        else:
            await interaction.followup.send("截图失败，请稍后重试...")

    @app_commands.command(name="right", description="切换到下一个备选回复（右翻页）")

    async def cmd_right(self, interaction: discord.Interaction):
        if not await self._check_whitelist(interaction):
            return
        await interaction.response.defer()
        if not core.acquire_lock():
            await interaction.followup.send("有正在处理中的消息，请稍后再试...")
            return

        try:
            result = await core.swipe_right()
            if result is None:
                await interaction.followup.send("右翻页失败，当前不在聊天中。")
                return

            if result == "generating":
                response = await core.wait_for_response()
                if not response:
                    await interaction.followup.send("等待LLM回复超时...")
                    return

            path = await core.capture_screenshot()
            if path and os.path.isfile(path):
                await self._safe_followup(interaction, file_path=path)
            else:
                await interaction.followup.send("截图失败，请稍后重试...")
        finally:
            core.release_lock()

    @app_commands.command(name="regenerate", description="重新生成AI回复")

    async def cmd_regenerate(self, interaction: discord.Interaction):
        if not await self._check_whitelist(interaction):
            return
        if not core.acquire_lock():
            await interaction.response.send_message(
                "有正在处理中的消息，请稍后再试...或使用 /stop 中止", ephemeral=True
            )
            return

        await interaction.response.defer()
        try:
            ok = await core.regenerate()
            if not ok:
                await interaction.followup.send("重新生成触发失败...")
                return

            response = await core.wait_for_response()
            if not response:
                await interaction.followup.send("等待LLM回复超时...")
                return

            path = await core.capture_screenshot()
            if path and os.path.isfile(path):
                await self._safe_followup(interaction, file_path=path)
            else:
                content = response.get("content", "")[:1900]
                await interaction.followup.send(f"```\n{content}\n```")
        finally:
            core.release_lock()

    @app_commands.command(name="chat", description="查看最近聊天列表或切换到指定聊天")
    @app_commands.describe(index="聊天序号（不填则列出所有聊天）")

    async def cmd_chat(self, interaction: discord.Interaction, index: int = -1):
        if not await self._check_whitelist(interaction):
            return
        await interaction.response.defer()

        chats = await core.fetch_recent_chats()
        if not chats:
            await interaction.followup.send("获取聊天列表失败。")
            return

        if index >= 0:
            if index >= len(chats):
                await interaction.followup.send(f"序号超出范围，共 {len(chats)} 条聊天。")
                return

            chat = chats[index]
            file_name = chat.get("file_name", "")
            if not file_name:
                await interaction.followup.send("无法获取聊天文件名。")
                return

            ok = await core.open_chat(file_name)
            if not ok:
                await interaction.followup.send("切换聊天失败。")
                return

            await asyncio.sleep(2)
            path = await core.capture_screenshot()
            if path and os.path.isfile(path):
                name = file_name.replace(".jsonl", "")
                await self._safe_followup(interaction, content=f"已切换到: {name}", file_path=path)
            else:
                await interaction.followup.send("截图失败...")
            return

        # 无参数：列出聊天列表
        lines = [f"**最近聊天 ({len(chats)}条)**"]
        for i, c in enumerate(chats[:20]):
            ch_name = c.get("file_name", "?").replace(".jsonl", "")
            items = c.get("chat_items", 0)
            mes = (c.get("mes", "") or "")[:50].replace("\n", " ")
            lines.append(f"`{i}` — {ch_name}  _(消息:{items})_")
            if mes:
                lines.append(f"> {mes}")

        if len(chats) > 20:
            lines.append(f"...还有 {len(chats) - 20} 条")

        msg = "\n".join(lines)
        if len(msg) > 2000:
            msg = msg[:1950] + "\n...(截断)"
        await interaction.followup.send(msg)

    @app_commands.command(name="char", description="查看角色卡列表或选择角色")
    @app_commands.describe(index="角色序号（不填则列出所有角色）")

    async def cmd_char(self, interaction: discord.Interaction, index: int = -1):
        if not await self._check_whitelist(interaction):
            return
        await interaction.response.defer()

        chars = await core.fetch_characters()
        if not chars:
            await interaction.followup.send("获取角色卡列表失败。")
            return

        if index >= 0:
            if index >= len(chars):
                await interaction.followup.send(f"序号超出范围，共 {len(chars)} 个角色。")
                return

            char = chars[index]
            avatar = char.get("avatar", "")
            char_name = char.get("name", "?")

            chats = await core.fetch_character_chats(avatar)
            if not chats:
                await interaction.followup.send(f"角色 **{char_name}** 没有聊天记录。")
                return

            if len(chats) == 1:
                file_name = chats[0].get("file_name", "")
                if not file_name:
                    await interaction.followup.send("无法获取聊天文件名。")
                    return
                ok = await core.open_chat(file_name)
                if not ok:
                    await interaction.followup.send("切换聊天失败。")
                    return
                await asyncio.sleep(2)
                path = await core.capture_screenshot()
                if path and os.path.isfile(path):
                    await self._safe_followup(interaction, content=f"已切换到: {char_name}", file_path=path)
                else:
                    await interaction.followup.send("截图失败...")
            else:
                lines = [f"**{char_name} 的聊天记录 ({len(chats)}条)**"]
                for i, c in enumerate(chats[:15]):
                    fname = c.get("file_name", "?").replace(".jsonl", "")
                    items = c.get("chat_items", 0)
                    lines.append(f"`{i}` — {fname}  _(消息:{items})_")
                if len(chats) > 15:
                    lines.append(f"...还有 {len(chats) - 15} 条")
                lines.append(f"使用 `/chat <序号>` 选择聊天")
                msg = "\n".join(lines)
                if len(msg) > 2000:
                    msg = msg[:1950] + "\n...(截断)"
                await interaction.followup.send(msg)
            return

        # 无参数：列出角色卡
        import datetime as dt
        lines = [f"**角色卡列表 ({len(chars)}个)**"]
        for i, c in enumerate(chars[:25]):
            c_name = c.get("name", "?")
            last = c.get("date_last_chat", 0)
            if last:
                try:
                    last_str = dt.datetime.fromtimestamp(last / 1000).strftime("%m/%d %H:%M")
                except Exception:
                    last_str = str(last)
            else:
                last_str = "从未"
            lines.append(f"`{i}` — {c_name}  _(最后: {last_str})_")

        if len(chars) > 25:
            lines.append(f"...还有 {len(chars) - 25} 个")
        lines.append(f"使用 `/char <序号>` 选择角色查看聊天")

        msg = "\n".join(lines)
        if len(msg) > 2000:
            msg = msg[:1950] + "\n...(截断)"
        await interaction.followup.send(msg)


    @app_commands.command(name="user", description="查看用户设定列表或选择用户设定")
    @app_commands.describe(index="用户设定序号（不填则列出所有用户设定）")
    async def cmd_user(self, interaction: discord.Interaction, index: int = -1):
        if not await self._check_whitelist(interaction):
            return
        await interaction.response.defer()

        personas = await core.fetch_personas()
        if not personas:
            await interaction.followup.send("获取用户设定列表失败。")
            return

        if index >= 0:
            if index >= len(personas):
                await interaction.followup.send(f"序号超出范围，共 {len(personas)} 个用户设定。")
                return

            p = personas[index]
            ok = await core.select_persona(p["avatar_id"])
            if not ok:
                await interaction.followup.send("切换用户设定失败。")
                return

            current = await core.get_current_persona()
            await interaction.followup.send(
                f"已切换用户设定为: **{current}** _(序号:{index})_"
            )
            return

        # 无参数：列出用户设定
        lines = [f"**用户设定列表 ({len(personas)}个)**"]
        for i, p in enumerate(personas):
            name = p.get("name", "?")
            desc = (p.get("description", "") or "[无描述]")[:80]
            lines.append(f"`{i}` — **{name}**")
            if desc:
                lines.append(f"> {desc}")

        lines.append(f"使用 `/user <序号>` 选择用户设定")

        msg = "\n".join(lines)
        if len(msg) > 2000:
            msg = msg[:1950] + "\n...(截断)"
        await interaction.followup.send(msg)


async def setup(bot):
    await bot.add_cog(STCommands(bot))
