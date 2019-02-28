import asyncio
import os
from datetime import datetime

import discord

from redbot.core import commands, checks, Config

class AutoPrayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=(3322665 + 2))

        default_guild = {
            "channels_enabled": [],
            "duration": 300,
            "threshold": 3,
            "bot": False,
            "pray": "🙏"
        }

        self.config.register_guild(**default_guild)

    @commands.group(name="autoprayer", pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_guild=True)
    async def autoprayer(self, ctx):
        """autoprayer cog settings"""

        #if ctx.invoked_subcommand is None:
        #    await ctx.send_help()
        pass

    @autoprayer.command(name="on", pass_context=True, no_pm=True)
    async def _autoprayer_on(self, ctx):
        """Turn on autoprayer mode in the current channel"""
        guild_group = self.config.guild(ctx.guild)

        async with guild_group.channels_enabled() as channels_enabled:
            channel = ctx.message.channel
            if channel.id in channels_enabled:
                await ctx.send("AutoPrayer is already on in this channel.")
            else:
                channels_enabled.append(channel.id)

                await ctx.send("AutoPrayer is now on in this channel.")

    @autoprayer.command(name="off", pass_context=True, no_pm=True)
    async def _autoprayer_off(self, ctx):
        """Turn off autoprayer mode in the current channel"""
        guild_group = self.config.guild(ctx.guild)

        async with guild_group.channels_enabled() as channels_enabled:
            channel = ctx.message.channel
            if channel.id not in channels_enabled:
                await ctx.send("AutoPrayer is already off in this channel.")
            else:
                channels_enabled.remove(channel.id)

                await ctx.send("AutoPrayer is now off in this channel.")

    @autoprayer.command(name="bot", pass_context=True, no_pm=True)
    async def _autoprayer_bot(self, ctx):
        """Turn on/off reactions to bot's own messages"""
        await self.config.guild(ctx.guild).bot.set(not await self.config.guild(ctx.guild).bot())
        
        if await self.config.guild(ctx.guild).bot():
            await ctx.send("Reactions to bot messages turned on.")
        else:
            await ctx.send("Reactions to bot messages turned off.")

    def is_command(self, msg):
        return msg.content.startswith("--")

    async def on_message(self, message):
        try:
            guild_group = self.config.guild(message.guild)

            async with guild_group.channels_enabled() as channels_enabled:
                if message.channel.id not in channels_enabled:
                    return
                if message.author == self.bot.user and not guild_group.bot():
                    return
                if self.is_command(message):
                    return
                
                try:
                    pray = await guild_group.get_raw("pray")
                    await message.add_reaction(pray)
                except discord.errors.HTTPException:
                    # Implement a non-spammy way to alert users in future
                    pass
        except:
            pass