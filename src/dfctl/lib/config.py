from dataclasses import dataclass, field

from rich.prompt import Confirm

from dfctl.lib.misc import take_value


@dataclass
class DefaultConfig:
    install: bool = field(init=False)
    dots_repo: None | str = field(init=False)
    dots_path: str = field(init=False)
    noconfirm: bool = field(init=False)
    autopull: bool = field(init=False)
    autopush: bool = field(init=False)

    def __post_init__(self):
        while True:
            self.install = Confirm.ask("Install dfctl?")
            self.dots_repo = take_value(
                Confirm.ask("Do you have a dotfiles repo?"),
                lambda: input("Dotfiles repo: "),
                None,
            )
            self.dots_path = take_value(
                Confirm.ask("Change dotfiles path? (~/.dotfiles)"),
                lambda: input("Path: "),
                "~/.dotfiles",
            )
            self.noconfirm = Confirm.ask("Enable noconfirm?")
            self.autopull = Confirm.ask("Enable autopull?") if self.dots_repo else False
            self.autopush = (
                Confirm.ask("Enable noconfirm?") if self.dots_repo else False
            )
            if Confirm.ask("\nConfirm Configuration?"):
                break
