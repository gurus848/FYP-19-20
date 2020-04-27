# SYQ1 FYP 19-20

## Links
Date and Tasks Google Docs - https://docs.google.com/document/d/1_hZRVgCpLIr4eRkcN_XUIH37kvFyd-zENGd4lcbqAQQ/edit

Research Notes and Links Google Docs - https://docs.google.com/document/d/1820clrvOzJhBsEIrg_ElYxn46ze_h2oHYOViLXi8RxU/edit

## Setup
Please use a Python 3.6+ virtual environment for reproducibility. 

### Environment
clone this repository and install the required dependencies as follows:
```
    pip install -r FewRel/requirements.txt
```

### Coreference Resolution model
The pretrained model for the coreference model must be installed. Please run the following:
```
    cd models/coref/
    export data_dir=../
    ./download_pretrained.sh <model_name>
```
where model name can be one of: "bert_large", "spanbert_large", etc. "bert_large" is recommended. 
For more details, check `models/coref/README.md`

### FewRel model
Please run the following to download the pretrained FewRel model for our task:
```
    cd FewRel/ 
    ....
```
For more details, check `FewRel/README.md`

### Web Application
To run the web application, run the following:
```
    cd FYP_Web_App/
    python manage.py runserver 8008
    ....
```

## Other Notes

* Please add stuff to .gitignore as necessary.

* If using jupyter lab/notebook, make sure that you configure it correctly so that it uses the virtual environment's python interpreter rather than the systemwide on.

* The requirements_old.txt in the main project folder is old, use FewRel/requirements.txt instead. Need to install graphviz manually using your OS's package manager, may need to compile it from source. You can only install pygraphviz (a part of the python requirements) once you've installed graphviz.

* If the dependency library `flair` from `FewRel/requirements.txt` fails to download, try:
```
    pip install --upgrade git+https://github.com/flairNLP/flair.git
```

* The first time you run the project you will need to download the nltk 'punkt' dataset.
