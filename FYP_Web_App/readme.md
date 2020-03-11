* Django FYP Relation Extraction Project
* Use requirements.txt from the FewRel folder
* Using Django, jQuery and Bootstrap
* To run, in this folder run 'FEWREL_PATH=/path/to/fewrel python manage.py runserver 8008'
* Forward port 8008 using ssh ex. 'ssh meow@server -L 8008:127.0.0.1:8008'
* Save the BERT-PAIR checkpoint to be used in the checkpoint/ folder in FewRel folder
* also run 'FEWREL_PATH=/path/to/fewrel python manage.py makemigrations' and 'FEWREL_PATH=/path/to/fewrel python manage.py migrate' to set up the DB correctly for the first time