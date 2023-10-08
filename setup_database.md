# Setup Database
This file is intended as guideline to set up the aCe database. The database is the easiest way to store and analyze car
data.

## Create Database

If you already have created the database, you can skip this section.

1. Open the XAMPP Control Panel and start Apache and MySQL.
2. Open the following site in your browser of choice

`http://localhost/phpmyadmin/`

3. In the top menu, navigate to `User accounts`
4. In the middle of the screen, click on `Add user account`
5. In the section `Login Information`, insert the following values:
   5.1. Under `User name`, type `ace_db` into the text field.
   5.2. Choose a password and type it into the text fields for `Password` and `Re-type`.
6. In the section `Database for user account`, check the box `Create database with same name and grant all privileges.`
7. Leave everything else as it is and scroll to the bottom of the page. Click on `Go`


## Setup CAN message API

1. Clone the code for the CAN message API from GitHub: [https://github.com/acentauri-solar-racing/can-msg-api](https://github.com/acentauri-solar-racing/can-msg-api)
2. In the root folder of the project, run the script `source_tree.py` (e.g. in the terminal):

```sh
python source_tree.py
```

This script ensures an accurate and up-to-date representation of the CAN message tree in the file tree. This is
necessary that the scripts function as expected.

## Initialize Database

If you already have initialized the database, you can skip this section.

1. In the project you just cloned, navigate to the folder `db`
2. Copy the file `.env.example` and name it `.env`
3. In the file `.env`, insert `ace_db` as username and the password you chose earlier. the database name is the same as
   the username. It should look something like this:

```
DB_USER=ace_db
DB_PASSWORD=your_password.
DB_HOST=localhost
DB_NAME=ace_db
```

4. open the commandline in the top folder of the cloned project and run the following command:

```sh
python db_utils.py -r
```

This deletes all data from the database (if any existed) and creates all tables (if they didn't already exist)