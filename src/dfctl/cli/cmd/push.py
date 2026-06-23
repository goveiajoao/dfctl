from dfctl.lib.parser import SubParser, SubParserSetupReturn


class CMD(SubParser):
    def func(self, args, config):
        config.gitter.push()

    def setup(self, subparser):
        return SubParserSetupReturn(None)

    def generate(self, subparsers, name, parents):
        return subparsers.add_parser(name, parents=parents, help="push to remote")
