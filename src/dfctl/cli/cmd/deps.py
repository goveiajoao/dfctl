import os

from dfctl.lib.parser import SubParser, SubParserSetupReturn
from dfctl.lib.target import TargetExtentions, TargetGroup


class CMD(SubParser):
    def func(self, args, config):
        groups: list[TargetGroup] = args.groups
        pass

    def setup(self, subparser):

        subparser.add_argument(
            "dep",
            help=f"ACTION:TYPE:DEP (e.g which:dfctl)",
        )

        mode_choices = ["group", "branch"]
        subparser.add_argument(
            "mode",
            metavar="mode",
            choices=mode_choices,
            help=f"{{{','.join(mode_choices)}}}",
        )

        subparser.add_argument("target", help="<mode> target")
        return SubParserSetupReturn(None, (True, True))

    def generate(self, subparsers, name, parents):
        return subparsers.add_parser(
            name, parents=parents, help="manage group|branch target dependencies"
        )
