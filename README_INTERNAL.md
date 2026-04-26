## Instructions for groupmates
### First time stuff
- Make sure Python 3.12+ (I'm on 3.14.0) is installed
- Make a virtual environment using `requirements.txt`. The library versions are the latest as of 24/3/2026. Later versions should work but just in case
- `cd src` to get to the root folder of the code or else all `python manage.py` won't work
- `python manage.py migrate` to create a database on your side. Don't track it with git plz
- `python manage.py createsuperuser` to create a user that can access admin page. The admin page is `http://127.0.0.1:8000/admin`

### Always remember
- Pull from remote before working
- `cd src` before `manage.py` stuff
- Don't push venv, cache, IDE settings file onto git repo e.g.  `.venv` `.idea` `.vscode/`. The `.gitignore` should take care of this tho
- Don't update stuff without testing that they work
- Don't commit everything at once. If you made very different changes on two files, commit twice with proper message
- Make sure to commit the migration files after modifying the models and making migrations
- Don't forget to actually push your changes
- Feel free to ask if you are not unsure about something. Explaining is faster than debugging :D

### Useful commands
- `python manage.py runserver` to run the server
- `python manage.py makemigrations` after modifying the models to generate the changelist for migration 
- `python manage.py migrate` to actually write the changes to the database
- `python manage.py test` to test everything
- `coverage run --source="." manage.py test` to test with coverage check
- `coverage html -d "..\html_coverage"` to see html report of the coverage
