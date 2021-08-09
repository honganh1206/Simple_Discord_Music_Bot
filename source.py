

import youtube_dl,discord,asyncio,functools
from discord.ext import commands

youtube_dl.utils.bug_reports_message = lambda: ''

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
    'options': '-vn'
}

class YTDLError(Exception):
    pass


 # child class of discord
class Source(discord.PCMVolumeTransformer):      # control the volume

    ytld_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
    # 'extract_flat": "in_playlist'
}



    ytdl = youtube_dl.YoutubeDL(ytld_format_options)    # to interact with youtube

    def __init__(self, ctx:commands.Context, source: discord.FFmpegPCMAudio, *,data:dict,volume:float = 0.3):    # auto volume = 0.3
        super().__init__(source,volume)

        self.data = data
        self.requester = ctx.author
        self.channel = ctx.channel

        self.title = data.get('title')
        self.url = data.get('webpage_url')
        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.thumbnail = data.get('thumbnail')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.stream_url = data.get('url')

    def __str__(self):
        # 0 stands for self here
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    # cls stands for class here
    async def from_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None, stream=False):
        """ 
        Search from user's input (as a string) and return the filename of the video 
        Steps: get API => get entries (contains webpage url) => get url separately (correct?)

        """
        # no current event loop + no set_event_loop() has been called => new event loop and set this as the current one
        loop = loop or asyncio.get_event_loop() 
        #partial() make extract_info use one-argument callable
        partial = functools.partial(cls.ytdl.extract_info,search,download = False, process = False)

        # suspend func with await and then allow extract_info to run in executor (run int their own thread)

        data = await loop.run_in_executor(None, partial) 
        if data is None:
            raise YTDLError("The bot couldn\'t find anything that matches '{}' ".format(search))

        # get API => get entries (contains webpage url) => get url separately 

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None

            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

                if process_info is None:
                    raise YTDLError("The bot couldn\'t find anything that matches '{}' ".format(search))

        url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info,url,download = False)
        process_info = await loop.run_in_executor(None, partial)
        
        if process_info is None:
            raise YTDLError("The bot couldn\'t fetch'{}' ".format(url))


        if 'entries' not in process_info:
            info = process_info
        else:
            info = None
            while info is None:
                try:
                    # pop out the first url in the entries
                    info = process_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError("The bot couldn\'t retrieve any matches for '{}' ".format(url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        # returns a tuple containing the quotient  and the remainder
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)


    def get_embed(self):
        embed = (discord.Embed(title='Now playing',
                               description='```css\n{0.title}\n```'.format(self),
                               color=discord.Color.blurple())
                 .add_field(name='Duration', value=self.duration)
                 .add_field(name='Requested by', value=self.requester.mention)
                 .add_field(name='Uploader', value='[{0.uploader}]({0.uploader_url})'.format(self))
                 .add_field(name='URL', value='[Click]({0.url})'.format(self))
                 .set_thumbnail(url=self.thumbnail))

        return embed



