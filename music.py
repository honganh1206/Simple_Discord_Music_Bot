import discord
from discord.ext import commands
from source import Source, YTDLError


async def in_voice_channel(ctx):
    """Checks that the command sender is in the same voice channel as the bot."""
    voice = ctx.author.voice
    bot_voice = ctx.guild.voice_client
    if voice and bot_voice and voice.channel and bot_voice.channel and voice.channel == bot_voice.channel:
        return True
    else:
        raise commands.CommandError(
            "You need to be in the channel to do that.")


class MusicBot(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
    
    @commands.command()
    async def join(self, ctx):
        """ 
        Join a voice channel

        discord.py commands do not by default pass the context (pass_context=False)
        using ctx here means pass_context=True

        ctx(Context) is not created manually and is passed around to commands as the FIRST parameter
        """ 
        if not ctx.message.author.voice:
            await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
            return
        else:
            channel = ctx.message.author.voice.channel

        await channel.connect()

    @commands.command()
    async def yt(self,ctx,*,search):
        """ Play a file on youtube but not downloading it"""
        async with ctx.typing():
            try: 
                player = await Source.from_source(ctx, search,loop=self.bot.loop)   # loop the song
                ctx.voice_client.play(player)
                await ctx.send("", embed=player.get_embed())
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            
        
    @commands.command()
    async def stream(self,ctx,*,search):
        """ Play a file on youtube but not downloading it"""
        try: 
            player = await Source.from_source(ctx, search,loop=self.bot.loop,stream = True)   # loop the song
            ctx.voice_client.play(player)
            await ctx.send("", embed=player.get_embed())
        except YTDLError as e:
            await ctx.send('An error occurred while processing this request: {}'.format(str(e)))

    @commands.command()
    async def volume(self,ctx,volume:int):
        """ Change volume to an int value by 100 """
        if ctx.voice_client is None:
            return await ctx.send(f'{ctx.name} is not connected to the voice channel')

        ctx.voice_client.source.volume = volume/100
        await ctx.send(f'Changed volume to {volume}%')

    @commands.command()
    async def pause(self,ctx):
        """Pause the currently playing song"""
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            voice_client.pause()
            await ctx.message.add_reaction('⏯')
        else:
            await ctx.send(f"{self.bot.user} is not playing anything at the moment.")

    @commands.command()
    async def resume(self,ctx):
        voice_client = ctx.message.guild.voice_client
        if not voice_client.is_playing():
            voice_client.resume()
            await ctx.message.add_reaction('⏭')
        else:
            await ctx.send(f"{self.bot.user} was not playing anything before this. Use play_song command")
        
    @commands.command()
    async def leave(self,ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
        else:
            await ctx.send(f"{self.bot.user} is not in the voice channel.")
    
    @yt.before_invoke
    @stream.before_invoke   # stacked decorator
    
    async def ensure_voice(self,ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author is not connected to a voice channel")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

