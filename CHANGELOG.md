# Changelog

## [Unreleased]

### Changed
- `Twitter` and `TwitterUpload` are no longer `AsyncInit` and should not be awaited.
- Renamed:
    - `Tweet.author_username` -> `Tweet.author_at`

### Added
- `TwitterV2`

### Removed
- `Tweet.delete()`; use `Twitter.delete()` instead
- `Media.add_alt_text()`; use `Twitter.add_alt_text()` instead