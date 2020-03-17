"""
    Coreference Model using BERT with NER
    to generate queries from given text.
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
from textblob import TextBlob


class NERCoref(object):
    """
        Class Implementation for the Coreference
        Resolution model.
        
        Attributes:
        
    """
    def __init__(self, bert_model="bert_large", num_gpus=0):
        # BERT Tokenizer
        indent = "========"
        proj_path = os.getcwd().split("src")[0]
        
        print(indent + " loading BERT Tokenizer " + indent)
        sys.path.insert(1, proj_path + 'models/coref/')
        from bert import tokenization
        self.tokenizer = tokenization.FullTokenizer(
            vocab_file= proj_path + 'models/' + bert_model + '/vocab.txt',
            do_lower_case=False)
        
        # load NER model
        print(indent + " loading Flair NER model " + indent)
        self.ner_tagger = SequenceTagger.load('ner')

        # load spacy dependency parser
        print(indent + " loading Spacy Dependency Parser ===" + indent)
        self.dep_parser = spacy.load("en_core_web_sm", disable=['ner', 'tagger'])
        
        # initialise coref environment
        print(indent + " Initialising coref environment " + indent)
        import util
        os.environ['data_dir'] = proj_path + "models/"
        os.system("export data_dir")

        util.set_gpus(num_gpus)
        print("Running experiment: {}".format(bert_model))
        config = pyhocon.ConfigFactory.parse_file(
            proj_path + "models/coref/experiments.conf")[bert_model]
        
        config["log_dir"] = util.mkdirs(os.path.join(config["log_root"], bert_model))
        print(pyhocon.HOCONConverter.convert(config, "hocon"))
        log_dir = config["log_dir"]

        self.model = util.get_model(config)
        self.session = tf.Session()
        self.model.restore(self.session)
        
        print("===========================")
        print("=== Initialisation Done ===")
        print("===========================")
        
    
    def get_subtoken_map(self, tokens):
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
    
    
    def get_sentence_map(self, tokens):
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
    

    def create_jsonline(self, tokens):
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
        data['sentence_map'] = self.get_sentence_map(tokens)
        data['subtoken_map'] = self.get_subtoken_map(tokens)
        return data

    
    def bert_detokenize(self, tokens):
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
    
    
    def predict(self, example):
        """
            
        """
        tensorized_example = self.model.tensorize_example(example, is_training=False)
        feed_dict = {i:t for i,t in zip(self.model.input_tensors, tensorized_example)}
        _, _, _, top_span_starts, top_span_ends, top_antecedents, top_antecedent_scores = self.session.run(self.model.predictions, feed_dict=feed_dict)
        predicted_antecedents = self.model.get_predicted_antecedents(
            top_antecedents, 
            top_antecedent_scores)
        example["predicted_clusters"], _ = self.model.get_predicted_clusters(
            top_span_starts, 
            top_span_ends, 
            predicted_antecedents)
        example["top_spans"] = list(zip((int(i) for i in top_span_starts), 
                                        (int(i) for i in top_span_ends)))
        return example


    def coref_resolve(self, text, overlap=3):
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

                sent_tokens = self.tokenizer.tokenize(sent)
                if len(part) + len(sent_tokens) > 512:
                    sents.appendleft(sent)
                    break

                else:
                    part.extend(sent_tokens)

            # Coreference Prediction
            jsonline = self.create_jsonline(part)
            example = self.predict(jsonline)

            # Resolution
            for cluster in example["predicted_clusters"]:
                i, j = cluster[0]
                first_mention = self.bert_detokenize(example["sentences"][0][i: j+1])
                # first_mention = first_mention.translate(string.punctuation)

                # reduce longer mentions to two words
                if first_mention.count(' ') > 1:
                    dep = next(self.dep_parser(first_mention).sents)
                    r = dep.root.i
                    first_mention = str(dep[r-1:r+1])
                first_mention = self.tokenizer.tokenize(first_mention)

                # replace other mentions with first mention
                for (i, j) in cluster[1:]:
                    part[i: j+1] = first_mention

            # add partition to resolved
            resolved.extend(part)

        print(f"{nparts} partitions resolved")
        return self.bert_detokenize(resolved)


    def get_entities(self, text, disable_types=None):
        """
            Get entities for a given text. 

            Args:
                text (str): text to extract entities from.
                
                disable_types (list): list of entity types
                    that must not be detected.
                    Can include 'PER', 'LOC', 'ORG', 'MISC'

            Returns:
                ents (dict): dictionary of entities indexed
                    by sentence id. 
        """
        ents = dict()
        for idx, s in enumerate(text.split(". ")):
            sent = Sentence(s)
            self.ner_tagger.predict(sent)
            # note only PER and ORG entity types are included
            if disable_types:
                ents[idx] = [ent.text for ent in sent.get_spans('ner') 
                             if ent.tag not in disable_types]
            else:
                ents[idx] = [ent.text for ent in sent.get_spans('ner')]
        return ents

    
    def generate_queries(self, text, bidirectional=False, disable_types=None):
        """
            Generates a pandas.DataFrame of Relation Extraction
            queries.

            Args:
                text (str): document to determine relations from. 

                bidirectional (bool): If True, two queries are
                    formed for each potential relation with
                    head and tail switched. Otherwise the order
                    is with head as the earlier occuring span in text.
                
                disable_types (list): list of entity types
                    that must not be detected.
                    Can include 'PER', 'LOC', 'ORG', 'MISC'

            Returns:
                queries (dict): dictionary of potential relations
                    note - Use pandas.DataFrame.from_dict() to 
                    convert to dataframe. 
                    columns = ['sentence', 'head', 'tail'].
        """
        # resolve
        resolved = self.coref_resolve(text)

        # get entities
        ents = self.get_entities(resolved, disable_types=disable_types)

        # create queries using dataframe
        queries = {'sentence': [], 'head': [], 'tail': []}
        t = TextBlob(resolved)
        sentences = [str(s) for s in t.sentences]

        # iterate over potential entity pairs for each sentence in text
        for idx, ent_list in ents.items():
            pairs = list(combinations(set(ent_list), 2))
            
            if len(pairs) == 0:
                continue
            
            heads, tails = zip(*pairs)
            queries['sentence'].extend( len(pairs)*[sentences[idx]] )
            queries['head'].extend(heads)
            queries['tail'].extend(tails)

            if bidirectional:
                queries['sentence'].extend( len(pairs)*[sentences[idx]] )
                queries['head'].extend(tails)
                queries['tail'].extend(heads)
        return queries


if __name__ == "__main__":
    resolver = NERCoref()

    # get some text
    sys.path.append("../../")
    from src.preparation.data_loading import read_dossier
    dos = read_dossier.read_dossier()[0]

    queries = resolver.generate_queries(dos)
    for i in range(10):
        print("head:", queries["head"][i], "; tail:", queries["tail"][i])
        print("sent:", queries["sentence"][i])
        print()

