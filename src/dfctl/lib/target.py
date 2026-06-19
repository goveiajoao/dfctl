import json
import shutil
from dataclasses import dataclass
from enum import Enum
from json.encoder import ESCAPE
from pathlib import Path
from typing import Any, Literal

from dfctl.lib.misc import beautypath


class WholeNumber(int):

    def __new__(cls, value: int | str = 0):
        if not isinstance(value, int):
            value = int(value)
        if value < 0:
            raise ValueError("Value must be >= 0")
        return super().__new__(cls, value)


class TargetExtentions(Enum):
    # NAME = [Symbol,Default]
    LEVEL = ("@", "user")
    GROUP = None
    BRANCH = (":", "main")
    INSTANCE = ("/", WholeNumber(0))


@dataclass
class TargetGroup:
    name: str
    level: str
    branch: str
    instance: WholeNumber
    range: TargetExtentions
    path: Path

    def __str__(self):
        extentions: dict[str, tuple] = {
            x.name: x.value for x in TargetExtentions if x.value
        }
        symbols: list[str] = [v[0] for v in extentions.values()]
        match self.range:
            case TargetExtentions.LEVEL:
                return f"{self.level}{symbols[0]}"
            case TargetExtentions.GROUP:
                return f"{self.level}{symbols[0]}{self.name}"
            case TargetExtentions.BRANCH:
                return f"{self.level}{symbols[0]}{self.name}{symbols[1]}{self.branch}"
            case TargetExtentions.INSTANCE:
                return f"{self.level}{symbols[0]}{self.name}{symbols[1]}{self.branch}{symbols[2]}{self.instance}"

    def __post_init__(self):
        extentions: dict[str, tuple] = {
            x.name: x.value for x in TargetExtentions if x.value
        }
        symbols: list[str] = [v[0] for v in extentions.values()]

        string = str(self)
        for x in symbols:
            string = string.replace(x, "/")
        self.path = self.path / string

    def get_info_path(self) -> Path:
        match self.range:
            case TargetExtentions.GROUP:
                path = self.path / "info.json"
                return path
            case TargetExtentions.BRANCH:
                path = self.path.parent / "info.json"
                return path
            case TargetExtentions.INSTANCE:
                path = self.path.parent.parent / "info.json"
                return path
            case _:
                raise Exception("invalid target range")

    def get_info(self) -> dict:
        path = self.get_info_path()
        if not path.exists():
            with open(path, "w") as File:
                json.dump({"syms": {}, "deps": {"*": {}}}, File, indent=4)
        with open(path, "r") as File:
            return json.load(File)

    def get_syms(self) -> dict:
        info = self.get_info()
        return info["syms"]

    def add_syms(self, original: Path) -> None:
        info_path = self.get_info_path()
        info = self.get_info()
        syms = self.get_syms()

        instance = self.instance
        if str(instance) in list(syms.keys()) and instance != 0:
            raise ValueError("instance already exists")
        if original in list(syms.values()) and instance == 0:
            instance = {v: k for k, v in syms.items()}[original]

        syms[str(instance)] = str(beautypath(original))
        info["syms"] = syms
        with open(info_path, "w") as File:
            json.dump(info, File, indent=4)

    def rm_syms(self, index: int) -> None:
        info_path = self.get_info_path()
        info = self.get_info()
        syms = self.get_syms()

        syms.pop(str(index))
        info["syms"] = syms

        with open(info_path, "w") as File:
            json.dump(info, File, indent=4)

    def get_deps(self):
        info = self.get_info()
        deps = info["deps"]
        match self.range:
            case TargetExtentions.GROUP:
                return deps["*"]
            case TargetExtentions.BRANCH:
                return deps.get(self.branch, {}) | deps["*"]
            case _:
                raise ValueError("invalid range")

    def check_deps(self):
        deps = self.get_deps()
        check_result = {k: [True for i in v] for k, v in deps.items()}

        for k, v in deps.items():
            if not isinstance(v, list):
                raise Exception(f"deps not right in {str(self)}")
            match k:
                case "which":
                    for _, x in enumerate(v):
                        if shutil.which(x) is None:
                            check_result["which"][_] = False
                case "exists":
                    for _, x in enumerate(v):
                        if not Path(x).expanduser().exists():
                            check_result["exists"][_] = False
        return (
            all([y for x in check_result.values() for y in x]),
            {k: all([x for x in v]) for k, v in check_result.items()},
            check_result,
        )


def sudo_level_in_argv(argv: list, sudo_levels=["system"]):
    for level in sudo_levels:
        if f"{level}{TargetExtentions.LEVEL.value[0]}" in "".join(argv):
            return True
    return False


def get_target_groups(
    raw: str,
    path: Path,
    range: TargetExtentions,
    notfound: bool = True,
):

    raw_list: str = raw[raw.find("[") : raw.rfind("]") + 1]
    raw_nolist: str = raw.replace(raw_list, "")
    available_levels: list = [x for x in next(path.walk())[1] if x[0] != "."]
    available_levelsg: dict = {
        level: next((path / level).walk())[1] for level in available_levels
    }

    extentions: dict[str, tuple] = {
        x.name: x.value for x in TargetExtentions if x.value
    }
    names: list[str] = [k for k in extentions.keys()]
    range_ind: int = (
        next(_ for _, x in enumerate(names) if x == range.name)
        if range.name != "GROUP"
        else 0
    )
    excludes_names: list[str] = [k for k in names[range_ind + 1 :]]
    symbols: list[str] = [v[0] for v in extentions.values()]
    defaults: list[Any] = [v[1] for v in extentions.values()]
    no_instance_passed = False

    for _, name in enumerate(names):
        symbol = symbols[_]
        default = defaults[_]
        match raw_nolist.count(symbol):
            case 0:
                match name:
                    case TargetExtentions.LEVEL.name:
                        raw = f"{default}{symbol}{raw}"
                    case TargetExtentions.BRANCH.name:
                        raw = f"{raw}{symbol}{default}"
                        if raw.count(symbols[_ + 1]) != 0:
                            raw = f"{raw[:raw.find(symbols[_+1])]}{symbol}{default}{raw[raw.find(symbols[_+1]):]}"
                    case TargetExtentions.INSTANCE.name:
                        raw = f"{raw}{symbol}{default}"
                        no_instance_passed = True
            case 1:
                if name in excludes_names:
                    raise ValueError(f"{name} cannot be passed in range {range.name}")
            case _:
                raise ValueError(f"{name} passed more than once")

    input_level: str = raw[: raw.find(symbols[0])]
    levels: list = [input_level] if input_level != "*" else available_levels
    if input_level not in available_levels and input_level != "*":
        raise ValueError(
            f"level '{input_level}' does not exist, available ones: {available_levels}"
        )
    if symbols[0] in raw_list:
        raise ValueError("set the level outside the list")

    groups: None | list = (
        raw_list[1 : len(raw_list) - 1].replace(" ", "").split(",")
        if raw_list
        else [raw[raw.find(symbols[0]) + 1 : raw.rfind(symbols[1])]]
    )
    if "*" in groups:
        if groups[0] != "*":
            raise ValueError("please use * inside lists as first element")
        groups = groups[1:] + [
            x for k, v in available_levelsg.items() for x in v if k in levels
        ]

    general_branch: str = raw[raw.rfind(symbols[1]) + 1 : raw.rfind(symbols[2])]
    general_instance: str = raw[raw.rfind(symbols[2]) + 1 :]

    results: list[TargetGroup] = []
    result_remove_list: list[str] = []
    for group in groups:
        level: str = input_level
        name: str = group[
            : [
                group.find(symbols[ind]) if group.count(symbols[ind]) else len(group)
                for ind in [1, 2]
            ][0]
        ]
        mode: Literal["add", "remove"] = "add" if name[0] != "-" else "remove"
        name = name[1:] if name[0] == "-" else name

        try:
            level = next(
                k
                for k, v in {
                    k: v for k, v in available_levelsg.items() if k in levels
                }.items()
                if name in v
            )
        except Exception:
            if notfound:
                raise ValueError(f"group '{name}' does not exist in levels {levels}")

        branch: str = (
            group[
                group.find(symbols[1]) + 1 if group.count(symbols[1]) else 0 : (
                    group.find(symbols[2]) if group.count(symbols[2]) else len(group)
                )
            ]
            if group.count(symbols[1])
            else general_branch
        )
        if notfound and branch not in next((path / level / name).walk())[1]:
            raise ValueError(
                f"branch '{branch}' does not exist in group '{level}{symbols[0]}{name}'"
            )

        instance: WholeNumber = (
            WholeNumber(group[group.find(symbols[2]) + 1 :])
            if group.count(symbols[2])
            else WholeNumber(general_instance)
        )
        if notfound and str(instance) not in [
            y for x in next((path / level / name / branch).walk())[1:] for y in x
        ]:
            raise ValueError(
                f"instance '{instance}' does not exist in branch '{level}{symbols[0]}{name}{symbols[1]}{branch}'"
            )

        match mode:
            case "add":
                do_result = lambda: TargetGroup(
                    name, level, branch, instance, range, path
                )
                prov_result = do_result()
                match prov_result.range:
                    case TargetExtentions.INSTANCE:
                        if not notfound:
                            prov_result.path.parent.mkdir(parents=True, exist_ok=True)

                            syms = prov_result.get_syms()

                            if str(prov_result.instance) in list(syms.keys()):
                                if no_instance_passed:
                                    instance = WholeNumber(len(syms.keys()))
                                else:
                                    raise ValueError(
                                        f"instance {str(prov_result)} already exists"
                                    )

                results.append(do_result())
            case "remove":
                result_remove_list.append(name)

    results = [x for x in results if x.name not in result_remove_list]
    return results


def get_available_groups(path: Path) -> list[TargetGroup]:
    return get_target_groups("*@*", path, TargetExtentions.GROUP)


def get_available_branchs(path: Path) -> list[TargetGroup]:
    available_groups = get_available_groups(path)
    return [
        TargetGroup(x.name, x.level, y, x.instance, TargetExtentions.BRANCH, path)
        for x in available_groups
        for y in next(x.path.walk())[1]
    ]


def get_installed_branchs(path: Path) -> list[TargetGroup]:
    available_branchs = get_available_branchs(path)
    installed_branchs: list = []
    for group in available_branchs:
        syms = group.get_syms()

        for original, sym in syms.items():
            original = Path().joinpath(group.path, original)
            sym = Path(sym).expanduser()

            if sym.exists() and sym.is_symlink() and sym.readlink() == original:
                installed_branchs.append(group)
                break
    return installed_branchs
