<a id="development-top"></a>
<!-- PROJECT HEADER -->
<br />
<div align="center">
<h3 align="center">Development - ACM Meeting Records</h3>
  <p align="center">
    A developer's guide to the technical architecture and environment.
    <br />
  </p>
</div>

<!-- GETTING STARTED -->
### Developer Tooling

As you begin contributing to the ACM Meeting Records project, we recommend the following tools. Other tools may be used, but these are the project standards and we cannot guarantee that we will provide support for developers using other non-recommended developer tools.
1. [Docker Desktop](https://www.docker.com/products/docker-desktop/). Please note, technically you only need to ensure that Docker is installed on your system and the ```docker compose``` command is available, but for maximum debugging ease Docker desktop is the only recommended developer tooling in this category.
2. [Visual Studio Code](https://code.visualstudio.com/)
3. [DBeaver](https://dbeaver.io/)

<hr>

### Installation & Database Access Setup

Follow the standard installation procedure outlined in <a href="quickstart.md">quickstart.md</a> to begin the setup process. 

Next, you will need to add your DBeaver database connection. Be sure to select postgresql as your database, and fill out the details with the username, password, and port specified in the docker-compose.yml file, with localhost as the host. You can then find the database tables at ```Databases -> acm-meetings-db -> Schemas -> public -> Tables``` within DBeaver's Database Navigator pane.

<hr>

### FAQ

Running into a problem or not sure how to proceed? Before reaching out to someone else on the development team, check out these common questions and solutions!

<details>
<summary><strong>Database errors on web container startup - duplicates, invalid entries, etc. </strong></summary>
<br />
The database is likely crashing due to updated web app source code expecting a different schema (or even a new schema) in the database but not finding it. This can manifest in many types of errors output to the web container console, but they are often large and messy. These are especially common when making changes to the models.py or switching between branches.

We use flask-migrate for database management, so if you don't explicitly tell flask-migrate that your database needs updated, you can end up with an outdated or broken schema. First, check your database for an alembic_version table and look at the version_number column entry. Now search that ID in the source code in the project's ```migrations/versions directory```. If you find a file with the following line
```
Revises: your_version_number
```
a newer migration exists already, but hasn't been applied automatically. If however, you don't see any such file, you likely need to create a new migration file. To do this, run the following terminal commands while your db container is running. Be sure to replace the "<your upgrade message here>" message with a string that provides a clearer description of what the database model changes are.
```
docker compose build web
docker compose run --rm web flask db migrate -m "<your upgrade message here>"
docker compose run --rm web flask db upgrade
```
If the above information didn't solve your problem, reach out to the development team for further assistance.
</details>

<hr>

Didn't find what you were looking for? Check out our <a href="contributing.md">contributor-oriented introduction to the project</a>!

<p align="right">(<a href="#development-top">back to top</a>)</p>
