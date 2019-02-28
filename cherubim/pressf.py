import discord
from redbot.core import commands
import asyncio

class PressF(commands.Cog):
    """You can now pay repect to a person"""

    def __init__(self, bot):
        self.bot = bot
        self.messager = {}
        self.messagem = {}

    @commands.command(pass_context=True, no_pm=True)
    async def pressf(self, ctx, user: discord.User=None):
        """Pay Respects by pressing f"""

        author = ctx.author
        channel = ctx.channel

        if channel.id in self.messager or channel.id in self.messagem:
            return await ctx.send("Oops! I'm still paying respects in this channel, you'll have to wait until I'm done.")
        
        def check_message(m):
            return (m.author == author and m.channel == channel)

        if user:
            answer = user.display_name
        else:
            await ctx.send("What do you want to pay respects to?")
            message = await self.bot.wait_for("message", check=check_message, timeout=120.0)

            if message is None:
                return await ctx.send("You took too long to reply.")
        
            answer = message.content
        
        msg = f"Everyone, let's pay respects to **{answer}**! Press the F reaction on this message to pay respects."

        message = await ctx.send(msg)

        try:
            await message.add_reaction("\U0001f1eb")
            self.messager[channel.id] = []
            react = True
        except:
            self.messagem[channel.id] = []
            react = False
            await message.edit(content=f"Everyone, let's pay respects to **{answer}**! Press the F reaction on the this message to pay respects.")

            def check(m):
                return m.channel == ctx.channel

            await self.bot.wait_for("message", check=check)

        await asyncio.sleep(120)
        await message.delete()

        if react:
            amount = len(self.messager[channel.id])
        else:
            amount = len(self.messagem[channel.id])

        amount_of_people = "person has" if str(amount) == "1" else "people have"
        await channel.send(f"**{amount}** {amount_of_people} paid respects to **{answer}**.")
        
        if react:
            del self.messager[channel.id]
        else:
            del self.messagem[channel.id]
    
    async def on_reaction_add(self, reaction, user):
        message = reaction.message
        channel = message.channel

        if user.id == self.bot.user.id:
            return
        if channel.id not in self.messager:
            return    
        if user.id not in self.messager[channel.id]:
            if str(reaction.emoji) == "\U0001f1eb": 
                await channel.send(f"**{user.mention}** has paid respects.")
                self.messager[channel.id].append(user.id)

    async def on_message(self, message):
        channel = message.channel
        user = message.author

        if channel.id not in self.messagem:
            return    
        if user.id not in self.messagem[channel.id]:
            if message.content.lower() == "f":
                await ctx.send("**{user.mention}** has paid respects.")
                self.messagem[channel.id].append(user.id)
