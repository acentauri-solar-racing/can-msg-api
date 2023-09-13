# Decode Logfiles

This file is intended as a guideline to decode log files from the car and insert the decoded data into the main sql
database.

## Structure of logfiles 

The logfiles are named after the timestamp they are created, e.g. `09031656` corresponds to September 3, at 16.56.
The content  of the files looks something like this:

```
(1693760165.223) vcan0 505#C80000000000 R
(1693760165.247) vcan0 100#000000000000 R
(1693760165.266) vcan0 6F7#0000000000000000 R
...
````


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


## Clone can-msg-api

if you already cloned the project, you can skip this section.

Clone the code for the CAN message API from GitHub: [https://github.com/acentauri-solar-racing/can-msg-api](https://github.com/acentauri-solar-racing/can-msg-api)


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


## Decode the data

0. optionally, you can delete all data that has been previously been in the database by running the following command.
Attention! This will erase all data from the database!

```sh
python db_utils.py -r
```

### Via GUI
1. Type the following command into the command line:

```sh
python log_decoder.py
```

2. A file explorer should pop up. Chose all the logfiles you wish to decode. The files will be parsed and added to the
database.

### Via Command Line
1. Alternatively, you can directly specify the path to the logfile by using the -f option:

```sh
python log_decoder.py -f <path_to_logfile>
```