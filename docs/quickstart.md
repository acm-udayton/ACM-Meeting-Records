<a id="readme-top"></a>
<!-- PROJECT HEADER -->
<br />
<div align="center">
<h3 align="center">Quick Start - ACM Meeting Records</h3>
  <p align="center">
    An administrator's gudie to the web app system for recording attendance and notes for ACM meetings.
    <br />
  </p>
</div>

<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Installation

1. Ensure that Docker is installed on your system and the ```docker compose``` command is available.
2. Download the source code for the project to a directory on your filesystem & navigate there in your terminal.
3. Copy the .env.example file to a .env file and replace all placeholder data to include the following variables with the appropriate values for your organization and application configuration:

| .env Variable | Description |
| --- | --- |
| BASE_URL | The base URL for the web app. |
| GITHUB_SOURCE | The URL for the application's GitHub repository. |
| LINKEDIN_URL | The URL for the organization's LinkedIn page. |
| INSTAGRAM_URL | The URL for the organization's Instagram page. |
| GITHUB_URL | The URL for the organization's GitHub page. |
| ORGANIZATION_NAME | The name of the organization. |
| MEETING_LOCATION | The location of the meetings. |
| CONTACT_EMAIL | The contact email for the organization. |
| ENFORCE_USERNAMES | Whether to enforce username email domain restriction. Set to "True" to enforce, "False" to not enforce. |
| USERNAME_EMAIL_DOMAIN | The email domain to restrict usernames to, if ENFORCE_USERNAMES is set to "True". |
| SQLALCHEMY_DATABASE_URI | The URI for the PostgreSQL database. This should be in the format: "postgresql://admin:password@db:5432/acm-meetings-db" where "password" is replaced with the password you set for the PostgreSQL database in the docker-compose.yml file. |
| SECRET_KEY | A secret key for the Flask application. This can be any random string. |
| RECAPTCHA_SITE_KEY | The site key for Google reCAPTCHA. This is required to enable the reCAPTCHA on the user registration page. You can obtain a site key by registering your site with Google reCAPTCHA at https://www.google.com/recaptcha/admin/create. |
| RECAPTCHA_SECRET_KEY | The secret key for Google reCAPTCHA. This is required to enable the reCAPTCHA on the user registration page. Obtain this key when obtaining the above `RECAPTCHA_SITE_KEY`. |

4. Run the following command to start the webserver:
  ```sh
  docker compose up --build -d
  ```
5. Run the ```sql_manage_users.py``` utility to generate SQL query to add the first administrator to the PostgreSQL database. Run the SQL query via psql in the docker container, accessed via this command:
```sh
docker exec -it acm-meeting-records-db psql -U admin -d acm-meetings-db
```
All future administrator accounts can be created as user accounts and promoted by your first administrator.

<hr>

### Upgrades
For information on upgrading to a new version of ACM Meeting Records, please refer to the <a href="upgrading.md">upgrading.md</a> file.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
