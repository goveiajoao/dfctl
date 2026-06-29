from argparse import RawDescriptionHelpFormatter

from dfctl.lib.parser import SubParser, SubParserSetupReturn
from dfctl.lib.target import TargetGroup


class CMD(SubParser):
    def func(self, args, config):
        groups: list[TargetGroup] = args.groups
        pass

    def setup(self, subparser):

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
            name,
            parents=parents,
            formatter_class=RawDescriptionHelpFormatter,
            help="manage group|branch target dependencies",
            epilog="action:\n"
            "  ACTION:TYPE:DEP\n"
            "                                   ",
        )
