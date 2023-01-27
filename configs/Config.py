from pathlib import Path
from typing import Any, Optional, Union
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError

class Config():
    def __init__(self, plugin_name: str, *args, **kwargs):
        """
        Parameters
        ---
        plugin_name: Config类将会在`configs`文件夹中的`plugin_name`对应的文件夹中寻找`configs.yml`
        如果配置文件有多个，请通过**kwargs通过列表的形式以`config_files_name`的键值传入

        Return
        ---
        Config类，如为默认配置文件，则直接返回对应配置
        如通过`kwargs`设置文件名读取，则返回文件名作为键名，设置作为值的字典
        """
        config_path = Path() / "configs" / plugin_name / "configs.yml"
        #config_path = Path() / plugin_name / "configs.yml"
        _yaml = YAML()
        try:
            if kwargs.get("config_files_name"):
                self._configs = {}
                self.path = kwargs.get("config_files_name")
                for file_name in self.path:
                    config_path = Path() / "configs" / plugin_name / file_name
                    with open(config_path, "r", encoding="utf-8") as f:
                        self._configs[file_name.split(".")[0]] = _yaml.load(f)
            else:
                self.path = config_path
                with open(self.path, "r", encoding="utf-8") as f:
                    self._configs = _yaml.load(f)       
        except:
            raise ScannerError(f"无法读取 {plugin_name} 配置文件！请检查配置文件路径以及配置文件内容是否符合规范")

    def set_config(self, keys:list[Union[str, int]], value:Optional[Any], mode:str= "set", auto_save=True) -> None:
        """
        对设定的已有参数字段值进行修改
        建议在聊天事务处理中进行使用

        Parameters
        ---
        keys: 字段名称，如有多层字典则按从外到内的顺序将字段名称以列表形式传入
        value: 字段设定值（`remove`方法可缺省）
        mode: 方法类型，可选值有 `set` 设定（如果有则覆盖\n
        `add` 添加（如果有则抛出异常）\n
        `remove` 删除该字段下所有内容\n
        `forced` 忽略一切结构和类型错误，强制构建结构并完成赋值（谨慎使用）
        auto_save: 是否自动保存至 `config.yml` 中，默认为True
        """
        cur_dict = self._configs
        for sub_key in keys[:-1]:
            if cur_dict.get(sub_key) is None:
                if mode in ["add", "forced"]:
                    cur_dict[sub_key] = {}
                else:
                    raise KeyError(f"{'.'.join([str(_) for _ in keys[:keys.index(sub_key)+1]])} 未赋值，无法查询并进行增删")
            if isinstance(cur_dict[sub_key], dict):
                cur_dict = cur_dict[sub_key]
            elif mode == "forced":
                cur_dict[sub_key] = {}
                cur_dict = cur_dict[sub_key]
            else:
                raise TypeError(f"{'.'.join([str(_) for _ in keys[:keys.index(sub_key)+1]])} 不是字典类型，请重新检查设置结构后再输入")

        if mode in ["set", "forced"]:
            cur_dict[keys[-1]] = value
        elif mode == "add":
            if cur_dict[keys[-1]] is None:
                cur_dict[keys[-1]] = value
            else:
                raise ValueError(f"{'.'.join([str(_) for _ in keys])} 已有指定值，无法添加")
        elif mode == "remove":
            del cur_dict[keys[-1]]
        if auto_save:
            self.save()

    def add_config(self, keys:list[str, int], value:Any, help_info:Optional[str]= None, auto_save=True) -> None:
        """
        添加配置字段，不会覆盖已有字段值
        建议初始化插件时使用，在插件`__init__`中进行配置

        Parameters
        ---
        keys: 字段名称，如有多层字典则按从外到内的顺序将字段名称以列表形式传入
        value: 字段设定值
        auto_save: 是否自动保存至 `config.yml` 中，默认为True
        """
        cur_dict = self._configs
        for sub_key in keys[:-1]:
            if cur_dict.get(sub_key) is None:
                cur_dict[sub_key] = {}
            if isinstance(cur_dict[sub_key], dict):
                cur_dict = cur_dict[sub_key]
            else:
                raise TypeError(f"{'.'.join([str(_) for _ in keys[:keys.index(sub_key)+1]])} 不是字典类型，请重新检查设置结构后再输入")
        if cur_dict.get(keys[-1]) is None:
            cur_dict[keys[-1]] = value
        else:
            raise ValueError(f"{'.'.join([str(_) for _ in keys])} 已有指定值，无法添加")

        if help_info:
            if self._configs["help_info"] is None:
                self._configs["help_info"] = {}
            self._configs["help_info"][keys[0]] = help_info
        if auto_save:
            self.save()
    
    def remove_config(self, keys:list[Union[str, int]], auto_save:bool= True) -> None:
        """
        Parameters
        ---
        keys: 字段名称，如有多层字典则按从外到内的顺序将字段名称以列表形式传入
        auto_save: 是否自动保存至 `config.yml` 中，默认为True
        """
        cur_dict = self._configs
        for sub_key in keys[:-1]:
            if cur_dict.get(sub_key) is None:
                raise KeyError(f"配置中不存在 {'.'.join([str(_) for _ in keys[:keys.index(sub_key)+1]])} ！请检查输入或先添加键值再进行配置")
            elif isinstance(cur_dict[sub_key], dict):
                cur_dict = cur_dict[sub_key]
            else:
                raise TypeError(f"{'.'.join([str(_) for _ in keys[:keys.index(sub_key)+1]])} 不是字典类型，请重新检查设置结构后再输入")

        result = cur_dict.pop(keys[-1])
        if auto_save:
            self.save()
        return result

    def get_config(self, key:str) -> Any:
        """
        获取字段值为`key`的设定值，结果与`__getitem__`一致
        """
        if key in self._configs.keys():
            return self._configs[key]
        else:
            raise KeyError(f"配置中不存在 {key} ！请检查输入或先添加键值再进行查询")

    def save(self) -> None:
        """
        将当前config中的配置保存至`config.yml`中
        """
        _yml = YAML()
        with open(self.path, "w", encoding="utf-8") as f:
            #yaml.dump(self.configs, f, indent=2, default_flow_style= False, Dumper=yaml.RoundTripDumper, allow_unicode=True)
            _yml.dump(self._configs, f)
            #yaml.round_trip_dump(self.configs, f, allow_unicode=True, indent=2)

    def check_keys(self, keys:Union[tuple, list]) -> bool:
        """
        判断keys中的字段列表是否与Config中记录的字段完全相等（强安全性检查）
        Note: keys中不要传入`help_info`
        """
        if len(keys) != len(self._configs.keys())-1 if "help_info" in self._configs.keys() else len(self._configs.keys()):
            return False
        else:
            for key in keys:
                if key not in self._configs.keys():
                    return False
            return True
    
    def keys(self):
        return self._configs.keys()

    def __setitem__(self, key, value):
        self._configs[key] = value

    def __getitem__(self, key):
        if key in self._configs.keys():
            return self._configs[key]
        else:
            raise KeyError(f"KeyError: {key} not exists")

if __name__=="__main__":
    config = Config("weather")
    #config.remove_config(["group_id", 123456, "location_list", "北京"])
    #config.add_config(["group_id", 123456, "location_list", "北京"], "101010100")
    #config.set_config(["group_id", 123456, "location_list", "北京"], "101010100", mode= "forced")
    #config["group_id"][123456] = {"location_list":{"北京":"101010100"}}
    config.save()