from pathlib import Path
import random
from typing_extensions import override

import pytest
from pydantic import BaseModel
from nonebug import App  # type:ignore


class TestConfig(BaseModel):
    option1: str = "default_value"
    option2: int = 42
    enabled: bool = True

@pytest.mark.asyncio
async def test_uniconfig_manager_functionality(app: App):
    """测试UniConfigManager的主要功能"""
    try:
        from nonebot_plugin_uniconf import UniConfigManager
        owner_name = str(random.randint(0, 1000000))
        # 清理之前的实例
        UniConfigManager._instance = None
        assert not UniConfigManager._instance
        config_manager = UniConfigManager()

        # 测试添加配置类
        await config_manager.add_config(
            TestConfig, init_now=True, watch=False, owner_name=owner_name
        )
        assert config_manager.has_config_class(owner_name)
        assert config_manager.has_config_instance(owner_name)

        # 测试获取配置实例
        config = await config_manager.get_config(owner_name)
        assert isinstance(config, TestConfig)
        assert config.option1 == TestConfig.option1
        assert config.option2 == TestConfig.option2

        # 测试通过配置类获取配置实例
        config_by_class = await config_manager.get_config_by_class(TestConfig)
        assert isinstance(config_by_class, TestConfig)
        assert config_by_class is config  # 应该是同一个实例

        # 测试保存和重载配置
        config.option1 = "modified_value"
        config.option2 = 100
        await config_manager.loads_config(config, owner_name)

        # 保存配置
        await config_manager.save_config(owner_name)

        # 重载配置
        await config_manager.reload_config(owner_name)
        reloaded_config = await config_manager.get_config(owner_name)

        assert reloaded_config.option1 == "modified_value"
        assert reloaded_config.option2 == 100
    finally:
        TestConfig.option1 = "default_value"
        TestConfig.option2 = 42
        TestConfig.enabled = True

@pytest.mark.asyncio
async def test_add_file_functionality(app: App):
    """测试添加文件功能"""
    # 清理之前的实例
    from nonebot_plugin_uniconf import UniConfigManager
    owner_name = str(random.randint(0, 1000000))
    UniConfigManager._instance = None

    config_manager = UniConfigManager()

    await config_manager.add_file(
        "test_file.txt", "test content", watch=False, owner_name=owner_name
    )

    # 检查文件是否添加成功
    files = await config_manager.get_plugin_files(owner_name)
    assert len(files) == 1
    file_path = next(iter(files))
    assert file_path.name == "test_file.txt"

    # 测试获取缓存文件内容
    cached_content = await config_manager.get_cached_file_by_path(
        Path("test_file.txt"), owner_name
    )
    assert cached_content.getvalue() == "test content"


def test_config_classes_methods():
    """测试配置类相关方法"""
    from nonebot_plugin_uniconf import UniConfigManager

    # 清理之前的实例
    UniConfigManager._instance = None

    config_manager = UniConfigManager()

    assert len(config_manager.get_config_classes()) == 0
    assert len(config_manager.get_config_instances()) == 0


@pytest.mark.asyncio
async def test_base_data_manager_with_type_annotation(app: App):
    """测试使用类型注解定义配置的管理器"""
    try:
        from nonebot_plugin_uniconf import BaseDataManager, UniConfigManager
        owner_name = str(random.randint(0, 1000000))
        class TestDataManager(BaseDataManager[TestConfig]):
            config: TestConfig
            @override
            @classmethod
            def __init_classvars__(cls):
                cls._owner_name = owner_name

        # 重置单例实例，确保测试之间不互相影响
        BaseDataManager._instance = None
        UniConfigManager._instance = None

        manager = TestDataManager()
        config = await manager.safe_get_config()
        assert isinstance(config, TestConfig)
        assert config.option1 == TestConfig.option1
        assert config.option2 == TestConfig.option2
    finally:
        TestConfig.option1 = "default_value"
        TestConfig.option2 = 42
        TestConfig.enabled = True


@pytest.mark.asyncio
async def test_base_data_manager_with_config_class(app: App):
    """测试使用config_class属性定义配置的管理器"""
    from nonebot_plugin_uniconf import BaseDataManager, UniConfigManager
    owner_name = str(random.randint(0, 1000000))
    class AnotherDataManager(BaseDataManager[TestConfig]):
        config_class = TestConfig
        @override
        @classmethod
        def __init_classvars__(cls):
            cls._owner_name = owner_name

    # 重置单例实例
    BaseDataManager._instance = None
    UniConfigManager._instance = None

    manager = AnotherDataManager()
    config = await manager.safe_get_config()
    assert isinstance(config, TestConfig)
    assert config.option1 == "default_value"
    assert config.option2 == 42


@pytest.mark.asyncio
async def test_config_modification(app: App):
    """测试配置修改功能"""
    try:


        from nonebot_plugin_uniconf import BaseDataManager, UniConfigManager
        owner_name = str(random.randint(0, 1000000))
        class TestDataManager(BaseDataManager[TestConfig]):
            config: TestConfig
            @override
            @classmethod
            def __init_classvars__(cls):
                cls._owner_name = owner_name
        # 重置单例实例
        BaseDataManager._instance = None
        UniConfigManager._instance = None

        manager = TestDataManager()
        config = await manager.safe_get_config()

        # 修改配置
        config.option1 = "new_value"
        config.option2 = 999

        # 验证修改后的值
        assert config.option1 == "new_value"
        assert config.option2 == 999
    finally:
        TestConfig.option1 = "default_value"
        TestConfig.option2 = 42
        TestConfig.enabled = True


@pytest.mark.asyncio
async def test_integration_full_config_lifecycle(app: App):
    """测试完整的配置生命周期"""
    from nonebot_plugin_uniconf import BaseDataManager, UniConfigManager
    owner_name = str(random.randint(0, 1000000))
    class TestDataManager(BaseDataManager[TestConfig]):
        config: TestConfig
        
        @override
        @classmethod
        def __init_classvars__(cls):
            cls._owner_name = owner_name
            assert cls._owner_name
    # 重置单例
    UniConfigManager._instance = None
    BaseDataManager._instance = None

    # 创建数据管理器
    manager = TestDataManager()

    # 获取初始配置
    config = await manager.safe_get_config()
    assert isinstance(config, TestConfig)
    assert config.option1 == TestConfig.option1
    assert config.option2 == TestConfig.option2

    # 修改配置
    config.option1 = "updated_value"
    config.option2 = 123

    # 通过UniConfigManager获取同一配置，验证是否更新
    uni_manager = UniConfigManager()
    same_config = await uni_manager.get_config()
    assert same_config.option1 == "updated_value"
    assert same_config.option2 == 123

    # 保存配置
    await uni_manager.save_config()

    # 重新加载配置
    await uni_manager.reload_config()
    reloaded_config = await uni_manager.get_config()

    # 验证重载后的值
    assert reloaded_config.option1 == "updated_value"
    assert reloaded_config.option2 == 123
