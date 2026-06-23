import json
from pathlib import Path
from shutil import rmtree

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

        _styles = {
            "WRITE": "[bold green]",
            "ALREADY": "[bold orange1]",
            "OVERWRITE": "[bold red]",
        }

        for group in groups:
            with console.status("[bold green] Installing..."):
                alreadyones = [
                    x
                    for x in installed_branchs
                    if x.name == group.name and x.branch != group.branch
                ]
                if len(alreadyones) > 0 and not args.force:
                    raise ValueError(
                        f"could not install branch '{str(group)}'\nanother branch from the same group already installed '{str(alreadyones[0])}'\nfor branch overwriting, use the force argument (-f)"
                    )

                if group.check_deps()[0]:
                    path: Path = group.path
                    syms = group.get_syms()

                    installed: list = []
                    run_status: str = ""
                    for original, sym in syms.items():
                        sym = Path(sym).expanduser()
                        original = path / original
                        run_status = "WRITE"

                        while True:
                            try:
                                sym.symlink_to(original)
                                break
                            except FileExistsError:
                                if sym.is_symlink():
                                    if sym.readlink() == original:
                                        run_status = "ALREADY"
                                        break
                                    else:
                                        sym.unlink() if sym.is_file() else rmtree(sym)
                                        run_status = "OVERWRITE"
                        installed.append(
                            (run_status, sym, original, _styles[run_status])
                        )

                    console.log(f"[bold green]Installed[/] [bold blue]'{str(group)}'")
                    for x in installed:
                        console.log(f"\t{x[3]}{f'{x[0]}[/]':<9} ({beautypath(x[1])} > {
                            beautypath(x[2])})")
                else:
                    console.log(
                        f"[bold red] deps doesn't line up for group '{str(group)}'"
                    )

    def setup(self, subparser):
        subparser.add_argument("target", help="group target")
        subparser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="use to overwrite already installed branchs",
        )
        return SubParserSetupReturn(TargetExtentions.BRANCH)
