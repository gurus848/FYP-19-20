"""
    Coreference Model using SpanBERT with NER
    
    Note: for integrating SpanBERT Coref code,
    Update line 8 in models/coref/coref_ops.py with:

        file_path = __file__.split("coref_ops.py")[0]
        coref_op_library = tf.load_op_library(file_path + "coref_kernels.so")

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys
import json
import pyhocon
import tensorflow as tf
import string
import spacy
from itertools import combinations
from flair.data import Sentence
from flair.models import SequenceTagger
from collections import deque

indent = "========"
bert_model = "bert_large"
proj_path = __file__.split("src")[0]

# BERT Tokenizer
print(indent + " loading BERT Tokenizer " + indent)
sys.path.insert(1, proj_path + 'models/coref/')
from bert import tokenization
tokenizer = tokenization.FullTokenizer(vocab_file= proj_path + 'models/' + bert_model + '/vocab.txt',
                                       do_lower_case=False)

# initialise coref environment
print(indent + " Initialising coref environment " + indent)
import util

class CorefResolver(object):
    
    def __init__(self, bert_model):
        os.environ['data_dir'] = proj_path + "models/"
        os.system("export data_dir")

        util.set_gpus(0)
        print("Running experiment: {}".format(bert_model))
        config = pyhocon.ConfigFactory.parse_file(
            proj_path + "models/coref/experiments.conf")[bert_model]

        config["log_dir"] = util.mkdirs(os.path.join(config["log_root"], bert_model))
        print(pyhocon.HOCONConverter.convert(config, "hocon"))
        log_dir = config["log_dir"]

        self.model = util.get_model(config)
        self.session = tf.Session()
        self.model.restore(self.session)
    
    def predict(self, text):
        pass


# load NER model
print(indent + " loading Flair NER model " + indent)
ner_tagger = SequenceTagger.load('ner')

# load spacy dependency parser
print(indent + " loading Spacy Dependency Parser ===" + indent)
dep_parser = spacy.load("en_core_web_sm", disable=['ner', 'tagger'])

print("===========================")
print("=== Initialisation Done ===")
print("===========================")


def get_subtoken_map(tokens):
    """
        Provides a flat list of int for each bert token
        its corresponding word in the text.
        
        Args:
            tokens (list): list of bert tokens. 
        
        Returns:
            subtoken_map (list): list of int with len equal to
                number of bert tokens.
    """
    subtoken_map = list()
    i = -1
    for t in range(len(tokens)):
        i += 0 if tokens[t].startswith('##') else 1
        subtoken_map.append(i)
    return [0] + subtoken_map + [i]


def get_sentence_map(tokens):
    """
        Provides a flat list of int for each bert token
        its corresponding word in the text.
        
        Args:
            tokens (list): list of bert tokens. 
        
        Returns:
            subtoken_map (list): list of int with len equal to
                number of bert tokens.
    """
    sentence_map = list()
    i = 0
    for t in range(len(tokens)):
        if tokens[t] == ".":
            i += 1
        sentence_map.append(i)
    return [0] + sentence_map + [i]


def create_jsonline(tokens):
    """
        Returns jsonline format which is inputtable
        to the Coreference Resolution model
        
        Args:
            tokens (list): list of bert tokens, len(tokens) <= 512
        
        Returns:
            data (dict): jsonline-style dictionary with relevant preprocessing
    """
    # check no. of tokens
    assert len(tokens) <= 512, "Input exceeds maximum number of tokens"
    data = dict()
    data['clusters'] = []
    data['doc_key'] = 'nw'
    data['sentences'] = [['[CLS]'] + tokens + ['[SEP]']]
    # setting to No speaker for every subword at the moment
    data['speakers'] = [['[SPL]'] + list(map(lambda x: ""*len(x), tokens)) + ['[SPL]']]
    data['sentence_map'] = get_sentence_map(tokens)
    data['subtoken_map'] = get_subtoken_map(tokens)
    return data


def bert_detokenize(tokens):
    """
        Converts a list of bert tokens to text.
        
        Args:
            tokens (list): list of bert tokens
        
        Returns:
            text (str): the merged text from tokens. 
    """
    text = ""
    for t in tokens:
        if t.startswith("##"):
            text += t[2:]
        
        elif t in string.punctuation:
            text += t
        
        else:
            text += ("", " ")[text != ""] + t
    return text


def coref_resolve(text, overlap=1):
    """
        Performs Coreference Resolution for a given text.
        A waterfall-style partitioning is used for texts
        since the maximum number of allowed bert tokens 
        for Coreference resolution at once is 512. 
        
        Args:
            text (str): The document to be resolved. 
        
            overlap (int): number of sentences to overlap
                between each partition of the text.
       
        Returns:
            resolved (str): The input text with all references
                replaced with first mentions. 
    """
    # check overlap
    assert type(overlap)==int and overlap > 0
    
    # do waterfall: partition the text into full sentences upto 512 bert tokens.
    sents = deque([sent+"." for sent in text.split(". ") if len(sent) > 2])
    
    # list of coreference resolved sentences as bert tokens
    resolved = list()
    nparts = 0
    
    with tf.Session() as session:
        model.restore(session)
        
        while sents:
            # create partition of 512 bert tokens
            part = list()
            nparts += 1

            # insert overlap sentences to partition
            if len(resolved) >= overlap:
                l = -1
                while part.count('.') < overlap+1:
                    part.append(resolved[l])
                    l -= 1

            # tokens were inserted in reverse order.
            part = part[:-1]
            part.reverse()

            # insert rest  of partition with unresolved sentences 
            # to partition upto 512 bert tokens
            while True:
                if sents:
                    sent = sents.popleft()
                else:
                    break
                
                sent_tokens = tokenizer.tokenize(sent)
                if len(part) + len(sent_tokens) > 512:
                    sents.appendleft(sent)
                    break
                    
                else:
                    part.extend(sent_tokens)

            # Coreference Prediction
            example = create_jsonline(part)
            tensorized_example = model.tensorize_example(example, is_training=False)
            feed_dict = {i:t for i,t in zip(model.input_tensors, tensorized_example)}
            _, _, _, top_span_starts, top_span_ends, top_antecedents, top_antecedent_scores = session.run(model.predictions, feed_dict=feed_dict)
            predicted_antecedents = model.get_predicted_antecedents(
                top_antecedents, 
                top_antecedent_scores)
            example["predicted_clusters"], _ = model.get_predicted_clusters(
                top_span_starts, 
                top_span_ends, 
                predicted_antecedents)
            example["top_spans"] = list(zip((int(i) for i in top_span_starts), 
                                            (int(i) for i in top_span_ends)))

            # Resolution
            for cluster in example["predicted_clusters"]:
                i, j = cluster[0]
                first_mention = bert_detokenize(example["sentences"][0][i: j+1])
                # first_mention = first_mention.translate(string.punctuation)
                
                print()
                
                # reduce longer mentions to two words
                if first_mention.count(' ') > 1:
                    dep = next(dep_parser(first_mention).sents)
                    print(dep.root)
                    r = dep.root.i
                    first_mention = str(dep[r-1:r+1])

                # replace other mentions with first mention
                for (i, j) in cluster[1:]:
                    part[i: j+1] = first_mention

            # add partition to resolved
            resolved.extend(part)

    print(f"{nparts} partitions resolved")
    return bert_detokenize(resolved)


def get_entities(text):
    """
        Get entities for a given text. 
        
        Args:
            text (str): text to extract entities from.
            
        Returns:
            ents (dict): dictionary of entities indexed
                by sentence id. 
    """
    ents = dict()
    for idx, s in enumerate(text.split(". ")):
        sent = Sentence(s)
        ner_tagger.predict(sent)
        # note only PER and ORG entity types are included
        ents[idx] = [ent.text for ent in sent.get_spans('ner') 
                     if ent.tag in "PER, ORG"]
    return ents


def generate_queries(text, bidirectional=False):
    """
        Generates a pandas.DataFrame of Relation Extraction
        queries.
        
        Args:
            text (str): document to determine relations from. 
            
            bidirectional (bool): If True, two queries are
                formed for each potential relation with
                head and tail switched. Otherwise the order
                is with head as the earlier occuring span in text. 
        
        Returns:
            queries (dict): dictionary of potential relations
                note - Use pandas.DataFrame.from_dict() to 
                convert to dataframe. 
                columns = ['sentence', 'head', 'tail'].
    """
    # resolve
    resolved = coref_resolve(text)
    
    # get entities
    ents = get_entities(resolved)
    
    # create queries using dataframe
    queries = {'sentence': [], 'head': [], 'tail': []}
    sentences = [s+"." for s in resolved.split(". ")]
    
    # iterate over potential entity pairs for each sentence in text
    for idx, ent_list in ents.items():
        pairs = list(combinations(ent_list, 2))
        heads, tails = zip(*pairs)
        queries['sentence'].extend( len(pairs)*[sentences[idx]] )
        queries['head'].extend(heads)
        queries['tail'].extend(tails)
        
        if bidirectional:
            queries['sentence'].extend( len(pairs)*[sentences[idx]] )
            queries['head'].extend(tails)
            queries['tail'].extend(heads)
    return queries