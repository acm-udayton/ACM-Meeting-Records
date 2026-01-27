<a id="contributing-top"></a>
<!-- PROJECT HEADER -->
<br />
<div align="center">
<h3 align="center">Contributing - ACM Meeting Records</h3>
  <p align="center">
    An developer's guide to contributing to the project.
    <br />
  </p>
</div>

<!-- GETTING STARTED -->
## Prerequisites

This project is developed and maintained solely by the members of the ACM student chapter at the University of Dayton. If you are interested in this project but are not a member of our student chapter, we welcome you to create a fork of the project and contribute there. We are not currently accepting issues or pull requests from outside of our student chapter. 

### Developer Tooling

As you begin contributing to the ACM Meeting Records project, we recommend the following tools. Other tools may be used, but these are the project standards and we cannot guarantee that we will provide support for developers using other non-recommended developer tools.
1. [Docker Desktop](https://www.docker.com/products/docker-desktop/). Please note, technically you only need to ensure that Docker is installed on your system and the ```docker compose``` command is available, but for maximum debugging ease Docker desktop is the only recommended developer tooling in this category.
2. [Visual Studio Code](https://code.visualstudio.com/)
3. [DBeaver](https://dbeaver.io/)

<hr>

### Branching Practices

We have a standardized procedure for adding features and making bugfixes in iterative versions. Along with this comes a standardized branching procedure. 
For every new major version, here is the process.

1. Create a new branch with the format ```vX.Y``` where X and Y are the major and minor version numbers. Use the ```main``` branch as the base branch.
2. Create a new branch (```feature/...```, ```docs/...```, ```bugfix/...```, ```task/...```, etc.) based on the new ```vX.Y``` branch.
3. Contribute your feature, documentation, bugfix, or task in the branch created in **2**.
4. Once you are done contributing, open a PR into the version branch created in **1** and request review.
5. When the version is finished (usually multiple iterations of **2** through **4**), open a PR into ```dev```.
6. After testing is completed in ```dev```, you open a PR into ```main``` and request review.
7. After that PR is merged into ```main```, create a new [GitHub release](https://github.com/acm-udayton/ACM-Meeting-Records/releases). A newly-built docker image will be pushed to Docker Hub automatically by one of our GitHub actions.

<hr>

### Code Standards

To ensure maintainability and uniformity of style in our codebase, we follow a few formats for commenting within code. When no further information is provided, default to [PEP 8](https://peps.python.org/pep-0008/).
1. All python files should begin with a block comment that follows this format, which should be updated whenever applicable:
```
#!/usr/bin/env python
# path/to/file.py

"""
Project Name: ACM-Meeting-Records
Project Author(s): First Last (github.com/username), ...
Last Modified: DD/MM/YYYY

File Purpose: One sentence to describe the overarching function of the file.
"""
```
2. Functions, classes, and routes should begin with a docstring explaining their function or purpose.
3. Database models (see ```app/models.py```) should always have a ```default``` and ```server_default``` value if ```nullable = false``` is specified.

#### Linting

To enforce code quality we have a GitHub actions runner that automatically kicks of a pylint instance on every push and pull request. For code quality levels of less than 9.5, the GitHub action will fail and any PRs with a failing pylint status will not be approved for merge. To be proactive about pylint, it is recommended that you install the official Pylint extension (by Microsoft) for Visual Studio Code, which will show all linting problems in the open files under a "Problems" tab in the bottom panel.

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

<p align="right">(<a href="#contributing-top">back to top</a>)</p>
