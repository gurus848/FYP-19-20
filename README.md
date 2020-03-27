# SYQ1 FYP 19-20

## Links
Date and Tasks Google Docs - https://docs.google.com/document/d/1_hZRVgCpLIr4eRkcN_XUIH37kvFyd-zENGd4lcbqAQQ/edit

Research Notes and Links Google Docs - https://docs.google.com/document/d/1820clrvOzJhBsEIrg_ElYxn46ze_h2oHYOViLXi8RxU/edit


## Other Notes

Please use a Python 3.6+ virtual environment for reproducibility. Install packages based on the requirements.txt, though not all of them may install using 'pip -r requirements.txt'. You may have to remove some of the lines manually. 

Please add stuff to .gitignore as necessary.

For neuralcoref package, might need to install it using 'pip3 uninstall neuralcoref; pip3 install neuralcoref --no-binary neuralcoref'. It can also likely only be run on Linux.

If using jupyter lab/notebook, make sure that you configure it correctly so that it uses the virtual environment's python interpreter rather than the systemwide on.

The requirements_old.txt in the main project folder is old, use FewRel/requirements.txt instead. Need to install graphviz manually using your OS's package manager, may need to compile it from source. You can only install pygraphviz (a part of the python requirements) once you've installed graphviz.

To use `models/OpenNRE`, set the `PYTHONPATH` variable to `/path-to/FYP-19-20/models/OpenNRE` in .bashrc. 

If the dependency library `flair` from `requirements.txt` fails to download, try:
```
    pip install --upgrade git+https://github.com/flairNLP/flair.git
```

The requirements_old.txt in the main project folder is old, use FewRel/requirements.txt instead. Need to install graphviz manually, may need to compile it from source.

In order to download the pretrained models for the `coref` model, run the following:
```
    cd models/coref/ | export data_dir=../ | ./download_pretrained.sh <model_name>
```
where model name can be one of: "bert_large", "spanbert_large", etc. For more, check `models/coref/README.md`

The first time you run the project you will need to download the nltk 'punkt' dataset.
