<div align="center">
  <a href="https://github.com/LiteSuggarDEV/nonebot_plugin_uniconf/">
    <img src="https://github.com/user-attachments/assets/b5162036-5b17-4cf4-b0cb-8ec842a71bc6" width="200" alt="uniconf Logo">
  </a>
  <h1>nonebot-plugin-uniconf</h1>
  <h3>配置文件管理器</h3>

  <p>
    <a href="https://pypi.org/project/nonebot-plugin-uniconf/">
      <img src="https://img.shields.io/pypi/v/nonebot-plugin-uniconf?color=blue&style=flat-square" alt="PyPI Version">
    </a>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&style=flat-square" alt="Python Version">
    </a>
    <a href="https://nonebot.dev/">
      <img src="https://img.shields.io/badge/nonebot2-2.4.0+-blue?style=flat-square" alt="NoneBot Version">
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/github/license/LiteSuggarDEV/nonebot_plugin_uniconf?style=flat-square" alt="License">
    </a>
    <a href="https://qm.qq.com/q/9J23pPZN3a">
      <img src="https://img.shields.io/badge/QQ%E7%BE%A4-1006893368-blue?style=flat-square" alt="QQ Group">
    </a>
  </p>
</div>

一个为 NoneBot2 插件设计的统一**文件**配置管理器，提供了便捷的配置文件管理、热重载和文件监控功能。

## 功能特性

- **类型安全的配置管理**：基于 Pydantic BaseModel，提供类型检查和自动验证
- **配置热重载**：当配置文件被修改时，自动重新加载配置
- **单例模式**：确保每个插件的配置管理器只有一个实例
- **异步支持**：完全异步实现，不阻塞事件循环
- **灵活的配置定义**：支持多种配置类定义方式
- **文件和目录监控**：支持对配置文件和自定义文件/目录的监控
- **环境变量支持**：支持在配置中使用环境变量占位符（`${VAR}` 或 `{{VAR}}`）

## 安装

```bash
# 使用 nb-cli 安装
nb plugin install nonebot-plugin-uniconf

# 使用 pip 安装
pip install nonebot-plugin-uniconf
```

## 快速开始

### 1. 定义配置类

首先，定义一个继承自 `Pydantic` 的 `BaseModel` 的配置类：

```python
from pydantic import BaseModel

class MyConfig(BaseModel):
    my_option: str = "default_value"
    my_number: int = 42
```

### 2. 创建配置管理器

有两种方式创建配置管理器：

#### 方式 1：使用类型注解定义配置实例

```python
from nonebot_plugin_uniconf import BaseDataManager
from nonebot import logger

class MyDataManager(BaseDataManager[MyConfig]):
    config: MyConfig  # 配置实例，类型注解用于自动推导 config_class

    async def __apost_init__(self):
        # 配置加载完成后的异步初始化
        logger.info(f"配置已加载: {self.config.my_option}")
```

#### 方式 2：定义配置类变量

```python
from nonebot_plugin_uniconf import BaseDataManager
from nonebot import logger

class MyDataManager(BaseDataManager[MyConfig]):
    config_class = MyConfig  # 配置类类型

    async def __apost_init__(self):
        # 配置加载完成后的异步初始化
        logger.info(f"配置已加载: {self.config.my_number}")
```

### 3. 使用配置管理器

```python
# 获取配置管理器实例
config_manager = MyDataManager()

# 获取配置（会等待配置加载完成）
config = await config_manager.safe_get_config()
logger.debug(config.my_option)
```

## 高级用法

### 环境变量支持

如果需要在配置中使用环境变量，可以使用 `EnvfulConfigManager`

```python
from nonebot_plugin_uniconf import EnvfulConfigManager

class MyEnvDataManager(EnvfulConfigManager[MyConfig]):
    config: MyConfig

    async def __apost_init__(self):
        # 配置中的环境变量会被自动替换
        logger.info(f"配置已加载: {self.config.my_option}")
```

配置文件中可以使用 `${ENV_VAR}` 或 `{{ENV_VAR}}` 格式的环境变量占位符。

### 直接使用 UniConfigManager

如果需要更细粒度的控制，可以直接使用 UniConfigManager：

```python
from nonebot_plugin_uniconf import UniConfigManager

# 添加配置类
await UniConfigManager().add_config(MyConfig)

# 获取配置
config = await UniConfigManager().get_config() # 请自行缓存配置文件实例或者缓存try_get_caller_plugin()的name字段并传入，因为频繁获取堆栈上下文会导致性能问题

# 保存配置
await UniConfigManager().save_config()
```

### 管理额外文件

```python
# 添加并监控额外的文件
await UniConfigManager().add_file("custom_data.txt", "初始内容")

# 添加并监控目录
async def on_directory_change(owner_name: str, path: Path):
    logger.info(f"目录 {path} 已更改")

await UniConfigManager().add_directory("data", on_directory_change)
```

## API 参考

### BaseDataManager[T]

配置数据管理器基类，实现了基于类型注解的自动配置类推导。

- `config: T` - 配置实例
- `config_class: Type[T]` - 配置类类型
- `safe_get_config()` - 安全获取配置，等待配置加载完成
- `refresh_config()` - 刷新当前配置
- `__apost_init__()` - 异步初始化后置处理方法
- `(classmethod) __init_classvars__()` - 类变量初始化方法
- `_owner_name` - 拥有者插件名称
- `_inited` - 是否已初始化
- `__lateinit__` - 适用于需要延迟初始化的 DataManager

### EnvfulConfigManager[T]

支持环境变量的配置管理器，继承自 BaseDataManager。

- `ins_config: T` - 实际配置实例
- `config: T` - 处理过环境变量的配置实例（重写了父类的 config 属性）
- `_cached_env_config` - 缓存的环境变量处理后的配置
- `_conf_id` - 配置ID，用于检测配置是否更改

### UniConfigManager[T]

统一配置管理器，提供完整的配置管理功能。

#### 主要方法

- `add_config()` - 添加配置类
- `get_config()` - 获取配置实例
- `get_config_by_class()` - 根据配置类获取配置实例
- `get_config_class()` - 获取配置类类型
- `reload_config()` - 重新加载配置
- `save_config()` - 保存配置
- `loads_config()` - 加载配置实例
- `add_file()` - 添加文件监控
- `add_directory()` - 添加目录监控
- `get_plugin_files()` - 获取插件注册的文件
- `get_cached_file_by_path()` - 获取缓存的文件内容
- `get_config_classes()` - 获取所有已注册的配置类
- `get_config_instances()` - 获取所有配置实例
- `has_config_class()` - 检查是否存在指定插件的配置类
- `has_config_instance()` - 检查是否存在指定插件的配置实例
- `get_config_instance()` - 获取指定插件的配置实例
- `get_config_instance_not_none()` - 获取指定插件的配置实例（非空）
- `get_config_class_by_name()` - 根据插件名称获取配置类

#### 其他实用方法

- `_init_config_or_nothing()` - 初始化配置文件（如果不存在）
- `_add_watch_path()` - 添加路径监控
- `_config_reload_callback()` - 配置重载回调函数
- `_file_reload_callback()` - 文件重载回调函数

## 使用场景

这个插件适合以下场景的 NoneBot2 插件，例如：

- 需要热重载配置的机器人插件
- 需要管理多个配置文件的插件
- 需要在运行时动态修改配置的插件
- 需要使用环境变量的插件

## 许可证

- AGPL-V3.0
