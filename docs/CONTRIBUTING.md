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
7. After that PR is merged into ```main```, create a new [GitHub release](https://github.com/acm-udayton/ACM-Meeting-Records/releases).

<hr>

<p align="right">(<a href="#contributing-top">back to top</a>)</p>
