from dfctl.lib.git import pull
from dfctl.lib.parser import SubParser, SubParserSetupReturn


class CMD(SubParser):
    def func(self, args, config):
        config.gitter.pull()

    def setup(self, subparser):
        return SubParserSetupReturn(None)
