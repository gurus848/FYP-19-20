import sys
import json

# BERT Tokenizer
# TODO update the paths when the file is moved
sys.path.append('../')
from bert import tokenization
tokenizer = tokenization.FullTokenizer(vocab_file='../../../models/bert_large/vocab.txt', do_lower_case=False)

# flat list mapping subtoken to respective word
def get_subtoken_map(sent_list):
    subtoken_map = list()
    i = -1
    for sent in sent_list:
        for t in range(len(sent)):
            if (not sent[t].startswith('#') \
            and sent[t-1] != "[CLS]") \
            and sent[t] != "[SEP]"
			and sent[t] != ".":
                i += 1
            subtoken_map.append(i)
    return subtoken_map


# [item for sublist in [[i]*len(sents[i]) for i in range(len(sents))] for item in sublist]
# map word to sen
def get_sentence_map(sent_list):
    sent_map = list()
    for i in range(len(sent_list)):
        sent_map.extend([i]*len(sent_list[i]))
    return sent_map


# create jsonline file
def create_jsonline(text, path):
	# texts = text if type(text) == list else [text] 
	sents = [s+" ." for s in text.split(".") if len(s) > 2]
	data = dict()
	data['clusters'] = []
	data['doc_key'] = 'nw'
	data['sentences'] = [s.split(" ") for s in sents]
	data['speakers'] =  [[""]*len(s) for s in sents] # setting to No speaker for every subword at the moment
	data['sentence_map'] = get_sentence_map(sents)
	data['subtoken_map'] = get_subtoken_map(sents)

	with open(path, 'w') as f:
		f.write(json.dumps(data))


if __name__=="main":
	sys.path.append("../../")
	from src.preparation.data_loading import read_dossier
	dos = read_dossier.read_dossier()
	create_jsonline(dos[0], "dossier_for_coref.jsonlines")
