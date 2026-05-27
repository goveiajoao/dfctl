from dfctl.lib.git import pull
from dfctl.lib.parser import SubParser, SubParserSetupReturn


class CMD(SubParser):
    def func(self, args, config):
        pull(config.remote)

    def setup(self, subparser):
        return SubParserSetupReturn(None)
