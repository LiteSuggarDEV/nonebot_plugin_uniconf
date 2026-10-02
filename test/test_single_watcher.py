import asyncio
import contextlib
import shutil
from pathlib import Path

import pytest
import watchfiles
from nonebug import App


async def _noop(owner: str, path: Path) -> None:
    pass


def _make_entry(plugin_name: str, path: Path, calls: list):
    from nonebot_plugin_uniconf.manager import _WatchEntry

    target = Path(path)

    def _filter(change) -> bool:
        return Path(change[1]).name == target.name

    async def _cb(owner: str, p: Path) -> None:
        calls.append((owner, p))

    return _WatchEntry(plugin_name, target, _filter, (_cb,))


def _reset(manager) -> None:
    if manager._watcher_task is not None:
        manager._watcher_task.cancel()
        manager._watcher_task = None
    manager._watch_entries.clear()
    manager._watch_stop = None


def _fresh_dir(owner: str) -> Path:
    from nonebot_plugin_localstore import get_config_dir

    d = get_config_dir(owner)
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.mark.asyncio
async def test_collect_roots_dedups_children(app: App, tmp_path: Path):
    """目录根覆盖的子路径不应重复交给 watchfiles"""
    from nonebot_plugin_uniconf.manager import UniConfigManager

    manager = UniConfigManager()
    _reset(manager)
    manager._watch_entries.append(_make_entry("a", tmp_path, []))
    manager._watch_entries.append(_make_entry("a", tmp_path / "config.toml", []))
    manager._watch_entries.append(_make_entry("a", tmp_path / "data", []))

    assert manager._collect_roots() == (tmp_path,)
    _reset(manager)


@pytest.mark.asyncio
async def test_collect_roots_keeps_independent_paths(app: App, tmp_path: Path):
    """互不覆盖的路径应全部保留"""
    from nonebot_plugin_uniconf.manager import UniConfigManager

    manager = UniConfigManager()
    _reset(manager)
    manager._watch_entries.append(_make_entry("a", tmp_path / "one.toml", []))
    manager._watch_entries.append(_make_entry("a", tmp_path / "sub", []))

    assert set(manager._collect_roots()) == {tmp_path / "one.toml", tmp_path / "sub"}
    _reset(manager)


@pytest.mark.asyncio
async def test_dispatch_is_scoped_per_plugin(app: App, tmp_path: Path):
    """单 watcher 下，A 的变更不能误触发 B 的回调"""
    from nonebot_plugin_uniconf.manager import UniConfigManager

    manager = UniConfigManager()
    _reset(manager)
    calls: list = []
    a_conf = tmp_path / "a" / "config.toml"
    b_conf = tmp_path / "b" / "config.toml"
    manager._watch_entries.append(_make_entry("a", a_conf, calls))
    manager._watch_entries.append(_make_entry("b", b_conf, calls))

    await manager._dispatch({(watchfiles.Change.modified, str(a_conf))})

    assert calls == [("a", a_conf)]
    _reset(manager)


@pytest.mark.asyncio
async def test_only_one_watcher_runs_and_restarts(
    app: App, tmp_path: Path, monkeypatch
):
    """无论注册多少条监视，同一时刻只有一个 watcher 在跑"""
    import nonebot_plugin_uniconf.manager as mgr
    from nonebot_plugin_uniconf.manager import UniConfigManager

    manager = UniConfigManager()
    _reset(manager)
    state = {"active": 0, "max_active": 0, "path_sets": []}

    async def fake_awatch(*paths, stop_event=None, **kwargs):
        state["active"] += 1
        state["max_active"] = max(state["max_active"], state["active"])
        state["path_sets"].append(tuple(paths))
        try:
            if stop_event is not None:
                await stop_event.wait()
            if False:  # pragma: no cover - 让它成为 async generator
                yield set()
        finally:
            state["active"] -= 1

    monkeypatch.setattr(mgr.watchfiles, "awatch", fake_awatch)

    p1 = tmp_path / "config.toml"
    p2 = tmp_path / "data"
    await manager._add_watch_path("a", p1, lambda c: True, _noop)
    await asyncio.sleep(0.05)
    await manager._add_watch_path("a", p2, lambda c: True, _noop)
    await asyncio.sleep(0.1)

    assert state["max_active"] == 1
    assert set(state["path_sets"][-1]) == {p1, p2}

    if manager._watcher_task is not None:
        manager._watcher_task.cancel()
        with contextlib.suppress(BaseException):
            await manager._watcher_task
    _reset(manager)


@pytest.mark.asyncio
async def test_add_file_watches_the_file_itself(app: App):
    """add_file 应直接监控目标文件，回调才能拿到真实文件路径"""
    from nonebot_plugin_uniconf.manager import UniConfigManager

    manager = UniConfigManager()
    _reset(manager)
    d = _fresh_dir("test_add_file_watches")
    await manager.add_file("notes.txt", "hello", watch=True, owner_name="test_add_file_watches")

    assert {entry.path for entry in manager._watch_entries} == {
        (d / "notes.txt").resolve()
    }
    _reset(manager)


@pytest.mark.asyncio
async def test_file_reload_callback_replaces_cache(app: App, tmp_path: Path):
    """文件变短时缓存应整体替换，而不是在旧内容后面追加"""
    from nonebot_plugin_uniconf.manager import UniConfigManager

    manager = UniConfigManager()
    _reset(manager)
    f = tmp_path / "notes.txt"
    f.write_text("hello", encoding="utf-8")
    await manager._file_reload_callback("p", f)
    assert manager._config_file_cache[str(f)].getvalue() == "hello"

    f.write_text("hi", encoding="utf-8")
    await manager._file_reload_callback("p", f)
    assert manager._config_file_cache[str(f)].getvalue() == "hi"
    _reset(manager)


@pytest.mark.asyncio
async def test_add_directory_ignores_sibling_prefix(app: App):
    """data 目录的监视不应命中 database 这类同前缀兄弟路径"""
    from nonebot_plugin_uniconf.manager import UniConfigManager

    manager = UniConfigManager()
    _reset(manager)
    d = _fresh_dir("test_dir_prefix")
    hits: list = []

    async def _cb(owner: str, path: Path) -> None:
        hits.append(path)

    await manager.add_directory("data", _cb, watch=True, owner_name="test_dir_prefix")

    await manager._dispatch(
        {(watchfiles.Change.added, str(d / "database" / "x.txt"))}
    )
    assert hits == []

    await manager._dispatch({(watchfiles.Change.added, str(d / "data" / "x.txt"))})
    assert hits == [d / "data"]
    _reset(manager)


@pytest.mark.asyncio
async def test_duplicate_registration_keeps_single_entry(app: App, tmp_path: Path):
    """同一 (插件, 路径) 重复注册应合并为一条，避免一次变更触发重复回调"""
    from nonebot_plugin_uniconf.manager import UniConfigManager

    manager = UniConfigManager()
    _reset(manager)
    target = tmp_path / "notes.txt"

    await manager._add_watch_path("dup", target, lambda c: True, _noop)
    await manager._add_watch_path("dup", target, lambda c: True, _noop)

    entries = [e for e in manager._watch_entries if e.path == target]
    assert len(entries) == 1
    assert entries[0].callbacks == (_noop,)

    if manager._watcher_task is not None:
        manager._watcher_task.cancel()
        with contextlib.suppress(BaseException):
            await manager._watcher_task
    _reset(manager)


@pytest.mark.asyncio
async def test_duplicate_registration_merges_callbacks(app: App, tmp_path: Path):
    """重复注册带不同回调时应合并，且每条回调只触发一次"""
    from nonebot_plugin_uniconf.manager import UniConfigManager

    manager = UniConfigManager()
    _reset(manager)
    target = tmp_path / "notes.txt"
    hits: list = []

    async def _cb1(owner: str, path: Path) -> None:
        hits.append("cb1")

    async def _cb2(owner: str, path: Path) -> None:
        hits.append("cb2")

    await manager._add_watch_path("dup", target, lambda c: True, _cb1)
    await manager._add_watch_path("dup", target, lambda c: True, _cb2)

    entries = [e for e in manager._watch_entries if e.path == target]
    assert len(entries) == 1
    assert set(entries[0].callbacks) == {_cb1, _cb2}

    await manager._dispatch({(watchfiles.Change.modified, str(target))})
    assert hits == ["cb1", "cb2"]

    if manager._watcher_task is not None:
        manager._watcher_task.cancel()
        with contextlib.suppress(BaseException):
            await manager._watcher_task
    _reset(manager)


@pytest.mark.asyncio
async def test_add_file_twice_registers_once(app: App):
    """add_file 重复调用同一文件名时只应保留一条监控"""
    from nonebot_plugin_uniconf.manager import UniConfigManager

    manager = UniConfigManager()
    _reset(manager)
    owner = "test_add_file_twice"
    d = _fresh_dir(owner)
    await manager.add_file("notes.txt", "hello", watch=True, owner_name=owner)
    await manager.add_file("notes.txt", "hello", watch=True, owner_name=owner)

    target = (d / "notes.txt").resolve()
    assert [e.path for e in manager._watch_entries].count(target) == 1
    _reset(manager)
