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

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#developer-setup">Developer Setup</a>
      <ul>
        <li><a href="#tooling">Tooling</a></li>
        <li><a href="#database-access">Database Access</a></li>
      </ul>
    </li>
    <li>
      <a href="#project-structure">Project Structure</a>
      <ul>
        <li><a href="#directory-map">Directory Map</a></li>
      </ul>
    </li>
    <li>
      <a href="#design-patterns">Design Patterns</a>
      <ul>
        <li><a href="#flask-application-factory">Flask Application Factory</a></li>
      </ul>
    </li>
    <li>
      <a href="#flask-extensions">Flask Extensions</a>
      <ul>
        <li><a href="#flask-login">Flask-Login</a></li>
        <li><a href="#flask-migrate">Flask-Migrate</a></li>
        <li><a href="#flask-sqlalchemy">Flask-SQLAlchemy</a></li>
        <li><a href="#flask-wtf">Flask-WTF</a></li>
      </ul>
    </li>
    <li>
      <a href="#jinja-templating">Jinja Templating</a>
      <ul>
        <li><a href="#template-route-map">Template-Route Map</a></li>
        <li><a href="#extension--inclusion-summary">Extension & Inheritance Summary</a></li>
      </ul>
    </li>
    <li>
      <a href="#cicd-workflows">CI/CD Workflows</a>
    </li>
    <li><a href="#faq--troubleshooting">FAQ & Troubleshooting</a></li>
  </ol>
</details>
<hr>


<!-- Developer Setup -->
## Developer Setup

### Tooling
As you begin contributing to the ACM Meeting Records project, we recommend the following tools. Other tools may be used, but these are the project standards and we cannot guarantee that we will provide support for developers using other non-recommended developer tools.
1. [Docker Desktop](https://www.docker.com/products/docker-desktop/). Please note, technically you only need to ensure that Docker is installed on your system and the ```docker compose``` command is available, but for maximum debugging ease Docker desktop is the only recommended developer tooling in this category.
2. [Visual Studio Code](https://code.visualstudio.com/)
3. [DBeaver](https://dbeaver.io/)

### Database Access
Follow the standard installation procedure outlined in <a href="quickstart.md">quickstart.md</a> to begin the setup process. 

Next, you will need to add your DBeaver database connection. Be sure to select postgresql as your database, and fill out the details with the username, password, and port specified in the docker-compose.yml file, with localhost as the host. You can then find the database tables at ```Databases -> acm-meetings-db -> Schemas -> public -> Tables``` within DBeaver's Database Navigator pane.
<hr>


<!-- Project Structure -->
## Project Structure

### Directory Map
<pre>
ACM-Meeting-Records
├── <a href="#cicd-workflows">.github/workflows</a>
│   ├── .pylintrc
│   ├── <a href="#docker-image-ci">docker-image.yml</a>
│   └── <a href="#pylint-ci">pylint.yml</a>
├── /app
│   ├── <a href="#route-map">/blueprints</a>
│   │   ├── <a href="#routes-admin">admin.py</a>
│   │   ├── <a href="#routes-api">api.py</a>
│   │   ├── <a href="#routes-auth">auth.py</a>
│   │   ├── <a href="#routes-main">main.py</a>
│   │   ├── <a href="#routes-mfa">mfa.py</a>
│   │   └── <a href="#routes-polls">polls.py</a>
│   ├── /static
│   ├── <a href="#route-map">/templates</a>
│   ├── /uploads
│   ├── /utilities
│   ├── <a href="#flask-application-factory">__init__.py</a>
│   ├── .env
│   ├── .env.example
│   ├── <a href="#flask-extensions">extensions.py</a>
│   ├── <a href="#flask-wtf">forms.py</a>
│   ├── <a href="#flask-sqlalchemy">models.py</a>
│   └── utils.py
├── /docs
│   ├── application-demo.png
│   ├── <a href="/docs/CONTRIBUTING.md">CONTRIBUTING.md</a>
│   ├── DEVELOPMENT.md
│   ├── <a href="/docs/quickstart.md">quickstart.md</a>
│   └── <a href="/docs/upgrading.md">upgrading.md</a>
├── <a href="#flask-migrate">/migrations</a>
├── .dockerignore
├── .gitignore
├── Dockerfile
├── LICENSE
├── README.md
├── docker-compose.yml
└── requirements.txt
</pre>
<hr>


<!-- Design Patterns -->
## Design Patterns
Comments and specifications relating to the design patterns and ideologies used in the project's architecture.

### Flask Application factory
The application factory is a design pattern for building scalable codebases for flask backends. We rely on the application factory to build one complete app from a variety of files.

Strictly speaking, the application factory itself can be found in `app/__init__.py`. The contents of this file compiles the logic, extensions, and utilities that are specified in the rest of the python files in the codebase.

The application factory within the `create_app` function in `app/__init__.py` is responsible for the following:
1. Loading environment variables from the ```app/.env``` file.
2. Configuring the logger.
3. Initializing the Flask app.
4. Adding configuration settings to the Flask app.
5. Initializing <a href="#flask-extensions">Flask extensions</a> with the app.
6. Specifying the user loader for <a href="#flask-login">Flask-Login</a>.
7. Setting the app variables such as ```.context```, ```.logs```, ```.base_url```, and ```.storage```.
8. Defining the app's context processor for variables passed to all templates.
9. Adding custom Jinja filters to the app.
10. Registering the app's error handlers for HTTP status code exceptions.
11. Registering all <a href="#route-map">app blueprints</a>.

The application factory is launched by Docker within the web container. This results in a clean build of the flask app, combining the entire codebase and all of its extensions into one app that can be run and debugged within the web container. This also allows us to avoid many issues that arise with monolithic flask apps, such as circular imports and messy code structure. By following the application factory design pattern, we also ensure that our codebase is modular, scalable, and maintainable as we continue to build out the project.
<hr>


<!-- Flask Extensions -->
## Flask Extensions

<details>
<summary id="flask-login"><strong>Flask-Login</strong></summary>
<br>
Flask-Login is a Flask extension that provides user session management for Flask applications. It handles the common tasks of logging in, logging out, and remembering users' sessions across requests. With Flask-Login, you can easily manage user authentication and access control in your Flask app. It provides a simple API for defining user models, handling login and logout functionality, and protecting routes that require authentication. Flask-Login also integrates well with other Flask extensions, such as <a href="#flask-sqlalchemy">Flask-SQLAlchemy</a> for database management and <a href="#flask-wtf">Flask-WTF</a> for form handling, making it a powerful tool for building secure and user-friendly web applications.
<br><br>

In our project, Flask-Login is used to manage user authentication and session management. It allows us to restrict access to certain routes and functionalities based on whether a user is logged in or not. For example, routes related to account management and poll submission are protected with Flask-Login's `@login_required` decorator, ensuring that only authenticated users can access those features. Flask-Login also provides the functionality to remember users' sessions, so they don't have to log in every time they visit the site, which enhances the user experience. 

We have also built a custom `@admin-required` decorator on top of Flask-Login's `@login_required` to restrict access to admin-only routes, ensuring that only users with admin privileges can access certain parts of the application, such as the admin dashboard for managing polls.

For more information on how to use Flask-Login, please refer to the official documentation: https://flask-login.readthedocs.io/en/latest/
</details>

<details>
<summary id="flask-migrate"><strong>Flask-Migrate</strong></summary>
<br>
Flask-Migrate is a Flask extension that handles SQLAlchemy database migrations for Flask applications using Alembic. It provides a set of command-line tools to manage database schema changes, allowing us to easily create, apply, and track database migrations as the application evolves. With Flask-Migrate, you can generate migration scripts based on changes to your SQLAlchemy models, apply those migrations to the database, and keep track of the migration history. These scripts are shared as part of the codebase, allowing all developers and users to automatically apply your changes without conflict. 

Whenever you make changes to the database models, you should create a new migration script and apply it to the database. This can be done using the following command sequence:
```sh
docker compose stop
docker compose up -d db
docker compose build web
docker compose run --rm web flask db migrate -m "your upgrade message here"
docker compose run --rm web flask db upgrade
```

Be sure to replace the "your upgrade message here" message with a string that provides a clearer description of what the database model changes are. This will help other developers understand the purpose of the migration when they see it in the codebase. Whenever possible, only generate one migration per pull request by including all model changes in one migration script. This will help keep the migration history clean and organized. If you need to make additional model changes after generating a migration, you can either modify the existing migration script (if it hasn't been applied yet) or create a new migration script for the additional changes. For any questions on the migration script recreation process, please reach out to the development team lead for assistance.

For more information on how to use Flask-Migrate, please refer to the official documentation: https://flask-migrate.readthedocs.io/en/latest/
</details>

<details>
<summary id="flask-sqlalchemy"><strong>Flask-SQLAlchemy</strong></summary>
<br>
Flask-SQLAlchemy is a Flask extension that provides integration with SQLAlchemy, a powerful Object-Relational Mapping (ORM) library for Python. It simplifies the process of working with databases in Flask applications by providing a high-level API for defining database models, querying the database, and managing database connections. With Flask-SQLAlchemy, you can define your database models for the project as Python classes in `app/models.py`, and it will handle the underlying SQL queries and database interactions for you. This allows you to work with your database using Python objects and methods, rather than writing raw SQL queries. Flask-SQLAlchemy also provides support for <a href="#flask-migrate">database migrations when used in conjunction with Flask-Migrate</a>, allowing you to easily manage changes to your database schema as your application evolves.
<br><br>

Each time you make changes to your database models, be sure to create a new migration script using Flask-Migrate and apply it to your database to keep your schema up to date. When possible, keep the number of migration scripts to a minimum by including all model changes in one migration script per pull request. This will help maintain a clean and organized migration history. If you need to make additional model changes after generating a migration, you can either modify the existing migration script (if it hasn't been applied yet) or create a new migration script for the additional changes. For any questions on the migration script recreation process, please reach out to the development team lead for assistance.


For more information on how to use Flask-SQLAlchemy, please refer to the official documentation: https://flask-sqlalchemy.palletsprojects.com/en/2.x/
</details>

<details>
<summary id="flask-wtf"><strong>Flask-WTF</strong></summary>
<br>
Flask-WTF is a Flask extension that integrates the WTForms library with Flask applications. It provides a simple and flexible way to create and handle web forms in Flask. With Flask-WTF, you can define your forms as Python classes in `app/forms.py`, and it will handle form rendering, validation, and CSRF protection for you. Flask-WTF also provides support for file uploads and custom validators, making it a powerful tool for building complex forms in your Flask application. By using Flask-WTF, you can easily manage user input and ensure that your forms are secure and user-friendly.
<br><br>

In our project, all Flask-WTF forms are defined in the `app/forms.py` file. Each form is represented as a Python class that inherits from `FlaskForm`, and the form fields are defined as class attributes. For example, we have forms for user login, registration, account updates, poll creation, and MFA verification. These forms are then imported and used in the appropriate routes to handle form rendering and processing. When a form is submitted, Flask-WTF will automatically validate the input based on the field definitions and any custom validators we have specified. If the form data is valid, we can then process it in our route functions to perform actions such as creating a new user account, updating user information, or creating a new poll.

For more information on how to use Flask-WTF, please refer to the official documentation: https://flask-wtf.readthedocs.io/en/1.2.x/
</details>

<hr>


<!-- Templating -->
## Jinja Templating
Documentation about to Jinja, render_template calls, and other related topics.

## Route Map
Document each endpoint. Include the route, overarching function, and return. If the return is a redirect, link to that sub-item. For all of the endpoint templates, list the routes that point to them, what Jinja2 parameters are passed to them (and data format if needed), or mark as a template for a page component (not a complete or served page). 

For POST requests, specify the type of data that should be expected, if any. This is usually specified by the Flask-WTF form used on the page. Also make note of what templates send data to the endpoint.

<details>
<summary id="routes-admin"><strong>Admin Routes</strong></summary>
<br>
<p>The following routes handle meeting operations, attendee tracking, and user management for administrators. These routes are contained within the admin blueprint (<code>/admin/...</code>) and are strictly protected by the <code>@login_required</code> and <code>@admin_required</code> decorators to prevent unauthorized access.</p>
    <ul>
      <li id="route-admin-dashboard">
        <strong>/admin/dashboard/&lt;int:meeting_id&gt;/ (GET)</strong>
        <br>
        <i>admin_dashboard</i>
        <p>
          Show the administrator dashboard page for a single meeting. This endpoint queries and displays the selected meeting, its attendees, associated meeting minutes, and any uploaded attachments.
        </p>
        <h4>Template file: admin/dashboard.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>String - formatted as "Meeting - {meeting.title}"</td></tr>
          <tr><td>meeting</td><td>Meetings object</td></tr>
          <tr><td>attendees</td><td>List of Attendees objects</td></tr>
          <tr><td>minutes</td><td>List of Minutes objects</td></tr>
          <tr><td>attachments</td><td>List of Attachments objects</td></tr>
          <tr><td>add_attendee_form</td><td>Flask-WTF form object - AdminAttendeeAddForm</td></tr>
        </table>
      </li>
      <li id="route-admin-create">
        <strong>/admin/create/ (POST)</strong>
        <br>
        <i>event_create</i>
        <p>
          Create a new meeting based on form inputs (title, description, and admin_only status). Uses the <code>CreateMeetingForm</code>. On success, the admin is redirected to the <a href="#route-admin-dashboard">admin.admin_dashboard</a>. On failure, they are redirected to the main events list.
        </p>
      </li>
      <li id="route-admin-start">
        <strong>/admin/start/&lt;int:meeting_id&gt;/ (POST)</strong>
        <br>
        <i>event_start</i>
        <p>
          Start a single meeting from the administrator dashboard. This generates a meeting code, updates the meeting state to "active", records the start time, and adds the starting officer as an attendee. Returns a JSON payload indicating success, along with the meeting code. If the meeting under the given meeting id is already in an active state, then a JSON payload is returned indicating failure.
        </p>
      </li>
      <li id="route-admin-reset-code">
        <strong>/admin/reset-code/&lt;int:meeting_id&gt;/ (GET)</strong>
        <br>
        <i>reset_code</i>
        <p>
          Reset the meeting join code for a currently active meeting. Generates a new code and redirects to <a href="#route-admin-show-code">/admin/show-code/</a>. If the meeting is not active, it renders an error page.
        </p>
      </li>
      <li id="route-admin-show-code">
        <strong>/admin/show-code/ (GET)</strong>
        <br>
        <i>show_code</i>
        <p>
          Show the meeting join code for a single meeting based on the URL argument.
        </p>
        <h4>Template file: code.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>String - "Meeting Code"</td></tr>
          <tr><td>code</td><td>String - the active meeting code</td></tr>
        </table>
      </li>
      <li id="route-admin-end">
        <strong>/admin/end/&lt;int:meeting_id&gt;/ (POST)</strong>
        <br>
        <i>event_end</i>
        <p>
          End an active meeting from the administrator dashboard. Updates the state to "ended" and logs the end time. Returns a JSON response. If meeting state cannot be updated, returns an error message with the current state.
        </p>
      </li>
      <li id="route-admin-attendees">
        <strong>/admin/attendees/&lt;int:meeting_id&gt;/ (POST)</strong>
        <br>
        <i>event_attendees</i>
        <p>
          Manually add an attendee to a single meeting. Expects data from the <code>AdminAttendeeAddForm</code>. Returns a JSON payload indicating success or failure (e.g., if the user does not exist or is already checked in).
        </p>
      </li>
      <li id="route-admin-remove-attendee">
        <strong>/admin/remove-attendee/&lt;int:meeting_id&gt;/&lt;int:attendee_id&gt;/ (POST)</strong>
        <br>
        <i>event_remove_attendee</i>
        <p>
          Remove an attendee from a meeting based on their attendee ID. Returns a JSON payload.
        </p>
      </li>
      <li id="route-admin-minutes">
        <strong>/admin/minutes/&lt;int:meeting_id&gt;/ [and] /admin/minutes/&lt;int:meeting_id&gt;/&lt;int:minutes_id&gt;/ (POST)</strong>
        <br>
        <i>event_minutes</i>
        <p>
          Add or update minutes for a single meeting. Expects form data containing <code>meeting_minutes</code>. If a <code>minutes_id</code> is provided, it updates the existing entry; otherwise, it creates a new one. Returns a JSON response.
        </p>
      </li>
      <li id="route-admin-add-attachment">
        <strong>/admin/add-attachment/&lt;int:meeting_id&gt;/ (POST)</strong>
        <br>
        <i>event_add_attachment</i>
        <p>
          Upload a file attachment to a single meeting. Expects a file in the request payload and validates against allowed extensions (pptx, pdf, docx, txt, png, jpg, jpeg, gif). Returns a JSON response.
        </p>
      </li>
      <li id="route-admin-remove-attachment">
        <strong>/admin/remove-attachment/&lt;int:meeting_id&gt;/&lt;int:attachment_id&gt;/ (POST)</strong>
        <br>
        <i>event_remove_attachment</i>
        <p>
          Remove an attachment from a meeting. Deletes the physical file from the Docker volume directory and removes the database record. Returns a JSON response.
        </p>
      </li>
      <li id="route-admin-delete">
        <strong>/admin/delete/&lt;int:meeting_id&gt;/ (POST)</strong>
        <br>
        <i>event_delete</i>
        <p>
          Delete a meeting along with all of its cascaded data, including attendees, minutes, and attachments. Redirects to the main events list upon completion.
        </p>
      </li>
      <li id="route-admin-users">
        <strong>/admin/users/ (GET)</strong>
        <br>
        <i>users_list</i>
        <p>
          Show the user management index page. Aggregates each user's total meetings attended and their most recent check-in date.
        </p>
        <h4>Template file: admin/users.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>String - "Users"</td></tr>
          <tr><td>users</td><td>List of Users objects, augmented with meeting counts and recent dates</td></tr>
        </table>
      </li>
      <li id="route-admin-user-actions">
        <strong>User Action Routes (POST)</strong>
        <br>
        <p>The following routes accept POST requests from the user management dashboard to perform administrative actions on specific accounts. After execution, they all flash a status message and redirect back to <a href="#route-admin-users">/admin/users/</a>.</p>
        <ul>
            <li><strong>/admin/users/reset-password/&lt;int:user_id&gt;/</strong> - <i>reset_user_password:</i> Overwrites a user's password with the value provided in <code>new_password</code>.</li>
            <li><strong>/admin/users/promote/&lt;int:user_id&gt;/</strong> - <i>promote_user:</i> Grants admin privileges to a standard user.</li>
            <li><strong>/admin/users/demote/&lt;int:user_id&gt;/</strong> - <i>demote_user:</i> Revokes admin privileges from a user. Cannot be used on the currently authenticated admin.</li>
            <li><strong>/admin/users/disable-mfa/&lt;int:user_id&gt;/</strong> - <i>disable_user_mfa:</i> Forces disabling of TOTP and general MFA requirements for a specified user.</li>
            <li><strong>/admin/users/disable-account/&lt;int:user_id&gt;/</strong> - <i>disable_user_account:</i> Deactivates an active user account.</li>
            <li><strong>/admin/users/enable-account/&lt;int:user_id&gt;/</strong> - <i>enable_user_account:</i> Reactivates a disabled user account.</li>
        </ul>
      </li>
    </ul>
</details>

<details>
  <summary id="routes-api"><strong>API Routes</strong></summary>
  <br>
  <p>
    Gets and returns various app data. 
  </p>

  <!-- API Routes List-->
  <ul>
  <li id="route-api-event-attendees">
    <strong>/event/attendees/&lt;int:meeting_id&gt;/ (GET)</strong>
    <br>
    <i>"api_event_attendees"</i>
    <p>
      Get attendee list for a single meeting and returns in a json object. 
    </p>
    <h4>Parameters</h4>
    <table>
      <tr><th>Parameters</th><th>Type</th></tr>
      <tr><td>meeting_id</td><td>Integer</td></tr>
    </table>
  </li>

  <li id="route-api-event-notes">
    <strong>/event/notes/&lt;int:meeting_id&gt;/ (GET)</strong>
    <br>
    <i>api_event_minutes</i>
    <p>
      Get the meting notes for a specified meeting and returns in a json object. 
    </p>
    <h4>Parameters</h4>
    <table>
      <tr><th>Parameters</th><th>Type</th></tr>
      <tr><td>meeting_id</td><td>Integer</td></tr>
    </table>
  </li>

  <li id="route-api-event-state">
    <strong>/event/state/&lt;int:meeting_id&gt;/ (GET)</strong>
    <br>
    <i>api_event_state</i>
    <p>
      Get the state for a specified meeting and returns in a json object. If the meeting isn't fount it will return 404.
    </p>
    <h4>Parameters</h4>
    <table>
      <tr><th>Parameters</th><th>Type</th></tr>
      <tr><td>meeting_id</td><td>Integer</td></tr>
    </table>
  </li>

  <li id="route-api-event-attachments">
    <strong>/event/attachments/&lt;int:meeting_id&gt;/ (GET)</strong>
    <br>
    <i>api_event_attachments</i>
    <p>
      Gets the attachments for a specified meeting and returns in a json object. 
    </p>
    <h4>Parameters</h4>
    <table>
      <tr><th>Parameters</th><th>Type</th></tr>
      <tr><td>meeting_id</td><td>Integer</td></tr>
    </table>
  </li>
  
</ul>
</details>

<details>
<summary id="routes-auth"><strong>Authentication Routes</strong></summary>
<br>
<p>The following routes handle user authentication and account management. These routes are contained in the auth blueprint (.../) and account management routes are restricted to logged in users.</p>
  <ul>
      <li id="route-auth-login">
        <strong>/login/ (GET, POST)</strong>
        <br>
        <i>login</i>
        <p>
          Display the login page and process login submissions.
          <br>
          <br>
          If the endpoint is accessed with a GET request, the user is shown the login form. If the endpoint is accessed with a POST request, the given user credentials are validated. This includes verifying that the account exists, the account is activated, and password verification.
          <br>
          <br>
          If Multi-Factor Authentication (MFA) is enabled for the account, the user is redirected to the appropriate MFA verification endpoint (<a href="#route-mfa-verify-totp">/mfa/verify-totp/</a> or <a href="#route-mfa-verify-recovery-code">/mfa/verify-recovery-code/</a>) to complete the authentication process.
          <br>
          <br>
          On a successful login, the user is redirected to <a href="#route-main-home">main.home</a>.
        </p>
        <h4>Template file: login.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>User Log In</td></tr>
          <tr><td>form</td><td>Flask-WTF form object - LoginForm</td></tr>
        </table>
      </li>
      <li id="route-auth-sign-up">
        <strong>/sign-up/ (GET, POST)</strong>
        <br>
        <i>sign_up</i>
        <p>
          Display the registration page and create new accounts.
          <br>
          <br>
          If the endpoint is accessed with a GET request, the user is shown the registration form. If the endpoint is accessed with a POST request, the submitted registration data (email and password) is validated.
          <br>
          <br>
          On successful registration, the user is redirected to <a href="#route-auth-login">/login/</a> to authenticate with their newly created credentials.
        </p>
        <h4>Template file: sign_up.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>Create New Account</td></tr>
          <tr><td>required_domain</td><td>String or None - Email domain that usernames must end with</td></tr>
          <tr><td>form</td><td>Flask-WTF form object - SignUpForm</td></tr>
        </table>
      </li>
      <li id="route-auth-logout">
        <strong>/logout/</strong>
        <br>
        <i>logout</i>
        <p>
          Restricted to logged in users. Log out the currently authenticated user. After logout, the user is redirected to <a href="#route-main-home">main.home</a>.
        </p>
      </li>
      <li id="route-auth-my-account">
        <strong>/my-account/</strong>
        <br>
        <i>my_account</i>
        <p>
          Restricted to logged in users. Shows a user's number of MFA codes, start semester and graduation semester. There is also an update account form shown for the user to update their account.
        </p>
        <h4>Template file: account.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>My Account</td></tr>
          <tr><td>num_codes</td><td>Integer - number of MFA codes</td></tr>
          <tr><td>account_update_form</td><td>Flask-WTF form object - AccountUpdateForm</td></tr>
        </table>
      </li>
      <li id="route-auth-update-account">
        <strong>/update-account/ (POST)</strong>
        <br>
        <i>update_account</i>
        <p>
          When the endpoint is accessed with a POST request, it processes submissions of the account update form (password, start semester, and graduation semester) and updates the data into the database. After processing, the user is redirected back to <a href="#route-auth-my-account">/my-account/</a>.
        </p>
      </li>
    </ul>
</details>

  <!-- Main Routes -->
<details>
<summary id="routes-main"><strong>Main Routes</strong></summary>
<br>
  <!-- Route Discription -->
<p> The following routes handle serving the main app functionality. They send and retrieve data related to meeting minutes and handle checking in as well as voting and downloading files.</p>

  <!-- Route Details List -->
  <ul>
    <li id="route-main-home">
        <strong>/ (GET)</strong>
        <br>
        <i>home</i>
        <p>
          Displays the homepage. Admins can see the admin only meetings. The meeting checking and any polls are also attached here. 
        </p>
        <h4>Template file: index.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>Home</td></tr>
          <tr><td>recent_meetings</td><td> A list of meetings</td></tr>
          <tr><td>featured_meeting</td><td>The first meeting found in recent_meetings or None</td></tr>
          <tr><td>polls</td><td>A list of all polls</td></tr>
          <tr><td>form</td><td>The form for checking into the meeting.</td></tr>
          <tr><td>poll_form</td><td>The form for voting in a poll.</td></tr>
        </table>
      </li>
       <li id="route-main-events-list">
        <strong>/events/ (GET)</strong>
        <br>
        <i>events_list</i>
        <p>
          Displays the event list ordered by id. Checks to ensure admin only meetings can be displayed. A form for creating a new meeting is also attached here. 
        </p>
        <h4>Template file: events.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>Meetings</td></tr>
          <tr><td>meetings</td><td> A list of meetings</td></tr>
          <tr><td>form</td><td> Form for creating meetings</td></tr>
        </table>
      </li>
       <li id="route-main-user-event">
        <strong>/event/&lt;int:meeting_id&gt;/ (Get)</strong>
        <br>
        <i>user_event</i>
        <p>
          Displays details for a selected event, the check-in form, attendees, minutes and attachments. Redirects to 404 if the meeting doesn't exist. 
        </p>
        <h4>Parameters</h4>
        <table>
        <tr><th>Parameters</th><th>Type</th></tr>
        <tr><td>meeting_id</td><td>Integer</td></tr>
        </table>
        <h4>Template file: event.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>Meeting - {meeting title}</td></tr>
          <tr><td>meeting</td><td>Meetings object</td></tr>
          <tr><td>all_minutes</td><td>Meeting minutes</td></tr>
          <tr><td>all_attendees</td><td>List of attendees</td></tr>
          <tr><td>all_attachments</td><td>List of attachments</td></tr>
          <tr><td>form</td><td>A form for checking into the meeting</td></tr>
        </table>
      </li>
      <li id="route-main-event-check-in">
        <strong>/event/check-in/&lt;int:meeting_id&gt;/ (POST)</strong>
        <br>
        <i>event_check_in</i>
        <p>
          Check into a single meeting or displays a <q>check-in failed</q> warning. Checks for the following:
          </p>
           <ul>
            <li>Meeting exists</li>
            <li>Form is valid</li> 
            <li>Meeting code is correct</li> 
            <li>Meeting is active</li> 
            <li>Admin status</li>
            <li>Active user status</li>
            <li>Current attendee is not already checked in.</li> 
           </ul>
        <p>  
          If all checks pass, a <q>check-in succeeded</q> message will be displayed. If the user is not activated they will be redirected <a href="#route-auth-login">auth.login</a> page. If the meeting doesn't exist then 404 will be displayed and the user will be redirectred to <a href="#route-main-home">main.home</a>. All other failed checks will result in a <q>Check-in failed</q> message.  
        </p>
      </li>
       <li id="route-main-download-file">
        <strong>/uploads/&lt;name&gt; (GET)</strong>
        <br>
        <i>download_file</i>
        <p>
          Download the specified file.
        </p>
        <h4>Parameters</h4>
        <table>
          <tr><th>Parameters</th><th>Type</th></tr>
          <tr><td>name</td><td>String</td></tr>
        </table>
      </li>
       <li id="route-main-submit-poll">
        <strong>/submit-poll/&lt;int:poll_id&gt; (POST)</strong>
        <br>
        <i>submit_poll</i>
        <p>
          Handle voting for a poll. The user must be logged in. Handles FRQ, and MCQ poll questions one at a time via helper functions also defined in the blueprint `main.py` file. Adds one vote to the question if user hasn't voted already, otherwise updates the vote for the user. Redirects to <a href="#route-main-show-polls">main.show_polls</a> page after all questions are processed. 
        </p>
        <h4>Parameters</h4>
        <table>
          <tr><th>Parameters</th><th>Type</th></tr>
          <tr><td>poll_id</td><td>Integer</td></tr>
        </table>
      </li>
  </ul>
</details>

<details>
<summary id="routes-mfa"><strong>MFA Routes</strong></summary>
<br>
<p>The following routes handle Multi-Factor Authentication (MFA) functionalities, including TOTP setup and verification, as well as recovery code management. All routes here are contained within the mfa Blueprint (.../mfa/...) and should be restricted to logged-in users. </p>
    <ul>
      <li id="route-mfa-reset-recovery-codes">
        <strong>/reset-recovery-codes/ (GET)</strong>
        <br>
        <i>reset_recovery_codes</i>
        <p>
          Remove all of a user's unused recovery codes and generate 10 new recovery codes. 
        </p>
        <h4>Template file: auth/reset-codes.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>MFA Recovery Codes</td></tr>
          <tr><td>codes</td><td>String with newlines or tab characters separating the ten recovery codes</td></tr>
        </table>
      </li>
      <li id="route-mfa-verify-recovery-code">
        <strong>/verify-recovery-code/ (GET, POST)</strong>
        <br>
        <i>verify_recovery_code</i>
        <p>
          Verify a user's MFA recovery code during the login process. If the endpoint is accessed with a GET request, the user is shown the recovery code verification form. If the endpoint is accessed with a POST request, the submitted recovery code is verified and the user is either logged in or shown an error message. On successful login, the used recovery code is invalidated and the user is redirected to <a href="#route-main-home">main.home</a>.
        </p>
        <h4>Template file: auth/verify-code.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>Verify MFA Recovery Code</td></tr>
          <tr><td>form</td><td>Flask-WTF form object - RecoveryCodeVerifyForm</td></tr>
        </table>
      </li>
      <li id="route-mfa-verify-totp">
        <strong>/verify-totp/ (GET, POST)</strong>
        <br>
        <i>verify_totp</i>
        <p>
          Verify a user's MFA TOTP code during the login process. If the endpoint is accessed with a GET request, the user is shown the TOTP verification form. If the endpoint is accessed with a POST request, the submitted TOTP code is verified and the user is either logged in or shown an error message. On successful login, the user is redirected to <a href="#route-main-home">main.home</a>.
        </p>
        <h4>Template file: auth/verify-totp.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>Verify MFA TOTP Code</td></tr>
          <tr><td>form</td><td>Flask-WTF form object - TotpVerifyForm</td></tr>
        </table>
      </li>
      <li id="route-mfa-setup-totp">
        <strong>/setup-totp/ (GET)</strong>
        <br>
        <i>setup_totp</i>
        <p>
          Setup Multi-Factor Authentication (MFA) for a user account. The user is shown the MFA setup page with a QR code and secret key for TOTP configuration as well as a form to verify the TOTP setup. Upon submission of the form, the form data is sent as a POST request to <a href="#route-mfa-verify-totp-setup">mfa.verify_totp_setup</a>.
        </p>
        <h4>Template file: auth/setup-totp.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>Setup TOTP MFA</td></tr>
          <tr><td>qr_code_data</td><td>Base64-encoded PNG image data for the TOTP QR code</td></tr>
          <tr><td>totp_secret</td><td>String representing the TOTP secret key</td></tr>
          <tr><td>form</td><td>Flask-WTF form object - TotpSetupForm</td></tr>
        </table>
      </li>
      <li id="route-mfa-verify-totp-setup">
        <strong>/verify-totp-setup/ (POST)</strong>
        <br>
        <i>verify_totp_setup</i>
        <p>
          Verify the TOTP setup during MFA configuration. The submitted TOTP code from the setup form is verified using cookie data, and if valid, MFA is enabled for the user account. If the user doesn't yet have recovery codes set up, they are redirected to <a href="#route-mfa-reset-recovery-codes">mfa.reset_recovery_codes</a>. Otherwise, redirect to <a href="#route-auth-my-account">auth.my_account</a>. If the code is invalid, an error message is shown on the setup page.
        </p>
      </li>
      <li id="route-mfa-disable-totp">
        <strong>/disable-totp/ (GET)</strong>
        <br>
        <i>disable_totp</i>
        <p>
          Disable TOTP-based MFA for the user account. Upon successful disabling, the user is redirected to <a href="#route-auth-my-account">auth.my_account</a>.
        </p>
      </li>
      <li id="route-mfa-disable-mfa">
        <strong>/disable-mfa/ (GET)</strong>
        <br>
        <i>disable_mfa</i>
        <p>
          Disable all MFA methods for the user account, including TOTP and recovery codes. Upon successful disabling, the user is redirected to <a href="#route-auth-my-account">auth.my_account</a>.
        </p>
    </ul>
</details>

<details>
<summary id="routes-polls"><strong>Polls Routes</strong></summary>
<br>
<p>The following routes handle the creation, submission, and deletion of polls. These routes are contained in the polls blueprint (.../polls/...). Poll submission is limited to logged in users, while creation and deletion is limited to admin users.</p>
    <ul>
      <li id="route-polls-polls">
        <strong>/polls/ (GET)</strong>
        <br>
        <i>polls_list</i>
        <p>
          Display the admin polls management dashboard showing all existing polls with their questions, options, vote counts, and free response answers. Admins can view poll statistics and access forms to create new polls or delete existing ones.
        </p>
        <h4>Template file: admin/polls.html</h4>
        <table>
          <tr><th>Jinja2 Parameters</th><th>Data Format</th></tr>
          <tr><td>page_title</td><td>Polls</td></tr>
          <tr><td>polls</td><td>List of Poll objects with related questions, options, and responses</td></tr>
          <tr><td>form</td><td>Flask-WTF form object - CreatePollForm</td></tr>
          <tr><td>delete_poll_form</td><td>Flask-WTF form object - DeletePollForm</td></tr>
        </table>
      </li>
      <li id="route-polls-create">
        <strong>/create-poll/ (POST)</strong>
        <br>
        <i>create_poll</i>
        <p>
          Creates a new poll in the admin dashboard. Admins can create a varity of questions including multiple choice, 
          free response, and multiple response. On successful creation or not, the admin is redirected to <a href="#route-polls-list">polls.polls_list</a>. 
        </p>
      </li>
      <li id="route-polls-delete">
        <strong>/delete-poll/&lt;int:poll_id&gt;/ (POST)</strong>
        <br>
        <i>delete_poll</i>
        <p>
          Deletes the selected poll. Exists as a button associated with each existing poll, only accessable to admins. Redirects the admin to <a href="#route-polls-list">polls.polls_list</a> after clicking. 
        </p>
      </li>
    </ul>
</details>

### Extension & Inclusion Summary

In addition to the HTML templates passed to flask's `render_template` function, we have a few HTML files that contain the code for a single component, which are then extended or included in other templates. 
<details>
<summary id="jinja-footer"><strong>footer.html</strong></summary>
<br>
</details>
<details>
<summary id="jinja-header"><strong>header.html</strong></summary>
<br>
</details>
<details>
<summary id="jinja-nav"><strong>navbar.html</strong></summary>
<br>
</details>
<details>
<summary id="jinja-base"><strong>base.html</strong></summary>
<br>
</details>
<hr>


<!-- CI/CD Workflows -->
## CI/CD Workflows
We use a few GitHub Actions runners for our project's CI/CD processes.

<details>
<summary id="pylint-ci"><strong>Pylint CI</strong></summary>
This workflow runs on every push to the repository as well as on every pull request. It automatically runs pylint on the codebase and outputs a report of any linting errors or warnings. This helps us maintain code quality and consistency across the project. The "passing" standard for the workflow is currently set high at 9.5, as specified in the `.github/workflows/.pylintrc` file, but this may be adjusted in the future as the codebase continues to evolve and we determine what an appropriate standard is for our project.
<br><br>

For precise configuration details, please consult the file at ```.github/workflows/pylint.yml```.
</details>

<details>
<summary id="docker-image-ci"><strong>Docker Image CI</strong></summary>
This workflow is only triggered on successful pushes to the repository's main branch. It will automatically use the Dockerfile to build a new image for the web container. It will also use GitHub secrets (must be configured by an ACM officer with Organization manager access on GitHub) to publish this image to DockerHub. This ultimately serves the purpose of ensuring that the public build of the web app is a stable release, never a release candidate or development version.
<br><br>

For precise configuration details, please consult the file at ```.github/workflows/docker-image.yml```.
</details>
<hr>


<!-- FAQ & Troubleshooting -->
## FAQ

Running into a problem or not sure how to proceed? Before reaching out to someone else on the development team, check out these common questions and solutions!

<details>
<summary><strong>Database errors on web container startup - duplicates, invalid entries, etc. </strong></summary>
<br />
The database is likely crashing due to updated web app source code expecting a different schema (or even a new schema) in the database but not finding it. This can manifest in many types of errors output to the web container console, but they are often large and messy. These are especially common when making changes to the models.py or switching between branches.

We use flask-migrate for database management, so if you don't explicitly tell flask-migrate that your database needs updated, you can end up with an outdated or broken schema. First, check your database for an alembic_version table and look at the version_number column entry. Now search that ID in the source code in the project's ```migrations/versions directory```. If you find a file with the following line
```
Revises: your_version_number
```
a newer migration exists already, but hasn't been applied automatically. If however, you don't see any such file, you likely need to create a new migration file. To do this, run the following terminal commands while your db container is running. Be sure to replace the "< your upgrade message here >" message with a string that provides a clearer description of what the database model changes are.
```
docker compose build web
docker compose run --rm web flask db migrate -m "<your upgrade message here>"
docker compose run --rm web flask db upgrade
```
If the above information didn't solve your problem, reach out to the development team for further assistance.
</details>

<details>
<summary><strong>I'm not sure what database schema version I am currently using</strong></summary>
<br />
This issue is particularly prevalent when switching between branches, as different branches may have different migration histories and therefore different database schema versions. To check your current database schema version, you can follow these steps:

1. Ensure that your database container is running. 
2. Connect to your database using DBeaver or any other database client.
3. Look for a table named `alembic_version` in the `public` schema of your database. This table is created and managed by Flask-Migrate to keep track of the current migration version applied to the database.
4. Query the `alembic_version` table to find the current version number. It should be the only entry in the table and it will be an alphanumeric string that corresponds to the latest migration that has been applied to your database.
5. Once you have the version number, you can search for it in the `migrations/versions` directory of the codebase to find out which migration file corresponds to that version. 

This will give you insight into what schema changes have been applied to your database and help you determine if you need to apply any new migrations or if you are on the correct version for the branch you are working on. If you are on the wrong version, you can either apply the necessary migrations to update your database schema or reset your database and apply all migrations from the beginning to ensure you are on the correct version for your branch.
</details>


<hr>

Didn't find what you were looking for? Check out our <a href="/docs/CONTRIBUTING.md">contributor-oriented introduction to the project</a>!

<p align="right">(<a href="#development-top">back to top</a>)</p>
