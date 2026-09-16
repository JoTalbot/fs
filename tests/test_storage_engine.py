from __future__ import annotations

import pytest

from fs_overlay.storage_engine import ContentAddressedStore


def test_get_missing_object_does_not_create_shard_directory(tmp_path) -> None:
    store = ContentAddressedStore(tmp_path)
    object_id = "ab" * 32
    shard = store.objects / object_id[:2]

    assert not shard.exists()
    with pytest.raises(FileNotFoundError):
        store.get(object_id)
    assert not shard.exists()


def test_put_creates_shard_directory_for_object_publication(tmp_path) -> None:
    store = ContentAddressedStore(tmp_path)
    data = b"content-store write path"
    object_id = store.put(data)
    shard = store.objects / object_id[:2]

    assert shard.is_dir()
    assert store.get(object_id) == data
