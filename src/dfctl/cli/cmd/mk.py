import json
from pathlib import Path
from shutil import rmtree

from rich.console import Console

from dfctl.lib.misc import beautypath
from dfctl.lib.parser import SubParser, SubParserSetupReturn
from dfctl.lib.target import TargetExtentions, TargetGroup


class CMD(SubParser):
    def func(self, args, config):
        console = Console()
        groups: list[TargetGroup] = args.groups
        if len(groups) > 1:
            raise ValueError("just one group in target for mk")
        group = groups[0]
        group.path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(group.path.parent / "syms.json", "r") as File:
                syms: dict = json.load(File)
            for original, sym in syms.items():
                original = group.path.parent / original
                sym = Path(sym).expanduser()
                if original == group.instance:
                    raise ValueError(f"instance in '{str(group)}' already exists")
        except Exception:
            with open(group.path.parent / "syms.json", "w") as File:
                json.dump({}, File)

        with open(group.path.parent.parent / "dependencies.json", "w") as File:
            json.dump({}, File)
        with open(group.path.parent / "dependencies.json", "w") as File:
            json.dump({}, File)

        original: Path = Path(group.path).expanduser()
        sym: Path = Path(args.path).expanduser()

        if sym.is_dir():
            (sym / ".gitkeep").touch()
        sym.copy(original)
        original.unlink() if original.is_file() else rmtree(sym)

        with open(group.path.parent / "syms.json", "r") as File:
            syms: dict = json.load(File)
        with open(group.path.parent / "syms.json", "w") as File:
            json.dump({group.instance: str(beautypath(sym))} | syms, File)

        config.gitter.commit(f"Created '{str(group)}'")
        console.log(f"Created '{str(group)}'")

    def setup(self, subparser):
        subparser.add_argument(
            "target",
            help="""
            the instance to make (instances start at 0);
            E.G: "User@tmux:main/0" or just "tmux" """,
        )

        subparser.add_argument(
            "path",
            help="""
            the path where the instance links (folder or file);
            E.G: "~/.config/tmux" """,
        )

        return SubParserSetupReturn(TargetExtentions.INSTANCE, True, True)
