from redbot.core import commands
import discord
import os

dir_path = os.path.dirname(__file__)

class Fun(commands.Cog):
    @commands.command()
    async def dab(self, ctx, item: str=None):
        img = discord.File(f"{dir_path}/horsedabbing.jpg")

        if item:
            await ctx.send(f"{ctx.author.mention} dabs on {item}.", file=img)

    @commands.command()
    async def slap(self, ctx, user: discord.Member=None, item: str=None):
        if item:
            await ctx.send(f"{ctx.author.mention} slaps {item} with a fish.")

    @commands.command()
    async def kill(self, ctx, item: str=None):
        if item:
            await ctx.send(f"{item} :gun:")
        else:
            await ctx.send("I can't kill thin air!")