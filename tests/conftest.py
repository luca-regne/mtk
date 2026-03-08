"""Shared pytest fixtures for batuta tests."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from batuta.models.apk import DecompileResult, PackageInfo, PatchResult, PulledAPK


@pytest.fixture
def cli_runner():
    """Typer CLI runner for testing commands."""
    return CliRunner()


@pytest.fixture
def sample_package_info():
    """Sample PackageInfo for testing."""
    return PackageInfo(
        package_name="com.example.test",
        version_name="1.0.0",
        version_code=100,
        min_sdk=21,
        target_sdk=34,
        signing_version=3,
        apk_path="/data/app/com.example.test/base.apk",
    )


@pytest.fixture
def sample_package_info_split():
    """Sample PackageInfo for split APK testing."""
    return PackageInfo(
        package_name="com.example.split",
        version_name="2.0.0",
        version_code=200,
        min_sdk=24,
        target_sdk=34,
        apk_path="/data/app/com.example.split/base.apk",
        split_apks=[
            "/data/app/com.example.split/split_config.en.apk",
            "/data/app/com.example.split/split_config.arm64_v8a.apk",
        ],
    )


@pytest.fixture
def sample_pulled_apk(tmp_path):
    """Sample PulledAPK for testing."""
    local_path = tmp_path / "com.example.test.apk"
    local_path.write_bytes(b"fake apk content")
    return PulledAPK(
        package_name="com.example.test",
        local_path=local_path,
        is_split=False,
    )


@pytest.fixture
def sample_pulled_apk_split(tmp_path):
    """Sample PulledAPK for split APK testing."""
    local_dir = tmp_path / "com.example.split"
    local_dir.mkdir()
    base = local_dir / "base.apk"
    split1 = local_dir / "split_config.en.apk"
    split2 = local_dir / "split_config.arm64_v8a.apk"
    base.write_bytes(b"fake base apk")
    split1.write_bytes(b"fake split 1")
    split2.write_bytes(b"fake split 2")

    return PulledAPK(
        package_name="com.example.split",
        local_path=local_dir,
        is_split=True,
        split_paths=[base, split1, split2],
    )


@pytest.fixture
def sample_decompile_result(tmp_path):
    """Sample DecompileResult for testing."""
    apk_path = tmp_path / "test.apk"
    output_dir = tmp_path / "decompiled"
    java_dir = output_dir / "java"
    smali_dir = output_dir / "smali"

    apk_path.write_bytes(b"fake apk")
    java_dir.mkdir(parents=True)
    smali_dir.mkdir(parents=True)

    return DecompileResult(
        apk_path=apk_path,
        output_dir=output_dir,
        java_dir=java_dir,
        smali_dir=smali_dir,
        java_success=True,
        smali_success=True,
    )


@pytest.fixture
def sample_patch_result(tmp_path):
    """Sample PatchResult for testing."""
    source_dir = tmp_path / "apktool_output"
    output_path = tmp_path / "patched.apk"
    source_dir.mkdir()
    output_path.write_bytes(b"fake patched apk")

    return PatchResult(
        source_dir=source_dir,
        output_path=output_path,
        signed=True,
        aligned=True,
        verified=True,
        keystore_generated=False,
    )


@pytest.fixture
def temp_apk_file(tmp_path):
    """Create a temporary APK file for testing."""
    apk = tmp_path / "test.apk"
    apk.write_bytes(b"fake apk content")
    return apk


@pytest.fixture
def temp_split_dir(tmp_path):
    """Create a temporary directory with mock split APKs."""
    split_dir = tmp_path / "split_apks"
    split_dir.mkdir()
    (split_dir / "base.apk").write_bytes(b"fake base apk")
    (split_dir / "split_config.en.apk").write_bytes(b"fake split 1")
    (split_dir / "split_config.arm64_v8a.apk").write_bytes(b"fake split 2")
    return split_dir


@pytest.fixture
def temp_apktool_dir(tmp_path):
    """Create a temporary apktool-decoded directory."""
    apktool_dir = tmp_path / "apktool_decoded"
    apktool_dir.mkdir()
    (apktool_dir / "AndroidManifest.xml").write_text("<manifest/>")
    (apktool_dir / "apktool.yml").write_text("version: 2.0")
    return apktool_dir


@pytest.fixture
def mock_adb_wrapper():
    """Mock ADBWrapper instance for testing."""
    return MagicMock()


@pytest.fixture
def mock_decompiler():
    """Mock APKDecompiler instance for testing."""
    return MagicMock()


@pytest.fixture
def mock_merger():
    """Mock SplitAPKMerger instance for testing."""
    return MagicMock()


@pytest.fixture
def mock_patcher():
    """Mock APKPatcher instance for testing."""
    return MagicMock()
