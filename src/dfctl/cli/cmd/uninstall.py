import json
from pathlib import Path

from rich.console import Console

from dfctl.lib.misc import beautypath
from dfctl.lib.parser import SubParser, SubParserSetupReturn
from dfctl.lib.target import TargetExtentions, TargetGroup, get_installed_branchs


class CMD(SubParser):
    def func(self, args, config):
        console = Console()
        dots_path: Path = config["dots_path"]
        groups: list[TargetGroup] = args.groups
        installed_branchs = get_installed_branchs(dots_path)

        uninstall_branchs: list[TargetGroup] = []
        for group in groups:
            alreadyones = [x for x in installed_branchs if x.name == group.name]
            if len(alreadyones) > 0:
                uninstall_branchs.append(alreadyones[0])

        for group in uninstall_branchs:
            with console.status("[bold red] Uninstalling..."):

                path: Path = group.path
                with open(path / "syms.json", "r") as File:
                    syms: dict = json.load(File)

                uninstalled: list = []
                for original, sym in syms.items():
                    sym = Path(sym).expanduser()
                    original = path / original

                    try:
                        sym.unlink()
                    except FileNotFoundError:
                        pass
                    else:
                        uninstalled.append((sym, original))

                msg: str = str(group)
                if uninstalled:
                    console.log(f"[bold red]Uninstalled[/] [bold blue]'{msg}'")
                    for x in uninstalled:
                        console.log(
                            f"        ({beautypath(x[0])} > {beautypath(x[1])})"
                        )
                else:
                    console.log(
                        f"[bold green]Already Uninstalled[/] [bold blue]'{msg}'"
                    )

    def setup(self, subparser):
        subparser.add_argument("target", help="group target")
        return SubParserSetupReturn(TargetExtentions.GROUP)
