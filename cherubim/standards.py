from redbot.core import commands
import discord
import asyncio
import os

dir_path = os.path.dirname(__file__)

class Standards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def on_member_join(self, member):
        channel = self.bot.get_channel(538525137784406018)
        msg = await channel.send(f"{member.mention} ^")

        staff_channel = self.bot.get_channel(538837260229935124)
        await staff_channel.send(f"{member.mention} has joined.")

        asyncio.sleep(30)

        msg.delete()

    async def on_member_remove(self, member):
        staff_channel = self.bot.get_channel(538837260229935124)
        await staff_channel.send(f"{member.mention} has left.")