* Django FYP Relation Extraction Project
* Use requirements.txt from the FewRel folder
* Using Django, jQuery and Bootstrap
* To run, in this folder run 'python manage.py runserver 8008'
* Forward port 8008 using ssh ex. 'ssh meow@server -L 8008:127.0.0.1:8008'
* Save the BERT-PAIR checkpoint to be used in the checkpoint/ folder in FewRel folder
* also run 'python manage.py makemigrations' and 'python manage.py migrate' to set up the DB correctly for the first time
* Run 'python manage.py createsuperuser' to make the admin user to that you can access the admin panel at /admin.