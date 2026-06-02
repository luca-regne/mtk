# mtk

> **mtk — mobile toolkit.** One CLI to pull apart, inspect, and tamper with mobile apps. Android today; iOS and device management on the way.

`mtk` is a Python CLI and library for mobile application security work — designed for penetration testers, bug bounty hunters, and malware analysts. It wraps battle-tested tooling behind a clean, composable, scriptable interface so you can move between pulling, decompiling, analyzing, and patching without juggling a dozen commands.

Today `mtk` ships full Android/APK support. iOS/IPA analysis and broader device management are actively planned — see [Roadmap](#roadmap--planned).

---

## Platform Support

| Platform               | Status                                            |
| ---------------------- | ------------------------------------------------- |
| **Android (APK)**      | ✅ Available — pull, merge, decompile, analyze, patch |
| **iOS (IPA)**          | 🚧 Planned (roadmap)                              |
| **Device management**  | 🟡 Partial — Android via `adb` today; iOS planned |

> `mtk` was previously named **`batuta`**. The `batuta` command still works as a deprecated alias and will be removed in the next major release. The config directory moved from `~/.batuta` to `~/.mtk` (the old location is read as a fallback).

---

## Available Now — Android

### Features

- **APK pulling** — pull APKs by package name, app name, or filter pattern
- **Split APK support** — automatically detects split packages, pulls every part, and merges them via `mtk apk merge` or `--auto-merge`
- **Decompilation** — run `jadx` and/or `apktool` via `mtk apk decompile` or `mtk apk pull --decompile`
- **APK patching** — rebuild, align, sign, and optionally install via `mtk apk patch`
- **Framework detection** — detect cross-platform frameworks (Flutter, React Native, Xamarin, Cordova, Unity) via `mtk analyze framework`
- **Manifest analysis** — inspect components, permissions, and attack surface via `mtk analyze manifest`
- **Interactive selection** — choose from multiple matches when searching (prompted automatically)
- **Scriptable by design** — every command supports `--json` output for piping into `jq`, `grep`, or custom tooling
- **Library-first architecture** — core logic is importable independently of the CLI

### Requirements

**Python** >= 3.14

**External tools** — these must be installed and available on your `PATH`:

| Tool        | Purpose                                     | Install                                                                                   |
| ----------- | ------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `adb`       | Android Debug Bridge — device communication | [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools) |
| `apktool`   | APK decoding, smali disassembly             | [Apktool Website](https://apktool.org/)                                                   |
| `jadx`      | Java/Kotlin decompilation                   | [Jadx GitHub Repository](https://github.com/skylot/jadx)                                  |
| `APKEditor` | Split APK merging                           | [APKEditor Repository](https://github.com/REAndroid/APKEditor)                            |

`mtk` checks for required tools at command entry and reports clear installation instructions when missing.

### Configuring APKEditor

`APKEditor` ships as a JAR file. `mtk` resolves it in this order:

1. `APKEDITOR_JAR` environment variable (points to the `.jar` or its parent directory)
2. `~/.mtk/config.json` → `apkeditor_path` (falls back to `~/.batuta/config.json` if present)
3. Executable wrapper called `APKEditor` somewhere on `PATH`

Examples:

```bash
# 1. Environment variable (temporary for current shell)
export APKEDITOR_JAR="$HOME/tools/APKEditor/APKEditor.jar"

# 2. Config file (~/.mtk/config.json)
{
  "apkeditor_path": "~/tools/APKEditor/APKEditor.jar"
}

# 3. Wrapper script placed on PATH (e.g., /usr/local/bin/APKEditor)
#!/bin/bash
exec java -jar "$HOME/tools/APKEditor/APKEditor.jar" "$@"
```

You can point `apkeditor_path` to either the JAR file itself or the directory
containing `APKEditor.jar`. `mtk` keeps the pulled split directory intact after
merging, regardless of the resolution method you use.

---

## Installation

Install from source with uv:

```bash
git clone https://github.com/luca-regne/mtk
cd mtk
uv sync
```

Or with pip:

```bash
pip install -e .
```

---

## Quick Start

```bash
# List connected devices
mtk device list

# Search for packages by name
mtk apk search google

# Get detailed info about a package
mtk apk info com.example.app

# Pull an APK (supports partial names and filters)
mtk apk pull youtube

# Pull to a specific directory
mtk apk pull com.example.app --output ./apks/

# Pull and immediately decompile
mtk apk pull com.example.app --decompile

# Standalone decompile from local APK
mtk apk decompile ./apks/com.example.app.apk --java-only

# Merge a split APK directory (keeps original files)
mtk apk merge ./apks/com.example.app --output ./apks/com.example.app.merged.apk

# Detect cross-platform frameworks
mtk analyze framework ./apks/com.example.app.apk

# Framework detection with JSON output
mtk analyze framework ./apks/com.example.app.apk --json
```

> The command layout is evolving as iOS support lands — see [Roadmap](#roadmap--planned).

---

## Command Reference

> These are today's commands (Android only). iOS commands and a revised top-level layout are planned.

```
mtk
├── analyze
│   ├── framework <apk>            Detect cross-platform frameworks in APK
│   └── manifest <apk>             Parse AndroidManifest.xml (components, permissions, attack surface)
│
├── device
│   ├── list                       List connected ADB devices
│   └── shell [COMMAND...]         Open ADB shell (or run command)
│
└── apk
    ├── list                       List installed packages
    ├── search <query>             Search packages by name or filter
    ├── info <query>               Show detailed package information
    ├── pull <query>               Pull APK from connected device (optional decompile)
    ├── merge <dir>                Merge split APK folder into a single APK (keeps folder)
    ├── patch <apktool-dir>        Build/align/sign APK from apktool output
    └── decompile <apk>            Decompile APK to Java and/or smali
```

### Common Options

| Option           | Description                                        |
| ---------------- | -------------------------------------------------- |
| `--device`, `-d` | Target specific device by ID                       |
| `--json`, `-j`   | Output as JSON for scripting                       |
| `--system`, `-s` | Include system packages in search                  |
| `--decompile`    | (pull) Decompile after pulling (Java + smali)      |
| `--auto-merge`   | (pull) Merge split APK folders via APKEditor       |
| `--java-only`    | (pull/decompile) Limit to Java (`jadx`) output     |
| `--smali-only`   | (pull/decompile) Limit to smali/resources (`apktool`) |

Split APK pulls always save the original directory of base/split parts.
Use `--auto-merge` for immediate merging (the folder stays untouched) or
run `mtk apk merge <dir>` later. When `--decompile` is supplied, splits
are merged automatically so jadx/apktool can run without extra steps.

### Examples

```bash
# JSON output for scripting
mtk device list --json | jq '.[0].id'
mtk apk search facebook --json | jq '.[].package_name'

# Target specific device
mtk apk pull com.example.app --device RX8WC00D7JE

# Include system packages
mtk apk list --system --filter android
```

---

## Roadmap / Planned

These capabilities are **not yet implemented**. They define the direction of `mtk` as a multi-platform mobile toolkit — issues and PRs welcome.

- **iOS / IPA analysis** — `Info.plist` parsing, entitlements inspection, framework detection, and IPA repack/resign workflows.
- **Expanded device management** — iOS device support, app install/uninstall, and on-device file transfer across both platforms.
- **Unified cross-platform surface** — a top-level command layout that treats Android and iOS as first-class peers.

---

## Library Usage

The core logic is importable independently of the CLI:

```python
from mtk.core.adb import ADBWrapper

# List devices
adb = ADBWrapper()
devices = adb.list_devices()
for device in devices:
    print(f"{device.id}: {device.model} ({device.state})")

# Search packages
packages = adb.search_packages("google")
for pkg in packages:
    print(f"{pkg.package_name} v{pkg.version_name}")

# Pull an APK
result = adb.pull_apk("com.example.app", output_dir=Path("./apks"))
print(f"Pulled to: {result.local_path}")
```

---

## Architecture

```
src/mtk/
├── cli/          # Typer commands — argument parsing and rich output only
├── core/         # Business logic — importable as a library
├── models/       # Pydantic v2 data models
├── utils/        # Shared utilities: deps checker, output helpers, process wrapper
└── exceptions.py # Typed exception hierarchy
```

Key architectural constraints:

- `cli/` never contains business logic — only calls into `core/`
- All subprocess invocations go through `utils/process.py`
- All external tool requirements are checked at command entry via `utils/deps.py`

---

## Development

```bash
# Install with dev dependencies
uv sync --group dev

# Lint
ruff check src/mtk/

# Auto-fix lint issues
ruff check src/mtk/ --fix

# Type check
mypy src/mtk/

# Run the CLI
uv run mtk --help
```

---

## Release Process

This project uses automated release management with conventional commits.

### For Maintainers

**Creating a Release:**

```bash
# Patch release (bug fixes): 1.0.0 -> 1.0.1
./scripts/release.sh patch

# Minor release (new features): 1.0.0 -> 1.1.0
./scripts/release.sh minor

# Major release (breaking changes): 1.0.0 -> 2.0.0
./scripts/release.sh major
```

The script will:
1. Validate working directory is clean
2. Run lint and type checks
3. Bump version in `pyproject.toml`
4. Update `CHANGELOG.md`
5. Create git commit and tag
6. Push to GitHub

GitHub Actions will then:
1. Run full validation suite
2. Build package
3. Publish to PyPI
4. Create GitHub Release with artifacts

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and workflow, and [COMMIT_CONVENTION.md](.github/COMMIT_CONVENTION.md) for the commit format.

All commits must follow [Conventional Commits](https://www.conventionalcommits.org/).

**Setup pre-commit hooks:**

```bash
pip install pre-commit
pre-commit install --hook-type commit-msg
```

**Required tools for releases:**

```bash
# macOS
brew install git-cliff

# Linux
cargo install git-cliff
```
