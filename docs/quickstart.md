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
3. Copy the .env.example file to a .env file.
4. Run the following command to start the webserver:
  ```sh
  docker compose up --build -d
  ```
5. Run the following commands to initialize the database:
  ```sh
  docker compose exec web flask db init
  docker compose exec web flask db migrate -m "Initial database schema"
  docker compose exec web flask db upgrade
  ```
5. Set up CLI for SQLITE3:
  ```sh
  sudo apt update
  sudo apt-get install sqlite3
  ```
6. Run the ```sql_manage_users.py``` utility to generate SQL queries to add administrator(s) to the SQLITE database.
Execute these queries on the database via the psql CLI within docker exec.
Please note, the passwords are stored in a SHA 256 hash, so you cannot manually edit the database to update a password. You must either:
* Go through the web UI
* Create a SHA 256 hash of the password first, then use that to update the database.


<p align="right">(<a href="#readme-top">back to top</a>)</p>
