"""Tests for batuta.cli.apk module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer

from batuta.cli.apk import _parse_selection, _select_package, app
from batuta.exceptions import (
    BatutaError,
    MultiplePackagesFoundError,
    PackageNotFoundError,
)
from batuta.models.apk import DecompileResult, PackageInfo, PatchResult, PulledAPK


@pytest.mark.unit
@pytest.mark.cli
class TestParseSelection:
    """Test the _parse_selection helper function."""

    def test_single_number_valid(self):
        """Test parsing a single valid number."""
        result = _parse_selection("1", 5)
        assert result == [0]

    def test_single_number_first(self):
        """Test parsing first item."""
        result = _parse_selection("1", 10)
        assert result == [0]

    def test_single_number_last(self):
        """Test parsing last item."""
        result = _parse_selection("5", 5)
        assert result == [4]

    def test_comma_separated_numbers(self):
        """Test parsing comma-separated numbers."""
        result = _parse_selection("1,3,5", 6)
        assert result == [0, 2, 4]

    def test_comma_separated_with_spaces(self):
        """Test parsing comma-separated with spaces."""
        result = _parse_selection("1, 3, 5", 6)
        assert result == [0, 2, 4]

    def test_range_notation(self):
        """Test parsing range notation."""
        result = _parse_selection("1-3", 5)
        assert result == [0, 1, 2]

    def test_range_notation_full(self):
        """Test parsing range spanning all items."""
        result = _parse_selection("1-5", 5)
        assert result == [0, 1, 2, 3, 4]

    def test_mixed_format(self):
        """Test parsing mixed format (ranges and individual)."""
        result = _parse_selection("1,3-5,7", 10)
        assert result == [0, 2, 3, 4, 6]

    def test_all_keyword(self):
        """Test parsing 'all' keyword."""
        result = _parse_selection("all", 5)
        assert result == [0, 1, 2, 3, 4]

    def test_all_keyword_shorthand(self):
        """Test parsing 'a' shorthand for all."""
        result = _parse_selection("a", 5)
        assert result == [0, 1, 2, 3, 4]

    def test_all_keyword_case_insensitive(self):
        """Test 'ALL' is case insensitive."""
        result = _parse_selection("ALL", 3)
        assert result == [0, 1, 2]

    def test_invalid_out_of_range_single(self):
        """Test invalid selection - single number out of range."""
        result = _parse_selection("10", 5)
        assert result is None

    def test_invalid_out_of_range_in_list(self):
        """Test invalid selection - one number in list out of range."""
        result = _parse_selection("1,10", 5)
        assert result is None

    def test_invalid_zero(self):
        """Test invalid selection - zero is not valid."""
        result = _parse_selection("0", 5)
        assert result is None

    def test_invalid_negative(self):
        """Test invalid selection - negative number."""
        result = _parse_selection("-1", 5)
        assert result is None

    def test_invalid_format(self):
        """Test invalid format."""
        result = _parse_selection("abc", 5)
        assert result is None

    def test_invalid_range_backward(self):
        """Test invalid range - backward range."""
        result = _parse_selection("5-1", 10)
        assert result is None

    def test_invalid_range_out_of_bounds(self):
        """Test invalid range - exceeds max."""
        result = _parse_selection("1-10", 5)
        assert result is None

    def test_empty_input(self):
        """Test empty input."""
        result = _parse_selection("", 5)
        assert result is None

    def test_duplicate_indices(self):
        """Test that duplicate indices are deduplicated."""
        result = _parse_selection("1,1,2", 5)
        assert result == [0, 1]

    def test_overlapping_ranges(self):
        """Test overlapping ranges are merged."""
        result = _parse_selection("1-3,2-4", 5)
        assert result == [0, 1, 2, 3]


@pytest.mark.unit
@pytest.mark.cli
class TestSelectPackage:
    """Test the _select_package helper function."""

    @patch("batuta.cli.apk.typer.prompt")
    @patch("batuta.cli.apk._display_package_table")
    def test_single_selection_valid(
        self, mock_display, mock_prompt, sample_package_info
    ):
        """Test single package selection with valid input."""
        packages = [sample_package_info]
        mock_prompt.return_value = "1"

        result = _select_package(packages, "test", multiple=False)

        assert result == [sample_package_info]
        mock_display.assert_called_once_with(packages, "test")

    @patch("batuta.cli.apk.typer.prompt")
    @patch("batuta.cli.apk._display_package_table")
    def test_multiple_selection_valid(self, mock_display, mock_prompt):
        """Test multiple package selection."""
        packages = [
            PackageInfo(package_name="com.example.one"),
            PackageInfo(package_name="com.example.two"),
            PackageInfo(package_name="com.example.three"),
        ]
        mock_prompt.return_value = "1,3"

        result = _select_package(packages, "test", multiple=True)

        assert len(result) == 2
        assert result[0].package_name == "com.example.one"
        assert result[1].package_name == "com.example.three"

    @patch("batuta.cli.apk.typer.prompt")
    @patch("batuta.cli.apk._display_package_table")
    def test_selection_quit(self, mock_display, mock_prompt, sample_package_info):
        """Test user quits selection."""
        packages = [sample_package_info]
        mock_prompt.return_value = "q"

        with pytest.raises(typer.Abort):
            _select_package(packages, "test", multiple=False)

    @patch("batuta.cli.apk.typer.prompt")
    @patch("batuta.cli.apk._display_package_table")
    @patch("batuta.cli.apk.console")
    def test_invalid_selection_then_valid(
        self, mock_console, mock_display, mock_prompt, sample_package_info
    ):
        """Test retry after invalid selection."""
        packages = [sample_package_info]
        mock_prompt.side_effect = ["99", "1"]  # Invalid then valid

        result = _select_package(packages, "test", multiple=False)

        assert result == [sample_package_info]
        assert mock_prompt.call_count == 2

    @patch("batuta.cli.apk.typer.prompt")
    @patch("batuta.cli.apk._display_package_table")
    def test_multiple_selection_all(self, mock_display, mock_prompt):
        """Test selecting all packages."""
        packages = [PackageInfo(package_name=f"com.example.{i}") for i in range(3)]
        mock_prompt.return_value = "all"

        result = _select_package(packages, "test", multiple=True)

        assert len(result) == 3


@pytest.mark.unit
@pytest.mark.cli
class TestListCommand:
    """Test the 'list' command."""

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    @patch("batuta.cli.apk.console")
    def test_list_basic_success(
        self, mock_console, mock_adb_class, mock_require, cli_runner
    ):
        """Test basic list command without filters."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.list_packages.return_value = ["com.example.app1", "com.example.app2"]

        result = cli_runner.invoke(app, ["list"])

        assert result.exit_code == 0
        mock_require.assert_called_once_with("adb")
        mock_adb.list_packages.assert_called_once_with(include_system=False)

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_list_with_filter(self, mock_adb_class, mock_require, cli_runner):
        """Test list command with filter query."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.search_packages.return_value = [
            PackageInfo(package_name="com.google.app")
        ]

        result = cli_runner.invoke(app, ["list", "google"])

        assert result.exit_code == 0
        mock_adb.search_packages.assert_called_once_with(
            "google", include_system=False, detailed=False
        )

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_list_system_packages(self, mock_adb_class, mock_require, cli_runner):
        """Test list command with --system flag."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.list_packages.return_value = ["android.system.app"]

        result = cli_runner.invoke(app, ["list", "--system"])

        assert result.exit_code == 0
        mock_adb.list_packages.assert_called_once_with(include_system=True)

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_list_detailed_mode(self, mock_adb_class, mock_require, cli_runner):
        """Test list command with --detailed flag."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.list_packages.return_value = ["com.example.app"]
        mock_adb.get_package_info.return_value = PackageInfo(
            package_name="com.example.app", version_name="1.0.0"
        )

        result = cli_runner.invoke(app, ["list", "--detailed"])

        assert result.exit_code == 0
        mock_adb.get_package_info.assert_called()

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_list_json_output(self, mock_adb_class, mock_require, cli_runner):
        """Test list command with --json flag."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.list_packages.return_value = ["com.example.app"]

        result = cli_runner.invoke(app, ["list", "--json"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert isinstance(output, list)
        assert len(output) == 1
        assert output[0]["package_name"] == "com.example.app"

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_list_no_packages_found(self, mock_adb_class, mock_require, cli_runner):
        """Test list command when no packages found."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.list_packages.return_value = []

        result = cli_runner.invoke(app, ["list"])

        assert result.exit_code == 1

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_list_with_device_option(self, mock_adb_class, mock_require, cli_runner):
        """Test list command with specific device."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.list_packages.return_value = ["com.example.app"]

        result = cli_runner.invoke(app, ["list", "--device", "emulator-5554"])

        assert result.exit_code == 0
        mock_adb_class.assert_called_once_with(device_id="emulator-5554")

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_list_error_handling(self, mock_adb_class, mock_require, cli_runner):
        """Test list command handles BatutaError."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.list_packages.side_effect = BatutaError("Device not found")

        result = cli_runner.invoke(app, ["list"])

        assert result.exit_code == 1


@pytest.mark.unit
@pytest.mark.cli
class TestSearchCommand:
    """Test the 'search' command."""

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_search_basic_success(self, mock_adb_class, mock_require, cli_runner):
        """Test basic search command."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.search_packages.return_value = [
            PackageInfo(package_name="com.google.chrome")
        ]

        result = cli_runner.invoke(app, ["search", "google"])

        assert result.exit_code == 0
        mock_adb.search_packages.assert_called_once_with(
            "google", include_system=False, detailed=False
        )

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_search_with_system_flag(self, mock_adb_class, mock_require, cli_runner):
        """Test search with --system flag."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.search_packages.return_value = []

        result = cli_runner.invoke(app, ["search", "android", "--system"])

        assert result.exit_code == 1  # No results
        mock_adb.search_packages.assert_called_once_with(
            "android", include_system=True, detailed=False
        )

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_search_detailed_mode(self, mock_adb_class, mock_require, cli_runner):
        """Test search with --detailed flag."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.search_packages.return_value = [
            PackageInfo(package_name="com.example.app", version_name="1.0")
        ]

        result = cli_runner.invoke(app, ["search", "example", "--detailed"])

        assert result.exit_code == 0
        mock_adb.search_packages.assert_called_once_with(
            "example", include_system=False, detailed=True
        )

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_search_json_output(self, mock_adb_class, mock_require, cli_runner):
        """Test search with --json flag."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.search_packages.return_value = [
            PackageInfo(package_name="com.example.app")
        ]

        result = cli_runner.invoke(app, ["search", "example", "--json"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert isinstance(output, list)
        assert output[0]["package_name"] == "com.example.app"

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_search_no_results(self, mock_adb_class, mock_require, cli_runner):
        """Test search when no packages match."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.search_packages.return_value = []

        result = cli_runner.invoke(app, ["search", "nonexistent"])

        assert result.exit_code == 1


@pytest.mark.unit
@pytest.mark.cli
class TestInfoCommand:
    """Test the 'info' command."""

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_info_exact_match(
        self, mock_adb_class, mock_require, cli_runner, sample_package_info
    ):
        """Test info command with exact package name match."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.return_value = sample_package_info
        mock_adb.get_package_info.return_value = sample_package_info

        result = cli_runner.invoke(app, ["info", "com.example.test"])

        assert result.exit_code == 0
        mock_adb.get_package_info.assert_called_once_with("com.example.test")

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    @patch("batuta.cli.apk._select_package")
    def test_info_multiple_matches_interactive(
        self, mock_select, mock_adb_class, mock_require, cli_runner
    ):
        """Test info command with multiple matches triggers selection."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.side_effect = MultiplePackagesFoundError(
            "test", ["com.example.test1", "com.example.test2"]
        )

        packages = [
            PackageInfo(package_name="com.example.test1"),
            PackageInfo(package_name="com.example.test2"),
        ]
        mock_adb.search_packages.return_value = packages
        mock_select.return_value = [packages[0]]
        mock_adb.get_package_info.return_value = packages[0]

        result = cli_runner.invoke(app, ["info", "test"])

        assert result.exit_code == 0
        mock_select.assert_called_once()

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_info_json_output(
        self, mock_adb_class, mock_require, cli_runner, sample_package_info
    ):
        """Test info command with --json flag."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.return_value = sample_package_info
        mock_adb.get_package_info.return_value = sample_package_info

        result = cli_runner.invoke(app, ["info", "com.example.test", "--json"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["package_name"] == "com.example.test"
        assert output["version_name"] == "1.0.0"

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_info_package_not_found(self, mock_adb_class, mock_require, cli_runner):
        """Test info command when package not found."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.side_effect = PackageNotFoundError("nonexistent")

        result = cli_runner.invoke(app, ["info", "nonexistent"])

        assert result.exit_code == 1

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_info_with_split_apk(
        self, mock_adb_class, mock_require, cli_runner, sample_package_info_split
    ):
        """Test info command displays split APK information."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.return_value = sample_package_info_split
        mock_adb.get_package_info.return_value = sample_package_info_split

        result = cli_runner.invoke(app, ["info", "com.example.split"])

        assert result.exit_code == 0


@pytest.mark.unit
@pytest.mark.cli
class TestPullCommand:
    """Test the 'pull' command."""

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_pull_single_apk_success(
        self, mock_adb_class, mock_require, cli_runner, sample_pulled_apk
    ):
        """Test pulling a single APK successfully."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.return_value = PackageInfo(
            package_name="com.example.test"
        )
        mock_adb.pull_apk.return_value = sample_pulled_apk

        result = cli_runner.invoke(app, ["pull", "com.example.test"])

        assert result.exit_code == 0
        mock_adb.pull_apk.assert_called_once()

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_pull_split_apk_no_merge(
        self, mock_adb_class, mock_require, cli_runner, sample_pulled_apk_split
    ):
        """Test pulling split APK without merging."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.return_value = PackageInfo(
            package_name="com.example.split"
        )
        mock_adb.pull_apk.return_value = sample_pulled_apk_split

        result = cli_runner.invoke(app, ["pull", "com.example.split"])

        assert result.exit_code == 0

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    @patch("batuta.cli.apk.SplitAPKMerger")
    def test_pull_split_apk_auto_merge(
        self,
        mock_merger_class,
        mock_adb_class,
        mock_require,
        cli_runner,
        sample_pulled_apk_split,
        tmp_path,
    ):
        """Test pulling split APK with --auto-merge flag."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.return_value = PackageInfo(
            package_name="com.example.split"
        )
        mock_adb.pull_apk.return_value = sample_pulled_apk_split

        mock_merger = MagicMock()
        mock_merger_class.return_value = mock_merger
        merged_path = tmp_path / "merged.apk"
        merged_path.write_bytes(b"merged apk")
        mock_merger.merge.return_value = merged_path

        result = cli_runner.invoke(app, ["pull", "com.example.split", "--auto-merge"])

        assert result.exit_code == 0
        mock_merger.merge.assert_called_once()

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    @patch("batuta.cli.apk.APKDecompiler")
    def test_pull_with_decompile_flag(
        self,
        mock_decompiler_class,
        mock_adb_class,
        mock_require,
        cli_runner,
        sample_pulled_apk,
        sample_decompile_result,
    ):
        """Test pulling APK with --decompile flag."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.return_value = PackageInfo(
            package_name="com.example.test"
        )
        mock_adb.pull_apk.return_value = sample_pulled_apk

        mock_decompiler = MagicMock()
        mock_decompiler_class.return_value = mock_decompiler
        mock_decompiler.decompile.return_value = sample_decompile_result

        result = cli_runner.invoke(app, ["pull", "com.example.test", "--decompile"])

        assert result.exit_code == 0
        mock_decompiler.decompile.assert_called_once_with(java=True, smali=True)

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_pull_all_flag(self, mock_adb_class, mock_require, cli_runner, tmp_path):
        """Test pulling all packages matching filter with --all flag."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb

        packages = [
            PackageInfo(package_name="com.google.app1"),
            PackageInfo(package_name="com.google.app2"),
        ]
        mock_adb.search_packages.return_value = packages

        pull_results = [
            PulledAPK(
                package_name="com.google.app1",
                local_path=tmp_path / "app1.apk",
                is_split=False,
            ),
            PulledAPK(
                package_name="com.google.app2",
                local_path=tmp_path / "app2.apk",
                is_split=False,
            ),
        ]
        mock_adb.pull_apk.side_effect = pull_results

        result = cli_runner.invoke(app, ["pull", "google", "--all"])

        assert result.exit_code == 0
        assert mock_adb.pull_apk.call_count == 2

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    @patch("batuta.cli.apk._select_package")
    def test_pull_multiple_selection(
        self, mock_select, mock_adb_class, mock_require, cli_runner, tmp_path
    ):
        """Test pulling with interactive multiple selection."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.side_effect = MultiplePackagesFoundError(
            "test", ["com.example.test1", "com.example.test2"]
        )

        packages = [
            PackageInfo(package_name="com.example.test1"),
            PackageInfo(package_name="com.example.test2"),
        ]
        mock_adb.search_packages.return_value = packages
        mock_select.return_value = packages

        pull_results = [
            PulledAPK(
                package_name="com.example.test1",
                local_path=tmp_path / "test1.apk",
                is_split=False,
            ),
            PulledAPK(
                package_name="com.example.test2",
                local_path=tmp_path / "test2.apk",
                is_split=False,
            ),
        ]
        mock_adb.pull_apk.side_effect = pull_results

        result = cli_runner.invoke(app, ["pull", "test"])

        assert result.exit_code == 0
        assert mock_adb.pull_apk.call_count == 2

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_pull_json_output(
        self, mock_adb_class, mock_require, cli_runner, sample_pulled_apk
    ):
        """Test pull command with --json flag."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.return_value = PackageInfo(
            package_name="com.example.test"
        )
        mock_adb.pull_apk.return_value = sample_pulled_apk

        result = cli_runner.invoke(app, ["pull", "com.example.test", "--json"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["package_name"] == "com.example.test"
        assert "local_path" in output

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    @patch("batuta.cli.apk.APKDecompiler")
    def test_pull_java_only_decompile(
        self,
        mock_decompiler_class,
        mock_adb_class,
        mock_require,
        cli_runner,
        sample_pulled_apk,
        sample_decompile_result,
    ):
        """Test pull with --decompile --java-only flags."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.return_value = PackageInfo(
            package_name="com.example.test"
        )
        mock_adb.pull_apk.return_value = sample_pulled_apk

        mock_decompiler = MagicMock()
        mock_decompiler_class.return_value = mock_decompiler
        mock_decompiler.decompile.return_value = sample_decompile_result

        result = cli_runner.invoke(
            app, ["pull", "com.example.test", "--decompile", "--java-only"]
        )

        assert result.exit_code == 0
        mock_decompiler.decompile.assert_called_once_with(java=True, smali=False)

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    @patch("batuta.cli.apk.APKDecompiler")
    def test_pull_smali_only_decompile(
        self,
        mock_decompiler_class,
        mock_adb_class,
        mock_require,
        cli_runner,
        sample_pulled_apk,
        sample_decompile_result,
    ):
        """Test pull with --decompile --smali-only flags."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.find_package.return_value = PackageInfo(
            package_name="com.example.test"
        )
        mock_adb.pull_apk.return_value = sample_pulled_apk

        mock_decompiler = MagicMock()
        mock_decompiler_class.return_value = mock_decompiler
        mock_decompiler.decompile.return_value = sample_decompile_result

        result = cli_runner.invoke(
            app, ["pull", "com.example.test", "--decompile", "--smali-only"]
        )

        assert result.exit_code == 0
        mock_decompiler.decompile.assert_called_once_with(java=False, smali=True)

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.ADBWrapper")
    def test_pull_package_not_found(self, mock_adb_class, mock_require, cli_runner):
        """Test pull when package not found."""
        mock_adb = MagicMock()
        mock_adb_class.return_value = mock_adb
        mock_adb.search_packages.return_value = []

        result = cli_runner.invoke(app, ["pull", "nonexistent", "--all"])

        assert result.exit_code == 1

    def test_pull_mutually_exclusive_flags(self, cli_runner):
        """Test pull rejects --java-only and --smali-only together."""
        result = cli_runner.invoke(
            app, ["pull", "test", "--decompile", "--java-only", "--smali-only"]
        )

        assert result.exit_code == 1


@pytest.mark.unit
@pytest.mark.cli
class TestMergeCommand:
    """Test the 'merge' command."""

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.SplitAPKMerger")
    def test_merge_success(
        self, mock_merger_class, mock_require, cli_runner, temp_split_dir, tmp_path
    ):
        """Test merge command successfully merges split APKs."""
        mock_merger = MagicMock()
        mock_merger_class.return_value = mock_merger
        merged_path = tmp_path / "merged.apk"
        merged_path.write_bytes(b"merged apk")
        mock_merger.merge.return_value = merged_path

        result = cli_runner.invoke(app, ["merge", str(temp_split_dir)])

        assert result.exit_code == 0
        mock_merger.merge.assert_called_once()

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.SplitAPKMerger")
    def test_merge_custom_output(
        self, mock_merger_class, mock_require, cli_runner, temp_split_dir, tmp_path
    ):
        """Test merge command with custom output path."""
        mock_merger = MagicMock()
        mock_merger_class.return_value = mock_merger
        output_path = tmp_path / "custom.apk"
        mock_merger.merge.return_value = output_path

        result = cli_runner.invoke(
            app, ["merge", str(temp_split_dir), "--output", str(output_path)]
        )

        assert result.exit_code == 0
        mock_merger_class.assert_called_once_with(temp_split_dir, output_path)

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.SplitAPKMerger")
    def test_merge_json_output(
        self, mock_merger_class, mock_require, cli_runner, temp_split_dir, tmp_path
    ):
        """Test merge command with --json flag."""
        mock_merger = MagicMock()
        mock_merger_class.return_value = mock_merger
        merged_path = tmp_path / "merged.apk"
        merged_path.write_bytes(b"merged apk")
        mock_merger.merge.return_value = merged_path

        result = cli_runner.invoke(app, ["merge", str(temp_split_dir), "--json"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "split_dir" in output
        assert "output_path" in output

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.SplitAPKMerger")
    def test_merge_error_handling(
        self, mock_merger_class, mock_require, cli_runner, temp_split_dir
    ):
        """Test merge command handles errors gracefully."""
        mock_merger = MagicMock()
        mock_merger_class.return_value = mock_merger
        mock_merger.merge.side_effect = BatutaError("Merge failed")

        result = cli_runner.invoke(app, ["merge", str(temp_split_dir)])

        assert result.exit_code == 1


@pytest.mark.unit
@pytest.mark.cli
class TestDecompileCommand:
    """Test the 'decompile' command."""

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.APKDecompiler")
    def test_decompile_both_java_smali(
        self,
        mock_decompiler_class,
        mock_require,
        cli_runner,
        temp_apk_file,
        sample_decompile_result,
    ):
        """Test decompile command with both Java and smali."""
        mock_decompiler = MagicMock()
        mock_decompiler_class.return_value = mock_decompiler
        mock_decompiler.decompile.return_value = sample_decompile_result

        result = cli_runner.invoke(app, ["decompile", str(temp_apk_file)])

        assert result.exit_code == 0
        mock_decompiler.decompile.assert_called_once_with(java=True, smali=True)

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.APKDecompiler")
    def test_decompile_java_only(
        self,
        mock_decompiler_class,
        mock_require,
        cli_runner,
        temp_apk_file,
        sample_decompile_result,
    ):
        """Test decompile with --java-only flag."""
        mock_decompiler = MagicMock()
        mock_decompiler_class.return_value = mock_decompiler
        mock_decompiler.decompile.return_value = sample_decompile_result

        result = cli_runner.invoke(
            app, ["decompile", str(temp_apk_file), "--java-only"]
        )

        assert result.exit_code == 0
        mock_decompiler.decompile.assert_called_once_with(java=True, smali=False)

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.APKDecompiler")
    def test_decompile_smali_only(
        self,
        mock_decompiler_class,
        mock_require,
        cli_runner,
        temp_apk_file,
        sample_decompile_result,
    ):
        """Test decompile with --smali-only flag."""
        mock_decompiler = MagicMock()
        mock_decompiler_class.return_value = mock_decompiler
        mock_decompiler.decompile.return_value = sample_decompile_result

        result = cli_runner.invoke(
            app, ["decompile", str(temp_apk_file), "--smali-only"]
        )

        assert result.exit_code == 0
        mock_decompiler.decompile.assert_called_once_with(java=False, smali=True)

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.APKDecompiler")
    def test_decompile_custom_output_dir(
        self,
        mock_decompiler_class,
        mock_require,
        cli_runner,
        temp_apk_file,
        sample_decompile_result,
        tmp_path,
    ):
        """Test decompile with custom output directory."""
        mock_decompiler = MagicMock()
        mock_decompiler_class.return_value = mock_decompiler
        mock_decompiler.decompile.return_value = sample_decompile_result
        output_dir = tmp_path / "custom_output"

        result = cli_runner.invoke(
            app, ["decompile", str(temp_apk_file), "--output", str(output_dir)]
        )

        assert result.exit_code == 0
        mock_decompiler_class.assert_called_once_with(temp_apk_file, output_dir)

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.APKDecompiler")
    def test_decompile_json_output(
        self,
        mock_decompiler_class,
        mock_require,
        cli_runner,
        temp_apk_file,
        sample_decompile_result,
    ):
        """Test decompile with --json flag."""
        mock_decompiler = MagicMock()
        mock_decompiler_class.return_value = mock_decompiler
        mock_decompiler.decompile.return_value = sample_decompile_result

        result = cli_runner.invoke(app, ["decompile", str(temp_apk_file), "--json"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "apk_path" in output
        assert "output_dir" in output
        assert output["java_success"] is True
        assert output["smali_success"] is True

    def test_decompile_mutually_exclusive_flags(self, cli_runner, temp_apk_file):
        """Test decompile rejects both --java-only and --smali-only."""
        result = cli_runner.invoke(
            app, ["decompile", str(temp_apk_file), "--java-only", "--smali-only"]
        )

        assert result.exit_code == 1

    @patch("batuta.cli.apk.require")
    @patch("batuta.cli.apk.APKDecompiler")
    def test_decompile_partial_failure(
        self,
        mock_decompiler_class,
        mock_require,
        cli_runner,
        temp_apk_file,
        tmp_path,
    ):
        """Test decompile when one decompiler fails."""
        mock_decompiler = MagicMock()
        mock_decompiler_class.return_value = mock_decompiler

        # Java succeeds, smali fails
        partial_result = DecompileResult(
            apk_path=temp_apk_file,
            output_dir=tmp_path / "output",
            java_dir=tmp_path / "output" / "java",
            smali_dir=None,
            java_success=True,
            smali_success=False,
        )
        mock_decompiler.decompile.return_value = partial_result

        result = cli_runner.invoke(app, ["decompile", str(temp_apk_file)])

        assert result.exit_code == 0  # Partial success is still success


@pytest.mark.unit
@pytest.mark.cli
class TestPatchCommand:
    """Test the 'patch' command."""

    @patch("batuta.cli.apk.require")
    @patch("batuta.core.patcher.APKPatcher")
    def test_patch_basic_success(
        self,
        mock_patcher_class,
        mock_require,
        cli_runner,
        temp_apktool_dir,
        sample_patch_result,
    ):
        """Test basic patch command."""
        mock_patcher = MagicMock()
        mock_patcher_class.return_value = mock_patcher
        mock_patcher.patch.return_value = sample_patch_result

        result = cli_runner.invoke(app, ["patch", str(temp_apktool_dir)])

        assert result.exit_code == 0
        mock_patcher.patch.assert_called_once()

    @patch("batuta.cli.apk.require")
    @patch("batuta.core.patcher.APKPatcher")
    def test_patch_custom_output(
        self,
        mock_patcher_class,
        mock_require,
        cli_runner,
        temp_apktool_dir,
        sample_patch_result,
        tmp_path,
    ):
        """Test patch with custom output path."""
        mock_patcher = MagicMock()
        mock_patcher_class.return_value = mock_patcher
        mock_patcher.patch.return_value = sample_patch_result
        output_path = tmp_path / "custom.apk"

        result = cli_runner.invoke(
            app, ["patch", str(temp_apktool_dir), "--output", str(output_path)]
        )

        assert result.exit_code == 0
        mock_patcher_class.assert_called_once_with(temp_apktool_dir, output_path)

    @patch("batuta.cli.apk.require")
    @patch("batuta.core.patcher.APKPatcher")
    def test_patch_custom_keystore(
        self,
        mock_patcher_class,
        mock_require,
        cli_runner,
        temp_apktool_dir,
        sample_patch_result,
        tmp_path,
    ):
        """Test patch with custom keystore."""
        mock_patcher = MagicMock()
        mock_patcher_class.return_value = mock_patcher
        mock_patcher.patch.return_value = sample_patch_result
        keystore = tmp_path / "custom.keystore"
        keystore.write_bytes(b"fake keystore")

        result = cli_runner.invoke(
            app,
            [
                "patch",
                str(temp_apktool_dir),
                "--keystore",
                str(keystore),
                "--key-alias",
                "mykey",
                "--keystore-pass",
                "mypass",
                "--key-pass",
                "keypass",
            ],
        )

        assert result.exit_code == 0
        call_kwargs = mock_patcher.patch.call_args[1]
        assert call_kwargs["keystore"] == keystore
        assert call_kwargs["key_alias"] == "mykey"

    @patch("batuta.cli.apk.require")
    @patch("batuta.core.patcher.APKPatcher")
    def test_patch_no_sign_no_align(
        self,
        mock_patcher_class,
        mock_require,
        cli_runner,
        temp_apktool_dir,
        sample_patch_result,
    ):
        """Test patch with --no-sign and --no-align flags."""
        mock_patcher = MagicMock()
        mock_patcher_class.return_value = mock_patcher
        mock_patcher.patch.return_value = sample_patch_result

        result = cli_runner.invoke(
            app, ["patch", str(temp_apktool_dir), "--no-sign", "--no-align"]
        )

        assert result.exit_code == 0
        call_kwargs = mock_patcher.patch.call_args[1]
        assert call_kwargs["sign"] is False
        assert call_kwargs["align"] is False

    @patch("batuta.cli.apk.require")
    @patch("batuta.core.patcher.APKPatcher")
    def test_patch_with_verify(
        self,
        mock_patcher_class,
        mock_require,
        cli_runner,
        temp_apktool_dir,
        sample_patch_result,
    ):
        """Test patch with --verify flag."""
        mock_patcher = MagicMock()
        mock_patcher_class.return_value = mock_patcher
        mock_patcher.patch.return_value = sample_patch_result

        result = cli_runner.invoke(app, ["patch", str(temp_apktool_dir), "--verify"])

        assert result.exit_code == 0
        call_kwargs = mock_patcher.patch.call_args[1]
        assert call_kwargs["verify_signature"] is True

    @patch("batuta.cli.apk.require")
    @patch("batuta.core.patcher.APKPatcher")
    @patch("batuta.utils.process.run_tool")
    def test_patch_with_install(
        self,
        mock_run_tool,
        mock_patcher_class,
        mock_require,
        cli_runner,
        temp_apktool_dir,
        sample_patch_result,
    ):
        """Test patch with --install flag."""
        mock_patcher = MagicMock()
        mock_patcher_class.return_value = mock_patcher
        mock_patcher.patch.return_value = sample_patch_result

        result = cli_runner.invoke(app, ["patch", str(temp_apktool_dir), "--install"])

        assert result.exit_code == 0
        mock_run_tool.assert_called_once()
        assert "adb" in mock_run_tool.call_args[0][0]
        assert "install" in mock_run_tool.call_args[0][0]

    @patch("batuta.cli.apk.require")
    @patch("batuta.core.patcher.APKPatcher")
    def test_patch_json_output(
        self,
        mock_patcher_class,
        mock_require,
        cli_runner,
        temp_apktool_dir,
        sample_patch_result,
    ):
        """Test patch with --json flag."""
        mock_patcher = MagicMock()
        mock_patcher_class.return_value = mock_patcher
        mock_patcher.patch.return_value = sample_patch_result

        result = cli_runner.invoke(app, ["patch", str(temp_apktool_dir), "--json"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "source_dir" in output
        assert "output_path" in output
        assert output["signed"] is True
        assert output["aligned"] is True

    @patch("batuta.cli.apk.require")
    @patch("batuta.core.patcher.APKPatcher")
    def test_patch_build_error(
        self, mock_patcher_class, mock_require, cli_runner, temp_apktool_dir
    ):
        """Test patch handles build errors."""
        mock_patcher = MagicMock()
        mock_patcher_class.return_value = mock_patcher
        mock_patcher.patch.side_effect = BatutaError("Build failed")

        result = cli_runner.invoke(app, ["patch", str(temp_apktool_dir)])

        assert result.exit_code == 1
