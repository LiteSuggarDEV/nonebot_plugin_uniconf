from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from nonebug import App
from pydantic import BaseModel

if TYPE_CHECKING:
    from pathlib import Path as TypeCheckingOnly


class PluginConfig(BaseModel):
    enabled: bool = True


@pytest.mark.asyncio
async def test_explicit_config_class_ignores_unrelated_annotations(app: App):
    from nonebot_plugin_uniconf import BaseDataManager, UniConfigManager

    class Manager(BaseDataManager[PluginConfig]):
        _owner_name = "explicit_annotations"
        config_class = PluginConfig
        unrelated: TypeCheckingOnly

    with patch.object(UniConfigManager, "add_config", autospec=True) as add_config:
        manager = Manager()
        assert manager._task is not None
        await manager._task
        assert add_config.await_args.args[1] is PluginConfig


@pytest.mark.asyncio
async def test_inferred_config_resolves_in_declaring_module(app: App):
    from nonebot_plugin_uniconf import BaseDataManager, UniConfigManager

    class PluginManager(BaseDataManager[PluginConfig]):
        _owner_name = "inferred_annotations"
        config: PluginConfig
        unrelated: TypeCheckingOnly

    # A subclass in a different module still uses the declaration's globals.
    class Manager(PluginManager):
        __module__ = BaseDataManager.__module__

    with patch.object(UniConfigManager, "add_config", autospec=True) as add_config:
        manager = Manager()
        assert manager._task is not None
        await manager._task
        assert manager.config_class is PluginConfig
        assert add_config.await_args.args[1] is PluginConfig
