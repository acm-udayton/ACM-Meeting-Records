<a id="contributing-top"></a>
<!-- PROJECT HEADER -->
<br />
<div align="center">
<h3 align="center">Contributing - ACM Meeting Records</h3>
  <p align="center">
    A developer's guide to the project standards and workflows.
    <br />
  </p>
</div>

<!-- GETTING STARTED -->
## Joining the Development Team

### Want to contribute?
If you are a member of the UD ACM chapter and want to get involved:
1. **Join the Discord:** Head to the official UD ACM Discord server.
2. **Request Access:** Message **@Joseph Lefkovitz** in the `#general` channel.
3. **Get Onboarded:** Once verified, you will be added to the:
   - Restricted `meeting-records-dev` role.
   - Private `#meeting-records` channel.
   - Project Jira Board (where you can pick up tickets and track progress).
   - GitHub Organization as a contributor.

*If you are not a University of Dayton student, we welcome you to fork the repository and explore the code independently!*
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

Didn't find what you were looking for? Check out our <a href="/docs/DEVELOPMENT.md">contributor-oriented technical documentation</a>!

<p align="right">(<a href="#contributing-top">back to top</a>)</p>
