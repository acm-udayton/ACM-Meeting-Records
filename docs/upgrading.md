<a id="readme-top"></a>
<!-- PROJECT HEADER -->
<br />
<div align="center">
<h3 align="center">Quick Start - ACM Meeting Records</h3>
  <p align="center">
    An administrator's guide to updating the web app system for recording attendance and notes for ACM meetings.
    <br />
  </p>
</div>

<!-- GETTING STARTED -->
## Getting Started

If it is your first time installing the ACM-Meeting-Records project, view <a href="quickstart.md">quickstart.md</a> instead. This document is only for version upgrades.

## Versions
Versions require subsequent upgrade patterns, so please incrementally update your system if you are more than one version behind the current version.

### Version 1.0 through Version 1.4
Prior to version 1.5, there was no simplified upgrading procedure. The common core update procedure for versions after v1.4 will not work if you try to upgrade to a version released pre-1.5, and a more manual approach may be required. 

Feel free to reach out for assistance if needed.

<hr>

### Version 1.4 to v1.5
1. Add the new fields found in the ```.env.example``` file and populate them with your own reCAPTCHA details.
2. Stop your old instance via this command:
```sh
docker compose stop
```
2. Pull changes of the newest version of the project (v1.5).
3. Apply database schema updates and restart the web app with the new version's changes via this command sequence:
```sh 
docker compose up -d --build db
docker compose build web
docker compose run --rm web flask db stamp 3e163497f885
docker compose run --rm web flask db upgrade
docker compose up
```
<hr>

<p align="right">(<a href="#readme-top">back to top</a>)</p>
