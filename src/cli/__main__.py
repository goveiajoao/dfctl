import argparse, json 
from pathlib import Path
from typing import Callable
from dataclasses import asdict
from shutil import rmtree
from lib.config import DefaultConfig
from lib.parser import SubParser
from lib.target import TargetExtentions, TargetGroup, get_target_groups
from lib.misc import ynquestion, beautypath
from git import Repo 
from git.exc import  InvalidGitRepositoryError


#
#       <Configs-Wrapper>
#
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
#       <Configs-Wrapper>
#
try: REPO    :Repo       =Repo(CONFIG_PATH_DOTS)
except InvalidGitRepositoryError:
    print(f"Git repo dont exists in '{CONFIG_PATH_DOTS}'")
except Exception as e: raise e



#
#       <CLI>
#
#   TODO: This part REALLY need some work
parser          :argparse.ArgumentParser        =argparse.ArgumentParser(prog="dfctl",
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
parser.add_argument("--autopull", action="store_false",  help=f"auto pull before any local-repo action   ({CONFIG_AUTOPULL})")
parser.add_argument("--autopush", action="store_false",  help=f"auto push after any local-repo action    ({CONFIG_AUTOPUSH})")
subparsers      :argparse._SubParsersAction     =parser.add_subparsers(required=True)
def run_pass(subparser:argparse._SubParsersAction):
    def __deco(cls):
        cls(subparser.add_parser(cls.__name__))
        return cls
    return __deco


@run_pass(subparsers)
class install(SubParser):
    def func(self, args):
        groups  = get_target_groups(args.target, range=TargetExtentions.GROUP, path=CONFIG_PATH_DOTS)
        print(f"selection: {[f"{x.level}@{x.name}" for x in groups]}")
        confirm = ynquestion(f"Warning: This will overwrite local configs. Proceed with installation?") if not args.noconfirm else True
        if confirm:
            for group in groups:
                path    :Path   =Path.joinpath(CONFIG_PATH_DOTS,group.level,group.name,group.branch)
                with open(path/"syms.json", 'r') as File:
                    syms   :dict   =json.load(File)

                print(f"Installing '{group.name}'...")
                installed   :list   =[]
                for original,sym in syms.items():
                    sym         =Path.expanduser(Path(sym))
                    original    =path/original
                    run_status       ="WRITE"
                    
                    while True:
                        try:
                            sym.symlink_to(path/original)
                            installed.append((run_status,sym,original))
                            break
                        except FileExistsError:
                            if sym.is_symlink():
                                if sym.readlink() == original:
                                    installed.append(("ALREADY",sym,original))
                                    break
                            sym.unlink() if sym.is_file() else rmtree(sym)
                            run_status = "OVERWRITE"         

                [print(f"    {f'{x[0]}:':<9} ({beautypath(x[1])} > {beautypath(x[2])})") for x in installed]
                print(f"    Install Completed")


    def setup(self, subparser):
        subparser.add_argument("target",help="group target")

@run_pass(subparsers)
class uninstall(SubParser):
    def func(self, args):
        groups  = get_target_groups(args.target, range=TargetExtentions.GROUP, path=CONFIG_PATH_DOTS)
        confirm = ynquestion(f"Are you sure you want to proceed with uninstalling?") if not args.noconfirm else True
        if confirm:
            for group in groups:
                path    :Path   =Path.joinpath(CONFIG_PATH_DOTS,group.level,group.name,group.branch)
                with open(path/"syms.json", 'r') as File:
                    syms   :dict   =json.load(File)

                print(f"Uninstalling '{group.name}'...")
                uninstalled     :list   =[]
                for original,sym in syms.items():
                    sym         =Path.expanduser(Path(sym))
                    original    =path/original
                    
                    try:
                        sym.unlink()
                    except FileNotFoundError:
                        pass
                    else:
                        uninstalled.append((sym,original))

                if uninstalled:
                    [print(f"    ({beautypath(x[0])} > {beautypath(x[1])})") for x in uninstalled]
                    print(f"    Uninstall Completed")
                else:
                    print(f"    Already Uninstalled")

    def setup(self, subparser):
        subparser.add_argument("target",help="group target")

#   TODO:
@run_pass(subparsers)
class rm(SubParser):
    def func(self, args):
        mode    :TargetExtentions   =TargetExtentions[args.mode.upper()]
        groups  :list[TargetGroup]  =get_target_groups(args.target, mode, path=CONFIG_PATH_DOTS)
        confirm = ynquestion(f"Are you sure you want to proceed with deletion?") if not args.noconfirm else True
        print(mode,groups)
    def setup(self, subparser):
        #   HACK: Funky as fuck the help prop in mode argument
        mode_choices    :list   =[x.name.lower() for x in TargetExtentions]
        subparser.add_argument("mode",metavar="mode",choices=mode_choices, help=f"{'{'}{','.join(mode_choices)}{'}'}")
        subparser.add_argument("target",help="<mode> target")
#   TODO:
@run_pass(subparsers)
class mk(SubParser):
    def func(self, args):
        print(args)
    def setup(self, subparser):
        subparser.add_argument(
            "instance",
            help="""
            the instance to make (instances start at 0);
            E.G: "User@tmux:main/0" or just "tmux" """)

        subparser.add_argument(
            "path",
            help="""
            the path where the instance links (folder or file);
            E.G: "~/.config/tmux" """)


if __name__ == "__main__":
    args = parser.parse_args()
    args.func(args)
