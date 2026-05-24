import argparse, json 
from pathlib import Path
from typing import Callable
from dataclasses import dataclass, asdict, field
from shutil import rmtree

from lib.config import DefaultConfig
from lib.parser import SubParser
from lib.target import TargetExtentions, TargetGroup, get_target_groups, get_available_branchs, get_installed_branchs
from lib.misc import beautypath
from git import Repo, Remote 
from git.exc import InvalidGitRepositoryError
from rich.console import Console
from rich.prompt import Confirm
from rich import print




#
#       <Rich>
#
console = Console()
error_console = Console(stderr=True, style="bold red")



#
#       <Configs-Wrapper>
#
#   TODO: Seriously, just make it better...
CONFIG_FOLDER       :Path   =Path("~/.config/dfctl").expanduser()
CONFIG_FILE         :Path   =(CONFIG_FOLDER/"config.json")
if not CONFIG_FOLDER.exists(): CONFIG_FOLDER.mkdir()
if not CONFIG_FILE.exists():
    print(f"Creating config file in {CONFIG_FILE} with default config")
    DEFAULT_CONFIG = {k: v() if isinstance(v,Callable) else v for k,v in asdict(DefaultConfig()).items()}
    with open(CONFIG_FILE, 'w') as File:
        json.dump(DEFAULT_CONFIG,File,indent=4)
with open(CONFIG_FILE, 'r') as File:
    CONFIG  :dict   =json.load(File)
CONFIG_INSTALL      :bool   =CONFIG["install"]
CONFIG_DOTS_REPO    :str    =CONFIG["dots_repo"]
CONFIG_PATH_DOTS    :Path   =Path(CONFIG["dots_path"]).expanduser()
CONFIG_NOCONFIRM    :bool   =CONFIG["noconfirm"]
CONFIG_AUTOPULL     :bool   =CONFIG["autopull"]
CONFIG_AUTOPUSH     :bool   =CONFIG["autopush"]



#
#       <Repo>
#
#   TODO: Add clone when dont find the local repo
try: REPO    :Repo       =Repo(CONFIG_PATH_DOTS)
except InvalidGitRepositoryError:
    raise FileExistsError(f"Git repo dont exists in '{CONFIG_PATH_DOTS}'\nPlease create it or clone an existing one to start using dfctl")
except Exception as e: raise e
try: REPO_REMOTE    :Remote     =REPO.remote()
except: ValueError(f"Please create 'origin' remote in the repo inside '{CONFIG_PATH_DOTS}'")



#
#       <CLI>
#
#   TODO: This part REALLY need some work
#   may be a good idea separate the cli commands from the commands itself
#   so then i can call ls from uninstall, etc... (dont repeat code)
parser  :argparse.ArgumentParser    =argparse.ArgumentParser(
    prog="dfctl",
    description="Dotfiles CLI",
    color=False,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="target:\n"
    "  [LEVEL@]([-]GROUP[:BRANCH][/INSTANCE][...] | [-]GROUP[...][:BRANCH][/INSTANCE])\n"
    "  elements:\n"
    "    LEVEL:     the ground where all your groups will live\n"
    "    GROUP:     the dotfile group itself, like 'tmux'\n"
    "    BRANCH:    the branch of the group, like 'main', 'secound', ...\n"
    "    INSTANCE:  index of a file or folder of the dot\n"
    "  comment:\n"
    "    Syntax for Lists (...): [a,b,c,d,...]\n"
    "    '*' Can be used in LEVEL and GROUP to expand all elements\n"
    "    '-' Means Exclude/Negate\n"
    "    '<x> target' Means that it is a target that accept info until x, if passed info after x, it will error\n")
parser.add_argument("--noconfirm", action="store_true", help=f"skip confirmation prompts                ({CONFIG_NOCONFIRM})")
parser.add_argument("--autopull", action="store_false", help=f"auto pull before any local-repo action   ({CONFIG_AUTOPULL})")
parser.add_argument("--autopush", action="store_false", help=f"auto push after any local-repo action    ({CONFIG_AUTOPUSH})")
subparsers      :argparse._SubParsersAction     =parser.add_subparsers(required=True)
@dataclass
class SubParserFS():
    mode            :None|TargetExtentions  =None
    autopullsh      :bool                   =False
    invert_notfind  :bool                   =False
    target      :None|str               =None
    args            :argparse.Namespace     =field(default_factory=lambda :argparse.Namespace())
    ask             :str                    ="Are you sure you want to proceed"
    ask_end         :str                    ='?'
    rich_console    :Console                =console
    no_ask          :bool                   =False
    hard_mode       :bool                   =False
    def __post_init__(self):
        try:
            if not self.target: self.target = self.args.target
        except: pass
        try:
            if not self.mode and self.hard_mode: self.mode = TargetExtentions[self.args.mode.upper()]
            self.args.target_mode = self.mode
        except:
            raise ValueError("specify the mode")
    def __enter__(self):
        if self.mode: groups = get_target_groups(str(self.target), CONFIG_PATH_DOTS, self.mode, self.invert_notfind)
        else: raise ValueError("specify the mode")

        self.rich_console.log(f"[bold blue]Selected[/] {[f"{str(x)}" for x in groups]}")

        if (Confirm.ask(f"{self.ask}{self.ask_end}") if not self.args.noconfirm else True) or self.no_ask:
            return groups
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def __call__(self, func):
        def __deco(*args, **kwargs):
            self.args = args[1]
            self.hard_mode = True
            self.__post_init__()


            if args[1].autopull and self.autopullsh:
                with console.status("[bold green]Pulling from repo...") as status: REPO_REMOTE.pull()

            with self as groups:
                result      :None|Callable  =None
                if groups:
                    self.args.groups = groups
                    result = func(*args,**kwargs)

            if args[1].autopush and self.autopullsh:
                with console.status("[bold green]Pushing to repo...") as status: REPO_REMOTE.push()
            return result
        return __deco

def run_pass(subparser:argparse._SubParsersAction, **kwargs):
    def __deco(cls):
        cls(subparser.add_parser(cls.__name__, **kwargs))
        return cls
    return __deco


@run_pass(subparsers)
class install(SubParser):
    @SubParserFS(TargetExtentions.BRANCH)
    def func(self, args):
        groups :list[TargetGroup] =args.groups
        installed_branchs = get_installed_branchs(CONFIG_PATH_DOTS)

        _styles = {"WRITE":"[bold green]","ALREADY":"[bold orange1]","OVERWRITE":"[bold red]"}
        for group in groups:
            with console.status("[bold green] Installing..."):
                alreadyones = [x for x in installed_branchs if x.name == group.name and x.branch != group.branch]
                if len(alreadyones) > 0 and not args.force:
                    raise ValueError(f"could not install branch '{str(group)}'\nanother branch from the same group already installed '{str(alreadyones[0])}'\nfor branch overwriting, use the force argument (-f)")

                path    :Path   =group.path
                with open(path/"syms.json", 'r') as File:
                    syms   :dict   =json.load(File)

                installed   :list   =[]
                run_status  :str    =""
                for original,sym in syms.items():
                    sym         =Path(sym).expanduser()
                    original    =path/original
                    run_status       ="WRITE"
                    
                    while True:
                        try:
                            sym.symlink_to(path/original)
                            break
                        except FileExistsError:
                            if sym.is_symlink():
                                if sym.readlink() == original:
                                    run_status = "ALREADY"
                                    break
                                else:
                                    sym.unlink() if sym.is_file() else rmtree(sym)
                                    run_status = "OVERWRITE"         
                    installed.append((run_status,sym,original,_styles[run_status]))

                console.log(f"[bold green]Installed[/] [bold blue]'{str(group)}'")
                for x in installed: console.log(f"\t{x[3]}{f'{x[0]}[/]':<9} ({beautypath(x[1])} > {beautypath(x[2])})")


    def setup(self, subparser):
        subparser.add_argument("target",help="group target")
        subparser.add_argument("--force", "-f", action="store_true", help="use to overwrite already installed branchs")

@run_pass(subparsers)
class uninstall(SubParser):
    @SubParserFS(TargetExtentions.GROUP)
    def func(self, args):
        groups :list[TargetGroup] =args.groups
        installed_branchs = get_installed_branchs(CONFIG_PATH_DOTS)

        uninstall_branchs  :list[TargetGroup]   =[]
        for group in groups:
            alreadyones = [x for x in installed_branchs if x.name == group.name]
            if len(alreadyones) > 0:
                uninstall_branchs.append(alreadyones[0])

        for group in uninstall_branchs:
            with console.status("[bold red] Uninstalling..."):

                path    :Path   =group.path
                with open(path/"syms.json", 'r') as File:
                    syms   :dict   =json.load(File)

                uninstalled     :list   =[]
                for original,sym in syms.items():
                    sym         =Path(sym).expanduser()
                    original    =path/original
                    
                    try:
                        sym.unlink()
                    except FileNotFoundError:
                        pass
                    else:
                        uninstalled.append((sym,original))

                msg     :str    =str(group)
                if uninstalled:
                    console.log(f"[bold red]Uninstalled[/] [bold blue]'{msg}'")
                    for x in uninstalled: console.log(f"        ({beautypath(x[0])} > {beautypath(x[1])})")
                else:
                    console.log(f"[bold green]Already Uninstalled[/] [bold blue]'{msg}'")

    def setup(self, subparser):
        subparser.add_argument("target",help="group target")

@run_pass(subparsers)
class rm(SubParser):
    @SubParserFS(autopullsh=True)
    def func(self, args):
        groups :list[TargetGroup] =args.groups
        final_func = self.takebymode(args.target_mode)
        with console.status("[bold red] Removing..."):
            for group in groups:
                final_func(group)
    def takebymode(self, mode):
        def default(group:TargetGroup):
            msg = str(group)
            rmtree(group.path)

            REPO.git.add(all=True)
            REPO.index.commit(f"Removed '{msg}'")
            console.log(f"[bold red]Removed[/] [bold blue]'{msg}'")

        def instance(group):
            msg = str(group)

            syms        = group.path.parent/"syms.json"
            instance    = group.path

            #   HACK: FUNKY AS FUCK, opening 2 time just to overwrite, may be a function in json to overwrite
            with open(syms, 'r') as File:
                jsonfile = json.load(File)
            with open(syms, 'w') as File:
                json.dump({k:v for k,v in jsonfile.items() if k != str(group.instance)},File)
            instance.unlink() if instance.is_file() else rmtree(instance)

            REPO.git.add(all=True)
            REPO.index.commit(f"Removed '{msg}'")
            console.log(f"[bold red]Removed[/] [bold blue]'{msg}'")
            
        match mode:
            case TargetExtentions.INSTANCE:
                return instance
            case _:
                return default
    def setup(self, subparser):
        #   HACK: Funky as fuck the help prop in mode argument
        mode_choices    :list   =[x.name.lower() for x in TargetExtentions if x.name != "LEVEL"]
        subparser.add_argument("mode",metavar="mode",choices=mode_choices, help=f"{{{','.join(mode_choices)}}}")
        subparser.add_argument("target",help="<mode> target")

#   TODO:
@run_pass(subparsers)
class mk(SubParser):
    @SubParserFS(TargetExtentions.INSTANCE, True, True)
    def func(self, args):
        groups :list[TargetGroup] =args.groups
        if len(groups) > 1: raise ValueError("just one group in target for mk")
        group = groups[0]

        group.path.parent.mkdir(exist_ok=True)
    def setup(self, subparser):
        subparser.add_argument(
            "target",
            help="""
            the instance to make (instances start at 0);
            E.G: "User@tmux:main/0" or just "tmux" """)

        subparser.add_argument(
            "path",
            help="""
            the path where the instance links (folder or file);
            E.G: "~/.config/tmux" """)

# #   TODO:
# @run_pass(subparsers)
# class ls(SubParser):
#     def func(self, args):
#         print(args)
#     def setup(self, subparser):
#         pass
#
# #   TODO:
# @run_pass(subparsers)
# class checkhealth(SubParser):
#     def func(self, args):
#         print(args)
#     def setup(self, subparser):
#         pass
#
# #   TODO:
# @run_pass(subparsers)
# class update(SubParser):
#     def func(self, args):
#         print(args)
#     def setup(self, subparser):
#         pass


if __name__ == "__main__":
    args = parser.parse_args()
    args.func(args)
