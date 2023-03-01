# Changelog

## [Unreleased]

---

## [0.2.0] - 2023-03-01

### Changed
- `Twitter` and `TwitterUpload` are no longer `AsyncInit` and should not be awaited.
- Renamed:
    - `Tweet.author_username` -> `Tweet.author_at`
- `Twitter` and `TwitterV2` accept a single `OAuth1` and `OAuth2` object, respectively.

### Added
- `TwitterV2`

### Removed
- `Tweet.delete()`; use `Twitter.delete()` instead
- `Media.add_alt_text()`; use `Twitter.add_alt_text()` instead

## [0.1.2] - 2023-02-26

### Added
- `Twitter` contructor accepts paths to auth files

## [0.1.1] - 2023-02-23

### Changed
- Files too large to tweet are not downloaded if provided as a URL

### Added
- `quote_tweet` accepts media

## [0.1.0] - 2022-02-21

Initial release.