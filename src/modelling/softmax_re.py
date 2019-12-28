import sys
import spacy
import opennre
from itertools import permutations
import json

sys.path.append('../..')
from src.preparation.data_loading import read_dossier

model = opennre.get_model('wiki80_cnn_softmax')

# Dictionary implementation with range of values
class RangeDict(dict):
    def __getitem__(self, item):
        if type(item) != range:
            for key in self:
                if item in key:
                    return self[key]
            raise KeyError(item)
        else:
            return super().__getitem__(item)

# run to check if OpenNRE works
def test_run():
    sample = dict()
    sample['text'] = 'More than 2.5 million cubic yards of contaminated \
            mud will be dredged from Onondaga Lake , near Syracuse , \
            under a consent decree between the state and Honeywell \
            International that was announced yesterday .'

    sample['h'] = {'pos': [96, 104]}
    sample['t'] = {'pos': [75, 88]}
    print(model.infer(sample))

# Relation Extraction
def extract_relations():
    nlp = spacy.load('en_core_web_sm')
    articles = read_dossier.read_dossier()
    print('Steele Dossier read')
    
    valid_labels = ['PERSON', 'LOC', 'GPE', 'NORP', 'ORG', 'FAC']
    
    # only one article
    doc = nlp(articles[0])

    # entities list based on sentence char range in doc
    ents = RangeDict()
    for s in doc.sents:
        ents[range(s.start_char, s.end_char)] = []
    
    for e in doc.ents:
        if e.label_ in valid_labels:
            ents[e.start_char].append(e)
    
    rels = []
    for s in doc.sents:
        sent_range = range(s.start_char, s.end_char)
        for p in permutations(ents[sent_range], r=2):
            sample = dict()
            sample['text'] = s.text
            sample['h'] = {'pos': (p[0].start_char, p[0].end_char), 
                           'name': p[0].text}
            sample['t'] = {'pos': (p[1].start_char, p[1].end_char),
                            'name': p[1].text}
            sample['inference'] = model.infer(sample)
            rels.append(sample)
    
    with open('Steele_dossier_rels.json', 'w')  as f:
        f.write(json.dumps(rels)

if __name__=="__main__":
   rels = extract_relations()
