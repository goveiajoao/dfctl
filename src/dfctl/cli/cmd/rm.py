import json
from pathlib import Path
from shutil import rmtree

from rich.console import Console

from dfctl.lib.parser import SubParser, SubParserSetupReturn
from dfctl.lib.target import TargetExtentions, TargetGroup


class CMD(SubParser):
    def func(self, args, config):
        console = Console()
        groups: list[TargetGroup] = args.groups
        final_func = self.takebymode(
            TargetExtentions[args.mode.upper()], config, console
        )
        with console.status("[bold red] Removing..."):
            for group in groups:
                final_func(group)

    def takebymode(self, mode, config, console):

        def final(func):
            def __deco(*args, **kwargs):
                func(*args, **kwargs)
                msg = str(args[0])
                config.gitter.commit(f"Removed '{msg}'")
                console.log(f"[bold red]Removed[/] [bold blue]'{msg}'")

            return __deco

        @final
        def default(group: TargetGroup):
            rmtree(group.path)

        @final
        def instance(group: TargetGroup):
            syms = group.path.parent / "syms.json"
            instance = group.path

            with open(syms, "r") as File:
                jsonfile = json.load(File)
            with open(syms, "w") as File:
                json.dump(
                    {k: v for k, v in jsonfile.items() if k != str(group.instance)},
                    File,
                )
            instance.unlink() if instance.is_file() else rmtree(instance)

        match mode:
            case TargetExtentions.INSTANCE:
                return instance
            case _:
                return default

    def setup(self, subparser):
        mode_choices: list = [
            x.name.lower() for x in TargetExtentions if x.name != "LEVEL"
        ]
        subparser.add_argument(
            "mode",
            metavar="mode",
            choices=mode_choices,
            help=f"{{{','.join(mode_choices)}}}",
        )
        subparser.add_argument("target", help="<mode> target")
        return SubParserSetupReturn(None, True)
