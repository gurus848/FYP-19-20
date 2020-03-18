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


class LazyStringSet(set):
    """
        Set of Strings with a lazy
        accessor. 
        
        Attributes:
            set (set): stores only string 
            type elementselements.
    """
    def __init__(self):
        self.set = set()
    
    def get(self, x):
        """
            if the string x is a subset of
            any element present in the set, 
            that element will be returned.
        """
        assert type(x) == str
        for i in self.set:
            if x in i:
                return i
        return None
    
    def put(self, x):
        """
        Inserts new string element x to set.
        Returns True if inserted, otherwise False.
        """
        assert type(x) == str
        if self.get(x) is None:
            self.set.add(x)
            return True
        return False


class NERCoref(object):
    """
        Class Implementation for the Coreference
        Resolution model.
        
        Attributes:
        
    """
    def __init__(self, bert_model="bert_large", num_gpus=0):
        # BERT Tokenizer
        indent = "========"
        proj_path = os.path.abspath(os.path.dirname(__file__)).split("src")[0]
        
        print(indent + " loading BERT Tokenizer " + indent)
        sys.path.insert(1, proj_path + 'models/coref/')
        from models.coref.bert import tokenization
        self.tokenizer = tokenization.FullTokenizer(
            vocab_file = proj_path + 'models/' + bert_model + '/vocab.txt',
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
            
            elif len(text) > 0 and text[-1] == "'" and t in "sS":
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


    def para_resolve(self, text, markers=False):
        """
            Performs Coreference Resolution for a given text.
            The text is partitioned into paragraphs since
            the maximum number of allowed bert tokens 
            for Coreference resolution at once is 512. 

            Args:
                text (str): The document to be resolved.

            Returns:
                resolved (str): The input text with all references
                    replaced with first mentions. 
           
            Notes:
                Assumed that the paragraphs are separated by'\n'.
        """
        paragraphs = text.split('\n')
        # list of resolved paragraphs as string
        resolved = list() 
        # store for inter paragraph first mention of entities
        global_mentions = LazyStringSet() 
        
        for para in paragraphs:
            # paragraph as BERT Tokens
            para_tokens = self.tokenizer.tokenize(para)
            
            # Coreference Prediction
            jsonline = self.create_jsonline(para_tokens)
            example = self.predict(jsonline)
            
            # Resolution
            # store all coreferences
            corefs = dict()
            for cluster in example["predicted_clusters"]:
                i, j = cluster[0] # indices of first mention
                first_mention = example['sentences'][0][i:j+1]
                fm_str = self.bert_detokenize(first_mention)
                
                # remove possession modifier
                if "'" in first_mention:
                    if "s" in first_mention:
                        first_mention.remove("'")
                        first_mention.remove("s")

                    if "S" in first_mention:
                        first_mention.remove("'")
                        first_mention.remove("S")
                
                # check for global coreference: inter paragraph. 
                # (Inefficent from detokenizer calls)
                gm = global_mentions.get(fm_str)
                if gm:
                    first_mention = self.tokenizer.tokenize(gm)
                else:
                    global_mentions.put(fm_str)
                
                # try to reduce longer first mentions to two words
#                 first_mention = self.bert_detokenize(first_mention)
#                 first_mention = first_mention.translate(string.punctuation)
#                 ent_reduced = self.reduce_entity(first_mention)
#                 first_mention = self.tokenizer.tokenize(ent_reduced)

                # store other mentions indices by first mention
                for (i, j) in cluster:
                    corefs[(i, j)] = first_mention

            # replace all mentions with their first mentions
            para_resolved = list()
            prev_i, prev_j = 0, 0
            
            for (i, j), fm in sorted(corefs.items()):
                if markers:
                    fm = ['$'] + fm + ['$']
                    
                # check intersection: resolution within resolution
                if i > prev_i and i < prev_j and j > prev_i and j < prev_j:
                    # get last resolve
                    delta = prev_j - prev_i + 1
                    last_resolve = para_resolved[-delta:]
                    para_resolved[-delta:] = last_resolve[0:i-prev_i-1] \
                                             + fm \
                                             + last_resolve[j-prev_i+1:]
                else:
                    para_resolved.extend(para_tokens[prev_j: i-1])
                    para_resolved.extend(fm)
                
                prev_i, prev_j = i, j
            
            # add paragraph to resolved
            para_resolved = self.bert_detokenize(para_resolved)
            resolved.append(para_resolved)
        
        # return the resolved text
        return "\n".join(resolved)
    
    
    def reduce_entity(self, entname):
        """
            Tries to reduce entity mentions longer than
            two words or resolve multiple entity types
            in a phrase.
            
            Args:
                entname (str): entity mention to reduce.
            
            Returns:
                ent_reduced (str): entity mention in 
                    two words.
        """
        ent_reduced = ""
        if entname.count(" ") > 1:
            ent_reduced = entname
        
        else:
            phrase = Sentence(entname)
            self.ner_tagger.predict(phrase)
            fm_ents = phrase.get_spans('ner')

            # check for multiple entities in mention phrase
            # assume the dependency root as entity mention
            if len(fm_ents) > 0:
                dep = next(self.dep_parser(entname).sents)
                r = dep.root.idx

                for ent in fm_ents:
                    if r in range(ent.start_pos, ent.end_pos):
                        ent_reduced = ent.text
        return ent_reduced
                    

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
            # improves NER prediction
            sent = [" "+t if t in string.punctuation else t for t in s]
            sent = "".join(sent)
            sent = Sentence(sent)
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
        sentences = [s+"." for s in resolved.split(". ")]

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
    from src.preparation.data_loading import read_dossier
    dos = read_dossier.read_dossier(paragraphs=True)[0]
    print(resolver.para_resolve(dos))

#     queries = resolver.generate_queries(dos)
#     for i in range(10):
#         print("head:", queries["head"][i], "; tail:", queries["tail"][i])
#         print("sent:", queries["sentence"][i])
#         print()