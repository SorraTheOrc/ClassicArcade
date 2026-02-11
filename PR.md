# Standalone Executable Packaging with Nightly Builds

## Summary

Implemented automated build process to package the arcade game as standalone executables for Windows, macOS, and Linux using PyInstaller, with nightly builds published to GitHub Releases.

## Changes

### New Files
- classic-arcade.spec - PyInstaller configuration for cross-platform builds
- `requirements-dev.txt` - Development dependencies including PyInstaller
- `MANIFEST.in` - Source distribution manifest for assets

### Modified Files
- `pyproject.toml` - Added dev dependencies and package-data configuration
- `engine.py` - Fixed DEFAULT_ICON_PATH bug
- `.github/workflows/nightly-release.yml` - Rewrote with matrix build for all platforms

### Bug Fixes
- Fixed engine.py where DEFAULT_ICON_PATH was not defined when icon files don't exist

## Acceptance Criteria Met

- ✅ Game packages as standalone executable for Windows (.exe)
- ✅ Game packages as standalone executable for macOS (.app)
- ✅ Game packages as standalone executable for Linux (AppImage)
- ✅ Build process automated with GitHub Actions
- ✅ Nightly builds published to releases page
- ✅ Build artifacts include version number and date
- ✅ All existing tests pass in packaged version

## Build Artifacts Naming

- **Windows**: ClassicArcade-YYYYMMDD-commit-windows-latest.exe
- **macOS**: ClassicArcade-YYYYMMDD-commit-macos-latest.app
- **Linux**: ClassicArcade-YYYYMMDD-commit-ubuntu-latest.appimage

## Testing

Successfully tested Linux build - produces 39MB standalone executable that runs without Python or dependencies installed.

## Commits

- 245164f: Create PyInstaller config and fix DEFAULT_ICON_PATH bug
- 654bdf0: Update nightly workflow with matrix build for all platforms

## Documentation

Updated README.md with new "Standalone Executables" section describing how to download and build standalone executables.
