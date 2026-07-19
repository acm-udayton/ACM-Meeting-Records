# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.2] - 2026-07-15

### Security

- Prevented the MFA verification step from being reached after failed password or account-activation checks.

## [1.8.1] - 2026-06-16

### Security

- Prevented standard-login users from being authenticated after failed password or account-activation checks.

## [1.8.0] - 2026-04-08

### Added

- Added poll expiration, immutable questions, optional hidden vote counts, and summary metrics on the administrator user dashboard.

### Fixed

- Stopped showing poll forms to signed-out users and allowed users to remove their final selection from multi-response questions.
- Corrected the administrator MFA warning styling.
- Corrected a typo in the quickstart documentation.

## [1.7.1] - 2026-03-11

### Fixed

- Fixed a login error caused by nonexistent usernames.

## [1.7.0] - 2026-03-11

### Added

- Added an environment setting that allows non-email usernames during registration.

### Changed

- Expanded `.env` setup documentation, removed obsolete settings, and mounted the application `.env` file into the Docker container.

## [1.6.0] - 2026-03-07

### Added

- Introduced the polling system with multiple-choice, free-response, and multi-response questions, administrative management, results, and home-page voting.
- Added contributor and development documentation for setup, architecture, routes, extensions, CI/CD, and database migrations.

### Changed

- Improved feedback when saving meeting minutes or updating account details and pre-populated account forms with saved data.

### Fixed

- Fixed meeting-minute formatting and uploaded attachment filenames containing spaces.

## [1.5.0] - 2026-02-17

### Added

- Added TOTP multi-factor authentication with recovery codes and administrative MFA controls.
- Added reCAPTCHA, email validation, administrator approval, and activation checks for new accounts.
- Added attendance totals and latest check-in dates to the administrator user dashboard.

### Changed

- Migrated application forms to Flask-WTF and standardized database upgrades on Flask-Migrate.

### Fixed

- Prevented administrators from demoting their own accounts.

## [1.4.0] - 2025-10-17

### Added

- Added configurable email-domain enforcement for usernames.

### Changed

- Generalized organization-specific configuration, masked password fields, and increased the Gunicorn worker count.

### Fixed

- Corrected meeting ordering.

## [1.3.0] - 2025-10-13

### Added

- Refactored the application into a Flask application factory with separate blueprints.
- Added meeting attachments and administrative controls for meetings, attendees, passwords, and user roles.
- Added GitHub Actions workflows for Pylint enforcement and Docker image publishing.

### Fixed

- Fixed crashes when creating a meeting without selecting the admin-only option.
- Fixed public meetings being hidden from administrators.

## [1.2.0] - 2025-10-06

### Added

- Added an on-demand PostgreSQL backup utility.

### Changed

- Migrated the application database from SQLite to PostgreSQL.
- Replaced unsalted SHA3-512 password hashes with salted scrypt hashes.

## [1.1.0] - 2025-09-30

### Added

- Moved administrator role management into the database and added admin-only meetings.

### Fixed

- Prevented duplicate meeting check-ins.

## [1.0.0] - 2025-09-10

### Added

- Released the initial application with account management, meeting check-in and history, administrative meeting controls, and API endpoints.
- Added Docker deployment, persistent database storage, application logging, and the initial README and quickstart documentation.

[1.8.2]: https://github.com/acm-udayton/ACM-Meeting-Records/releases/tag/v1.8.2
[1.8.1]: https://github.com/acm-udayton/ACM-Meeting-Records/releases/tag/v1.8.1
[1.8.0]: https://github.com/acm-udayton/ACM-Meeting-Records/releases/tag/v1.8
[1.7.1]: https://github.com/acm-udayton/ACM-Meeting-Records/compare/v1.7...6500e40f4f5180543766e7d8d05d7da1b37bc61d
[1.7.0]: https://github.com/acm-udayton/ACM-Meeting-Records/releases/tag/v1.7
[1.6.0]: https://github.com/acm-udayton/ACM-Meeting-Records/releases/tag/v1.6
[1.5.0]: https://github.com/acm-udayton/ACM-Meeting-Records/releases/tag/v1.5
[1.4.0]: https://github.com/acm-udayton/ACM-Meeting-Records/releases/tag/v1.4
[1.3.0]: https://github.com/acm-udayton/ACM-Meeting-Records/releases/tag/v1.3
[1.2.0]: https://github.com/acm-udayton/ACM-Meeting-Records/releases/tag/v1.2
[1.1.0]: https://github.com/acm-udayton/ACM-Meeting-Records/releases/tag/v1.1
[1.0.0]: https://github.com/acm-udayton/ACM-Meeting-Records/releases/tag/v1.0
