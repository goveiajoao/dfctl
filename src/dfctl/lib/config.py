import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from rich.prompt import Confirm

from dfctl.lib.misc import take_value


@dataclass
class Config:
    path: Path

    dots_repo: None | str | Callable = field(
        default_factory=lambda: lambda: take_value(
            Confirm.ask("Do you have a dotfiles repo?"),
            lambda: input("Dotfiles repo: "),
            None,
        )
    )

    dots_path: str | Callable = field(
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

        for k, v in asdict(self).items():
            if k not in load_config and k != "path":
                load_config[k] = v()

            if k != "path":
                self[k] = load_config[k]

        with open(self.path, "w") as File:
            json.dump(load_config, File)
