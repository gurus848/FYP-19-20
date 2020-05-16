# SYQ1 FYP 
2019-20
By: SENTHIL, Guru Sarjith and VALLAPURAM, Anish Krishna
Supervised By: Professor Yangqiu Song
Worked in collaboration with Professor Franziska Keller of the HKUST Division of Social Sciences 

## Setup
Please use a Python 3.6.5 virtual environment for reproducibility. Please leave the project structure as is as it is assumed that all of the individual parts of the code are in correct relative locations due to the use of relative paths.

### Environment
Clone this repository and install the required Python dependencies as follows:
```
    pip install -r merged_requirements.txt
```

Before you install the Python dependencies, you need to install graphviz on your computer. Follow the instructions at https://www.graphviz.org/download/ to do so. 

### Coreference Resolution model
The pretrained checkpoint for the coreference resolution ML model must be downloaded. Please run the following commands in a shell:
```
    cd models/coref/
    export data_dir=../
    ./setup_all.sh
    ./download_pretrained.sh <model_name>
```
where model name can be one of: "bert_base", "bert_large" _(recommended)_, "spanbert_base", "spanbert_large". For more details, check `models/coref/README.md`

### BERT_PAIR FewRel model
If not already there, the 2 BERT-PAIR FewRel trained models must be manually downloaded and placed in the `FewRel/checkpoint` directory.

Model which can predict NA/NOTA - https://drive.google.com/open?id=1EtW5DC9HVb00VDQJWKAuZO4zW1U2ouNu
Model which cannot predict NA/NOTA - https://drive.google.com/open?id=1-1xAi-ZDlIZuHeAPpyo6aO5DnFGiLsnn

For more details, check `FewRel/README.md`

To retrain the BERT-PAIR FewRel model, please run
```
    cd FewRel/
    python train_demo.py     --trainN 5 --N 5 --K 3 --Q 1     --model pair --encoder bert --pair --hidden_size 768 --val_step 300 --val_iter 100    --batch_size 4  --train combined_train --val test_wiki --test test_wiki
```

### Web Application
The first time the web application is run, it may take longer than usual as it will automatically download some machine learning model files. 

To run the web application, run the following:
```
    cd FYP_Web_App/
    ./run_server
```

This will start the server at the port 3389. The server can be accessed by going to a web browser and inputting 'http://server_address:3389' (ex. if the sever can be accessed at 'fyp_server' then the address would be 'http://fyp_server:3389').
You may have to configure your server computer's firewall to allow incoming requests on port 3389.

## Other Notes

* If the dependency library `flair` from `merged_requirements.txt` fails to download, try:
```
    pip install --upgrade git+https://github.com/flairNLP/flair.git
```

* The first time you run the project (web server) you will need to download the nltk 'punkt' dataset. In the console/shell the instructions for how to do so will be printed.

* Testing was done with e2e-coref, but the model files themselves were not included in the project as it was not ultimately used. To run the testing code in the e2e-coref/ folder, you can download the code at https://github.com/kentonl/e2e-coref.

* Testing the various models and methods is shown in several Jupyter notebooks. A jupyter server can be started by running `jupyter lab` or `jupyter notebook` in the project top-level directory.  
