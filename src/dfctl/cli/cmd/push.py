from dfctl.lib.git import push
from dfctl.lib.parser import SubParser, SubParserSetupReturn


class CMD(SubParser):
    def func(self, args, config):
        config.gitter.push()

    def setup(self, subparser):
        return SubParserSetupReturn(None)
