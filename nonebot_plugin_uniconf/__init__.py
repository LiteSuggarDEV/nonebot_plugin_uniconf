from nonebot.plugin import PluginMetadata

from .manager import CALLBACK_TYPE, BaseDataManager, UniConfigManager

__plugin_meta__ = PluginMetadata(
    name="Uniconfig配置文件API",
    description="适用于NoneBot的文件配置文件管理器",
    # usage="https://docs.suggar.top/project/uniconf/", # 这里还没写
    usage="参考README.md",
    homepage="https://github.com/LiteSuggarDEV/nonebot_plugin_uniconf/",
    type="library",
    supported_adapters=None, # 支持所有适配器
)

__all__ = [
    "CALLBACK_TYPE",
    "BaseDataManager",
    "UniConfigManager",
]
