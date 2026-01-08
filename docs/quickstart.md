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
3. Copy the .env.example file to a .env file and replace all placeholder data.
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
