from .autoprayer import AutoPrayer
from .suggestionbox import SuggestionBox
from .custom_reactions import CustomReactions

from .fun import Fun

from .announce import Announce
from .restrict import Restrict

def setup(bot):
    bot.add_cog(AutoPrayer(bot))
    bot.add_cog(SuggestionBox(bot))
    bot.add_cog(CustomReactions())

    bot.add_cog(Fun())

    bot.add_cog(Announce(bot))
    bot.add_cog(Restrict(bot))
