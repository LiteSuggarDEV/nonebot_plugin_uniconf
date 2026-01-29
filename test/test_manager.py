import os
import shutil

import pytest
from nonebot import require
from nonebug import App  # type:ignore
from pydantic import BaseModel


class TestConfig(BaseModel):
    option1: str = "default_value"
    option2: int = 42
    enabled: bool = True


class TestConfigWithEnv(TestConfig):
    option1: str = "${UNICONF_OPTION1}"


@pytest.mark.asyncio
async def test_integration_full_config_env(app: App):
    """测试完整的配置生命周期(带有环境变量支持)"""
    require("nonebot_plugin_localstore")
    from nonebot_plugin_localstore import get_config_dir

    from nonebot_plugin_uniconf import EnvfulConfigManager, UniConfigManager

    owner_name = "test_plugin2"
    conf_dir = get_config_dir(owner_name)
    shutil.rmtree(conf_dir, ignore_errors=True)
    os.mkdir(conf_dir)
    default_config = TestConfig()
    os.environ["UNICONF_OPTION1"] = "default_value"

    class TestDataManager(EnvfulConfigManager[TestConfigWithEnv]):
        config: TestConfigWithEnv
        _owner_name = owner_name

    # 重置单例
    UniConfigManager._instance = None

    # 创建数据管理器
    manager = TestDataManager()

    # 获取初始配置
    config = await manager.safe_get_config()
    assert isinstance(config, TestConfig)
    assert config.option1 == default_config.option1
    assert config.option2 == default_config.option2

    # 修改配置
    # config.option1 = "updated_value"
    # config.option2 = 123
    # 修改被替换环境变量占位符的变量并不会更改原始的配置实例，因此实际开发如果确实需要修改实例则应访问`ins_config`属性。


@pytest.mark.asyncio
async def test_integration_full_config_lifecycle(app: App):
    """测试完整的配置生命周期"""
    require("nonebot_plugin_localstore")
    from nonebot_plugin_localstore import get_config_dir

    from nonebot_plugin_uniconf import BaseDataManager, UniConfigManager

    owner_name = "test_plugin"
    conf_dir = get_config_dir(owner_name)
    shutil.rmtree(conf_dir, ignore_errors=True)
    os.mkdir(conf_dir)
    default_config = TestConfig()

    class TestDataManager(BaseDataManager[TestConfig]):
        config: TestConfig
        _owner_name = owner_name

    # 重置单例
    UniConfigManager._instance = None
    BaseDataManager._instance = None

    # 创建数据管理器
    manager = TestDataManager()
    uni_manager = UniConfigManager()

    # 获取初始配置
    config = await manager.safe_get_config()
    assert isinstance(config, TestConfig)
    assert config.option1 == default_config.option1
    assert config.option2 == default_config.option2

    # 修改配置
    config.option1 = "updated_value"
    config.option2 = 123

    # 通过UniConfigManager获取同一配置，验证是否更新

    same_config: TestConfig = await uni_manager.get_config(owner_name)
    assert same_config.option1 == "updated_value"
    assert same_config.option2 == 123

    # 保存配置
    await uni_manager.save_config(owner_name)

    # 重新加载配置
    await uni_manager.reload_config(owner_name)
    reloaded_config = await uni_manager.get_config(owner_name)

    # 验证重载后的值
    assert reloaded_config.option1 == "updated_value"
    assert reloaded_config.option2 == 123
