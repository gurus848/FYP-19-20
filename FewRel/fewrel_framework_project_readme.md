# Testing FewRel few-shot relation extraction

* goal is to make it like the demo at http://opennre.thunlp.ai/#/fewshot_re - in the demo it seems to work pretty well
* based on https://github.com/thunlp/FewRel
* use torch 1.3.1
* copy val_wiki.json as test_wiki.json in the data folder to make it work
* python requirements listed in requirements.txt. pytorch normal version will not work on the gpu, to use gpu if you want you have to use the gpu version.
* the checkpoint files are very big, so they aren't in the repository. (5-way 1-shot) checkpoint is at https://drive.google.com/file/d/1yiz3q3xNz-llsY55g5OdodxiH1RThYuz/view?usp=sharing
* 5-way 3-shot checkpoint: https://drive.google.com/open?id=1mzeMyu4yjcLXWSi1CjFEvsrtE6EaAqv7
* 5-way 3-shot with N/A checkpoint: https://drive.google.com/open?id=1C9tn_vpFf4tDcopZTZwBN2lwnqc3sKtF
* 6-way 4-shot with N/A checkpoint: https://drive.google.com/open?id=1hdl81PcWIaA6CyJw38VGTcRs6MQ1ipfH
* can't train on prof song's gpus, not enough vram. the hpc computers have enough vram, but i couldn't get pytorch to work on them, it uses a 10 year old version of linux.... 
* however testing using this code does actually work on the gpu (but you would need to use cuda pytorch (refer to pytorch.org) and whereever you are using model do "model = model.cuda()", and also "tensor=tensor.cuda()"). refer to test_script.py
* on my laptop cpu this code takes about 2 seconds per query, on the gpu it's a lot faster, runs in under 1 second. the speed seems fine, but if there are a lot of queries it will take a decent amount of time to run.
* we should probably make our own benchmark in order to compare different models to each other. 
* the maximum length is in terms of the number of bert tokens, not in terms of the number of characters in the sentence. increasing it seems to work fine
* make sure that csv files use utf 8 encoding. open it in sublime and resave it to ensure this.
* running in macos seems to not be optimized correctly in pytorch, it makes the laptop basically unusable. *I highly recommend that you only run this code on the server. you can follow the directions in the knowcomp manual to make jupyter lab work correctly from the server*
* I investigated if there would be any issues because the maximum number of bert tokens allowed is 128. I don't think that there would be many problems due to this. From my testing, the 128 token limit is only reached with extremely long sentences, which are definitely not the norm anyway.
* make sure that there are no spaces in unexpected places, because they can cause problems since I am assuming that the strings match up exactly always.
* also you should only pass 1 sentence at a time.
* tried out the 5-1 and 5-3-na3 models on the more realistic dataset - the 5-3 and 5-3-na3 models are the ones which work the best for sure. 5-3-na3 may be slightly better than the other one imo. at this point both seem to have only around 50% accuracies.
* which entity is the head and which one is the tail definitely matters, the results are different if they are swapped. The softmax results can also be significantly different. I'm not sure if this is due to how the model was trained or due to the support dataset.
* also if there are multiple relations in the same sentence additional processing will have to be done to figure out the actual results. but at least in this model you have a chance to actually figure out the different relations, if you use a classifier model you definitely won't be able to.
* the choice of support sentences definitely seems to have a significant effect on the output of the model. simpler sentences seem to work better.
* also which words are used as the head and the tail probably matter. one problem with the spacy ner model is that it doesn't detect long phrases as entities. ex. in "Trump had opposed President Obama's invasion of Iraq", i think i would want the entities detected to be "Trump" and "President Obama's invasion of Iraq", but instead the model detects "Trump", "Obama" and "Iraq" - this probably affects the accuracy of the output. I could try to test this.....
* need to test how much things like tenses and stuff affect the output. 
* i was actually accidently running it on the cpu on the server, it runs pretty fast on the cpu, like a quarter of a second per prediction. it doesn't actually seem to run much faster on the gpu. However, when running in this jupyter notebook the gpu sometimes runs  out of memory.... which is very weird.... this didn't happen when using the script for some reason. it outputs some predictions, then it runs out of memory and crashes.... i guess we'll just have to use the cpu.
* with 4-shot rather than 3-shot it seems to work better. with 5-shot it seems to work about the same as 4-shot. the na3 model definitely seems to work better with 5-shot.
* noticed that using the exact same word as in the relation support dataset doesn't seem to matter much, synonyms seem to produce pretty much the same output tensor.
* it's important that the head and tail are the name of the full entity - ex. in "Trump hacked Obama's laptop", the tail should be "Obama's laptop", not "Obama". Then it works A LOT better, and it is usually accurate.
* the 5-3-na3 model tested using 5 way 5 shot seems to work pretty damn well.....
* the 6-4-na3 model just seems to have worse performance
* adding sentiment analysis makes it take quite a bit longer, especially nltk
* relation_support_dataset_2 works pretty well, relation_support_dataset_3 doesn't work that well for some reason... actually dataset 2 also has the same problem.... both sometimes only predict one relation most of the time for some reason...
* also, when copying stuff from online newspaper articles, sometimes the characters are not ascii. to reveal this, save them as utf-8 in sublime, then reopen the csvs in excel. usually the commas and quotation marks are messed up, and they need to be fixed manually.