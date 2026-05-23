import argparse, json, subprocess
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Any, Literal, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from shutil import rmtree



class WholeNumber(int):
    def __new__(cls,value:int|str=0):
        if not isinstance(value, int):  value=int(value)
        if value < 0:                   raise ValueError("Value must be >= 0")
        return super().__new__(cls,value)

class TargetExtentions(Enum):
    #NAME       =[Symbol,Default]
    LEVEL       =('@',"User")
    GROUP       =None
    BRANCH      =(':',"main")
    INSTANCE    =('/',WholeNumber(0))

@dataclass
class TargetGroup():
    name        :str
    level       :str
    branch      :str
    instance    :WholeNumber

#   NOTE: I would make that class way nicer if this would be a multifile project
#   this class is NOT modular, but for the porpuse of this application, it works...
def get_target_groups(
    raw             :str,
    range           :TargetExtentions,
    path            :Path):

    raw_list            :str            =raw[raw.find('['):raw.rfind(']')+1]
    raw_nolist          :str            =raw.replace(raw_list,'')
    available_levels    :list           =next(path.walk())[1]
    available_levelsg   :dict           ={level:next((path/level).walk())[1] for level in available_levels}

    extentions          :dict[str,tuple]    ={x.name:x.value for x in TargetExtentions if x.value}
    names               :list[str]          =[k for k in extentions.keys()]
    range_ind           :int                =next(_ for _,x in enumerate(names) if x == range.name) if range.name != "GROUP" else 0
    excludes_names      :list[str]          =[k for k in names[range_ind+1:]]
    symbols             :list[str]          =[v[0] for v in extentions.values()]
    defaults            :list[Any]          =[v[1] for v in extentions.values()]

    for _,name in enumerate(names):
        symbol  = symbols[_]
        default = defaults[_]
        match raw_nolist.count(symbol):
            case 0:
                match name:
                    case TargetExtentions.LEVEL.name:
                        raw = f"{default}{symbol}{raw}"
                    case TargetExtentions.BRANCH.name:
                        raw = f"{raw}{symbol}{default}"
                        if raw.count(symbols[_+1]) != 0: raw = f"{raw[:raw.find(symbols[_+1])]}{symbol}{default}{raw[raw.find(symbols[_+1]):]}"
                    case TargetExtentions.INSTANCE.name:
                        raw = f"{raw}{symbol}{default}"
            case 1:
                if name in excludes_names: raise ValueError(f"{name} cannot be passed in range {range.name}")
            case _:
                raise ValueError(f"{name} passed more than once")

    input_level         :str            =raw[:raw.find(symbols[0])]
    levels              :list           =[input_level] if input_level != '*' else available_levels
    if input_level not in available_levels and input_level != '*':
        raise ValueError(f"level '{input_level}' does not exist, available ones: {available_levels}")

    groups              :None|list      =raw_list[1:len(raw_list)-1].replace(' ','').split(',') if raw_list else [raw[raw.find(symbols[0])+1:raw.rfind(symbols[1])]]
    if '*' in groups:
        if groups[0] != '*': raise ValueError("please use * inside lists as first element")
        groups = groups[1:]+[x for k,v in available_levelsg.items() for x in v if k in levels]

    general_branch      :str            =raw[raw.rfind(symbols[1])+1:raw.rfind(symbols[2])]
    general_instance    :str            =raw[raw.rfind(symbols[2])+1:]

    result              :list[TargetGroup]  =[]
    result_remove_list  :list[str]          =[]
    for group in groups:
        level       :str            =defaults[0]
        name        :str            =group[:[group.find(symbols[ind]) if group.count(symbols[ind]) else len(group) for ind in [1,2]][0]]
        mode        :Literal["add","remove"]    ="add" if name[0] != '-' else "remove"; name = name[1:] if name[0] == '-' else name
        try: level = next(k for k,v in {k:v for k,v in available_levelsg.items() if k in levels}.items() if name in v)
        except: raise ValueError(f"group '{name}' does not exist in levels {levels}")

        branch      :str            =group[group.find(symbols[1])+1 if group.count(symbols[1]) else 0 :
                                   group.find(symbols[2]) if group.count(symbols[2]) else len(group)] if group.count(symbols[1]) else general_branch
        if branch not in next((path/level/name).walk())[1]:
            raise ValueError(f"branch '{branch}' does not exist in group '{level}@{name}'")
        
        instance    :WholeNumber    =WholeNumber(group[group.find(symbols[2])+1:]) if group.count(symbols[2]) else WholeNumber(general_instance)
        if str(instance) not in [y for x in next((path/level/name/branch).walk())[1:] for y in x]:
            raise ValueError(f"instance '{instance}' does not exist in branch '{level}@{name}:{branch}'")

        match mode:
            case "add":
                result.append(TargetGroup(name,level,branch,instance))
            case "remove":
                result_remove_list.append(name)
    result = [x for x in result if x.name not in result_remove_list]
    return result
