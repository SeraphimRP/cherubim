from .autoprayer import AutoPrayer
from .suggestionbox import SuggestionBox
from .custom_reactions import CustomReactions

from .fun import Fun
from .standards import Standards

from .announce import Announce
from .restrict import Restrict

from .msgvote import MsgVote
from .reactpoll import ReactPoll
from .errorlogs import ErrorLogs

from .reactrole import ReactRole

def setup(bot):
    bot.add_cog(AutoPrayer(bot))
    bot.add_cog(SuggestionBox(bot))
    bot.add_cog(CustomReactions())

    bot.add_cog(Fun())
    bot.add_cog(Standards(bot))

    bot.add_cog(Announce(bot))
    bot.add_cog(Restrict(bot))
    
    bot.add_cog(MsgVote(bot))
    bot.add_cog(ReactPoll(bot))
    bot.add_cog(ErrorLogs())

    bot.add_cog(ReactRole(bot))
