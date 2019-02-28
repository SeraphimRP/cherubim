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
        else:
            await ctx.send(f"{ctx.author.mention} dabs.", file=img)

    @commands.command()
    async def slap(self, ctx, item: str=None):
        if item:
            await ctx.send(f"{ctx.author.mention} slaps {item} with a fish.")
        else:
            await ctx.send(f"{ctx.author.mention} didn't target anything and accidentally slapped themselves with a fish.")


    @commands.command()
    async def kill(self, ctx, item: str=None):
        if item:
            await ctx.send(f"{item} :gun:")
        else:
            await ctx.send("How am I supposed to kill nothing?!")