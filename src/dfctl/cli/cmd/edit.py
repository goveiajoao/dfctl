import os

from dfctl.lib.parser import SubParser, SubParserSetupReturn
from dfctl.lib.target import TargetExtentions, TargetGroup


class CMD(SubParser):
    def func(self, args, config):
        groups: list[TargetGroup] = args.groups
        for group in groups:
            os.system(f"{config['editor']} {str(group.path)}")
            config.gitter.commit(f"edit on '{str(group)}'")

    def setup(self, subparser):
        subparser.add_argument("target", help="instance target")
        return SubParserSetupReturn(TargetExtentions.INSTANCE, (True, True), True, None)

    def generate(self, subparsers, name, parents):
        return subparsers.add_parser(name, parents=parents, help="edits an instance")
