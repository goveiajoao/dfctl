import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from rich.prompt import Confirm

from dfctl.lib.git import Gitter
from dfctl.lib.misc import take_value


@dataclass
class Config:
    __exclude = ["__exclude", "path", "uid", "gid", "pcomm", "gitter"]
    path: Path
    uid: int
    gid: int
    pcomm: Any
    gitter: Gitter = field(init=False)

    dots_repo: None | str | Callable = field(
        default_factory=lambda: lambda: take_value(
            Confirm.ask("Do you have a dotfiles repo?"),
            lambda: input("Dotfiles repo: "),
            None,
        )
    )

    dots_path: str | Path | Callable = field(
        default_factory=lambda: lambda: take_value(
            Confirm.ask("Change dotfiles path? (~/.dotfiles)"),
            lambda: input("Path: "),
            "~/.dotfiles",
        )
    )

    noconfirm: bool | Callable = field(
        default_factory=lambda: lambda: Confirm.ask("Enable noconfirm?")
    )

    autopull: bool | Callable = field(
        default_factory=lambda: lambda: Confirm.ask("Enable autopull?")
    )

    autopush: bool | Callable = field(
        default_factory=lambda: lambda: Confirm.ask("Enable autopush?")
    )

    def __setitem__(self, name, value):
        super().__setattr__(name, value)

    def __getitem__(self, name):
        return self.__getattribute__(name)

    def __post_init__(self):
        if not self.path.exists():
            with open(self.path, "w") as File:
                json.dump({}, File)

        with open(self.path, "r") as File:
            load_config: dict = json.load(File)
        for k, v in vars(self).items():
            if k not in load_config and k not in self.__exclude:
                if isinstance(v, Callable):
                    load_config[k] = v()

            if k not in self.__exclude:
                self[k] = load_config[k]
        with open(self.path, "w") as File:
            json.dump(load_config, File)

        if not isinstance(self["dots_path"], Path):
            self["dots_path"] = Path(self["dots_path"]).expanduser()

        self.gitter = Gitter(self.pcomm)
        # self.gitter.dowait()
