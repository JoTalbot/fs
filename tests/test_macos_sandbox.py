from fs_overlay.macos_sandbox import MacOSSignedHelperBackend


def test_macos_backend_requires_signed_host_and_helper(monkeypatch):
    monkeypatch.setattr("fs_overlay.macos_sandbox.platform.system", lambda: "Darwin")
    result = MacOSSignedHelperBackend().plan()
    assert not result.available
    assert result.reason == "signed_helper_and_host_required"


def test_macos_backend_is_fail_closed_off_platform(monkeypatch, tmp_path):
    monkeypatch.setattr("fs_overlay.macos_sandbox.platform.system", lambda: "Linux")
    helper = tmp_path / "helper"
    host = tmp_path / "Host.app"
    helper.write_text("placeholder")
    host.mkdir()
    result = MacOSSignedHelperBackend().inspect(str(helper), str(host))
    assert not result.available
    assert result.reason == "host is not macOS"


def test_macos_backend_requires_app_bundle(monkeypatch, tmp_path):
    monkeypatch.setattr("fs_overlay.macos_sandbox.platform.system", lambda: "Darwin")
    helper = tmp_path / "helper"
    helper.write_text("placeholder")
    result = MacOSSignedHelperBackend().inspect(str(helper), str(tmp_path / "host"))
    assert not result.available
    assert result.reason == "sandbox_host_app_required"


def test_macos_backend_accepts_validated_entitlements(monkeypatch, tmp_path):
    monkeypatch.setattr("fs_overlay.macos_sandbox.platform.system", lambda: "Darwin")
    helper = tmp_path / "helper"
    host = tmp_path / "Host.app"
    helper.write_text("placeholder")
    host.mkdir()
    backend = MacOSSignedHelperBackend()
    monkeypatch.setattr(
        backend,
        "_entitlements",
        lambda target: (
            "<key>com.apple.security.app-sandbox</key>\n"
            + ("<key>com.apple.security.inherit</key>\n" if target == helper else "")
        ),
    )
    monkeypatch.setattr(backend, "_codesign", lambda args, target: "flags=0x10000(runtime)" if "-d" not in args else "valid")
    result = backend.inspect(str(helper), str(host))
    assert result.available
    assert result.guarantees == ("signed-sandbox-helper-admitted", "helper-sandbox-inheritance-configured")
