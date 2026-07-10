# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.1] - 2026-06-16
### Fixed
- Resolved a security vulnerability that allowed users to bypass the password check during authentication. Proper validation has been implemented on the login route.

## [1.8.0] - 2026-04-08
### Added
- Created comprehensive documentation for all application routes to better explain the backend structure.
- Introduced several significant enhancements to the polling system.
- Added free response question capabilities to the polling system, allowing members to provide custom text answers.
- Added support for multi-response questions, enabling users to select more than one option when voting.
### Changed
- Improved the administrative poll management user interface to make viewing results and managing questions easier.

## [1.7.0] - 2026-03-11
### Added
- Added new `.env` configuration settings to enforce email domain requirements during user registration (e.g., restricting to specific organization domains).
- Implemented logic and forms for non-email signups to handle special edge cases.
### Changed
- Removed redundant configuration fields in the environment file to streamline the deployment process.

## [1.6.0] - 2026-03-07
### Added
- Deployed a major update to the polling system that allows users to vote directly from the main page.
- Added new controls to the administrative dashboard for creating and deleting polls from the web interface.
- Separated the contributing and development documentation into distinct files to improve readability for new developers.
- Expanded the API and main route documentation to provide more detail for future frontend work.

## [1.5.0] - 2026-02-17
### Added
- Implemented database migration support using Flask-Migrate to simplify rolling out future schema changes.
- Added user activation requirements, preventing unactivated users from checking into meetings.
- Added a pre-login activation status check so users are notified if their account is pending approval.
- Implemented confirmation popups for saving meeting minutes and updating account details to prevent accidental data loss.
- Added more detailed user statistics to the administrative dashboard to track engagement over time.
### Changed
- Migrated nearly all forms (including login, registration, and check-in) to use Flask-WTF to improve security and validation.
- Applied major code styling and linter improvements across the codebase to increase the overall quality score.
### Fixed
- Fixed intermittent CSRF validation issues on the administrative dashboard that caused form submissions to fail.
- Prevented administrators from accidentally demoting themselves while editing user roles.
- Resolved 404 errors caused by file uploads with spaces in their filenames by automatically converting spaces to underscores.
- Fixed missing newlines and date formatting bugs in the meeting minutes view.

## [1.4.0] - 2025-10-17
### Added
- Introduced multi-factor authentication (MFA) via TOTP, supporting applications like Authy or Google Authenticator.
- Added backup recovery code generation for MFA to provide account access if a user loses their authenticator device.
- Added new environment configuration options to enforce specific email domains across the application.

## [1.3.0] - 2025-10-13
### Added
- Implemented meeting attachments and file uploads functionality, allowing presenters to share files directly on the meeting page.
- Created a basic administrative user index to facilitate promoting and demoting users directly from the UI.
- Configured GitHub Actions CI/CD pipelines to automate testing and application builds.
- Added Pylint score checking to pull requests to maintain code quality standards.

## [1.2.0] - 2025-10-06
### Added
- Added an on-demand database backup utility for administrators to easily download the current database state.
### Changed
- Migrated the primary database from SQLite to PostgreSQL to improve reliability and concurrency in production environments.
- Refactored the backend structure to utilize a Flask application factory architecture, improving testing and deployment flexibility.
- Upgraded the password hashing mechanism to use the more secure scrypt algorithm.

## [1.1.0] - 2025-09-30
### Added
- Added logic for creating admin-only meetings that restrict visibility and check-ins for standard users.
- Implemented user promotion and demotion capabilities directly from the database level.

## [1.0.0] - 2025-09-10
### Added
- Initial release of the ACM Meeting Records web application.
- Implemented core account management features, including user sign-up, login, and account detail viewing.
- Added a dynamic homepage featuring a meeting check-in form.
- Created administrative dashboards for managing meetings, attendees, and statuses.
- Configured custom error pages for application stability.
- Containerized the application using Docker and Docker Compose, utilizing persistent volumes for database stability.
- Implemented comprehensive logging for application events and user account actions.
- Published initial documentation suite, including a README and quickstart guide.
