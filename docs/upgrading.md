<a id="readme-top"></a>
<!-- PROJECT HEADER -->
<br />
<div align="center">
<h3 align="center">Quick Start - ACM Meeting Records</h3>
  <p align="center">
    An administrator's guide to the web app system for recording attendance and notes for ACM meetings.
    <br />
  </p>
</div>

<!-- GETTING STARTED -->
## Getting Started

If it is your first time installing the ACM-Meeting-Records project, view <a href="quickstart.md">quickstart.md</a> instead. This document is only for version upgrades.

### Versions

**Note: ** Prior to version 1.5, there was no simplified upgrading procedure. The common update procedure for versions after v1.4 will not work if you try to upgrade to a version released pre-1.5, and a more manual approach similar to the initial setup in <a href="quickstart.md">quickstart.md</a> may be required. 

#### v1.4 -> v1.5
1. Add the new fields found in the ```.env.example``` file and populate them with your own reCAPTCHA details.
2. Stop your old instance via this command:
```sh docker compose stop```
2. Pull changes of the newest version of the project (v1.5).
3. Apply database schema updates and restart the web app with the new version's changes via this command:
```sh docker compose up -d --build```

<p align="right">(<a href="#readme-top">back to top</a>)</p>
