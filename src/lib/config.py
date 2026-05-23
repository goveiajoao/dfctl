from dataclasses import dataclass, field
from lib.misc import ynquestion, take_value

@dataclass
class DefaultConfig():
    install     :bool       =field(init=False)
    dots_repo   :None|str   =field(init=False)
    dots_path   :str        =field(init=False)
    noconfirm   :bool       =field(init=False)
    autopull    :bool       =field(init=False)
    autopush    :bool       =field(init=False)
    def __post_init__(self):
        while True:
            self.install    =ynquestion("Install dfctl?")
            self.dots_repo  =take_value(ynquestion("Do you have a dotfiles repo?"),lambda :input("Dotfiles repo: "),None)
            self.dots_path  =take_value(ynquestion("Change dotfiles path? (~/.dotfiles)",False),lambda :input("Path: "),"~/.dotfiles")
            self.noconfirm  =ynquestion("Enable noconfirm?",False)
            self.autopull   =ynquestion("Enable autopull?",True) if self.dots_repo else False
            self.autopush   =ynquestion("Enable noconfirm?",True) if self.dots_repo else False
            if ynquestion("\nConfirm Configuration?"): break
