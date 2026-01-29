from nonebot import require
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_localstore")
from .manager import (
    BaseDataManager,
    EnvfulConfigManager,
    UniConfigManager,
)
from .types import (
    CALLBACK_TYPE,
    FILTER_TYPE,
)

__plugin_meta__ = PluginMetadata(
    name="Uniconfig-配置文件管理器",
    description="适用于NoneBot的文件配置文件管理器",
    usage="参考README.md",
    homepage="https://github.com/LiteSuggarDEV/nonebot_plugin_uniconf/",
    type="library",
    supported_adapters=None,  # 支持所有适配器
)

__all__ = [
    "CALLBACK_TYPE",
    "FILTER_TYPE",
    "BaseDataManager",
    "EnvfulConfigManager",
    "UniConfigManager",
]
