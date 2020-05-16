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
from functools import reduce
from operator import concat
from flair.data import Sentence
from flair.models import SequenceTagger
from collections import deque
from textblob import TextBlob
import re


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
            tokenizer: BERT tokenizer provided by models/coref.
            ner_tagger: NER tagger from flair package. 
            dep_parser: dependency parser from Spacy package.
            model: tensorflow model impelementation from models/coref.
            session: tensorflow session. 
    """
    def __init__(self, bert_model="bert_large", num_gpus=0):
        # BERT Tokenizer
        indent = "========"
        proj_path = os.path.abspath(os.path.dirname(__file__)).split("src")[0]
        
        print(indent + " loading BERT Tokenizer " + indent)
        sys.path.insert(1, proj_path + 'models/coref/')
        # from models.coref.bert import tokenization
        from bert import tokenization
        self.tokenizer = tokenization.FullTokenizer(
            vocab_file = proj_path + 'models/' + bert_model + '/vocab.txt',
            do_lower_case=False)
        
        # load NER model
        print(indent + " loading Flair NER model " + indent)
        self.ner_tagger = SequenceTagger.load('ner')

        # load spacy dependency parser
        print(indent + " loading Spacy Dependency Parser ===" + indent)
        self.dep_parser = spacy.load("en_core_web_sm")
        
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
    
    
    def _get_space_map(self, text, tokens):
        """
            Provides a flat list of 0's and 1's for whether
            a space exists after a bert token in the text.
            
            Args:
                text: text that has been tokenized to tokens.
                
                tokens: bert tokens from text.
            
            Returns:
                spaces (list): list indexed by index of token
                    with corresponding 1 for no space after the
                    token, 0 otherwise.
        """
        detokenized = ""
        spaces = list()
        for i, tok in enumerate(tokens):
            detokenized += tok[2:] if tok.startswith('##') else tok

            n = len(detokenized)
            if n == len(text):
                spaces.append(0)

            elif text[n] == " ":
                detokenized += " "
                spaces.append(1)
            else:
                spaces.append(0)
                
        spaces = [-1] + spaces + [-1]
        return spaces
        
    
    def _get_subtoken_map(self, tokens):
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
    
    
    def _get_sentence_map(self, tokens):
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
    

    def _create_jsonline(self, text):
        """
            Returns jsonline format which is inputtable
            to the Coreference Resolution model

            Args:
                text (str): text to be run the 
                    Coreference Resolution Model.
                
                Note: text must be result in more than 512 BERT tokens.

            Returns:
                data (dict): jsonline-style dictionary with relevant preprocessing
        """
        tokens = self.tokenizer.tokenize(text)
        # check no. of tokens
        assert len(tokens) <= 512, "Input exceeds maximum number of tokens"
        data = dict()
        data['clusters'] = []
        data['doc_key'] = 'nw'
        data['sentences'] = [['[CLS]'] + tokens + ['[SEP]']]
        # setting to No speaker for every subword at the moment
        data['speakers'] = [['[SPL]'] + list(map(lambda x: ""*len(x), tokens)) + ['[SPL]']]
        data['sentence_map'] = self._get_sentence_map(tokens)
        data['subtoken_map'] = self._get_subtoken_map(tokens)
        data['space_map'] = self._get_space_map(text, tokens)
        return data

    
    def _bert_detokenize(self, tokens, space_map):
        """
            Converts a list of bert tokens to text.

            Args:
                tokens (list): list of bert tokens

            Returns:
                detokenized (str): the merged text from tokens. 
        """
        # error handling
        if len(tokens) != len(space_map):
            toks_utf = [t.encode('utf-8') for t in tokens]
            print(list(zip(toks_utf[:len(space_map)], space_map)))
            assert len(tokens) == len(space_map), f"{len(tokens)} tokens and {len(space_map)} spaces"
        
        # detokenisation
        detokenized = ""
        for idx, tok in enumerate(tokens):
            # don't consider [CLS] and [SEP] during detokenisation
            if space_map[idx] == -1:
                continue
            
            # add the text
            detokenized += tok[2:] if tok.startswith('##') else tok
            
            # add the space
            if space_map[idx]:
                detokenized += " "
        
        # return detokenized text
        return detokenized
    
    
    def _predict(self, example):
        """
            Predicts coreference clusters using
            state-of-the-art Coreference Resolution 
            models/coref. 
            
            Args:
                example (jsonline): a input format 
                    defined as per the coreference
                    resolution framework. 
            
            Returns:
                example (jsonline): updates the input
                    with additional fields for the
                    predicted clusters in
                    example["predicted_clusters"].
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
    
    
    def _resolve(self, para, global_mentions, markers=False):
        """
            Performs Coreference Resolution for a given text.
            
            Args:
                text (str): The document to be resolved.
                
                global_mentions (LazyStringSet): to match the
                    resolved entities in the current document
                    to the given global mentions. 
                    
                markers (bool): if set, the resolved spans
                    in text will be quoted using '*'.
                    For debugging purposes only.
                
            Returns:
                resolved(str): the resolved text.
        """

        # Coreference Prediction
        jsonline = self._create_jsonline(para)
        example = self._predict(jsonline)
        
        # if there are no clusters to resolve
        if len(example["predicted_clusters"]) == 0:
            return para

        # Resolution
        # store all coreferences
        corefs = dict()
        for cluster in example["predicted_clusters"]:
            # pick the largest mention in the first five mentions as the first mention
            i, j = cluster[0]
            for m, n in cluster[:5]:
                if n-m > j-i:
                    i, j = m, n
            
            first_mention = example['sentences'][0][i:j+1]
            # take one less for customising last token's spacing
            fm_space_map = example['space_map'][i:j]
            
            # create dependency parse tree for checking special cases
            fm_str = self._bert_detokenize(first_mention, fm_space_map + [0])
            fm_doc = self.dep_parser(fm_str)
            
            # avoid replacing common nouns
            if len(fm_doc.ents) == 0:
                continue
            
            # Appositional modifier case for PERSON only
            if "appos" in [t.dep_ for t in fm_doc]:
                for ent in fm_doc.ents:
                    if ent.label_ == "PERSON":
                        fm_str = ent.text
                        fm_tok = self.tokenizer.tokenize(fm_str)
                        fm_space_map = self._get_space_map(fm_str, fm_tok)[1:-2]
                        first_mention = fm_tok
                        break

            # store other mentions indices by first mention
            for (i, j) in cluster[1:]:
                corefs[(i, j)] = (first_mention, fm_space_map)

        # replace all mentions with their first mentions
        para_resolved = list()
        spaces_resolved = list()
        prev_i, prev_j = 0, 0

        for (i, j), (fm, spaces) in sorted(corefs.items()):
            fm_space_map = [2 if s == 1 else 0 for s in spaces]
            # add the space of the last token in replaced text
            fm_space_map.append(example['space_map'][j])

            if markers:
                fm = ['*'] + fm + ['*']
                fm_space_map = [0] + fm_space_map + [1]

            # check intersection: resolution within resolution
            if i > prev_i and i < prev_j and j > prev_i and j < prev_j:
                # get last resolve
                delta = prev_j - prev_i + 1
                last_resolve = para_resolved[-delta:]
                last_space_map = spaces_resolved[-delta:]
                para_resolved[-delta:] = last_resolve[0:i-prev_i-1] \
                                         + fm \
                                         + last_resolve[j-prev_i+1:]
                spaces_resolved[-delta:] = last_space_map[0:i-prev_i-1] \
                                           + fm_space_map \
                                           + last_space_map[j-prev_i+1:]
            else:
                if prev_j == 0:
                    para_resolved.extend(example['sentences'][0][prev_j:i])
                    spaces_resolved.extend(example['space_map'][prev_j:i])
                else:
                    para_resolved.extend(example['sentences'][0][prev_j+1:i])
                    spaces_resolved.extend(example['space_map'][prev_j+1:i])
                
                para_resolved.extend(fm)
                spaces_resolved.extend(fm_space_map)  

                prev_i, prev_j = i, j
            
        # add the remaining tokens to resolved
        para_resolved.extend(example['sentences'][0][prev_j+1:])
        spaces_resolved.extend(example['space_map'][prev_j+1:])

        # add paragraph to resolved
        resolved = self._bert_detokenize(para_resolved, spaces_resolved)
        
        return resolved
    

    def sent_resolve(self, sents, markers=False):
        """
            Performs Coreference Resolution for a given text.
            The text is partitioned into sentences in 
            waterfall style. For each sentence to be resolved, 
            overlap number of resolved sentences will be 
            concatenated for context.
 
            the maximum number of allowed bert tokens 
            for Coreference resolution at once is 512. 

            Args:
                sents (list): list of string sentences to be resolved.
                
                markers (bool): if set, the resolved spans
                    in text will be quoted using '*'.
                    For debugging purposes only. 

            Returns:
                resolved (list): list of string resolved sentences. 
        """
        # list of resolved sentences as list of sentences tokenized
        resolved = list()
        for idx, sent in enumerate(sents):
            sent = sent.strip()
            sent_resolved = self._resolve(sent, None, markers=markers)
            resolved.append(sent_resolved)
        return resolved
    
    
    def para_resolve(self, sents, overlap=1, markers=False):
        """
            Performs Coreference Resolution for a given text.
            The text is partitioned into paragraphs with overlapping
            sentences since the maximum number of allowed bert tokens 
            for Coreference resolution at once is 512. 

            Args:
                sents (list): list of string sentences to be resolved.
                
                overlap (int): number of sentences to use
                    for each resolve for context.
                    Recommended range: 1, 2, 3. 
                    Note: If set too high, will face 
                    AssertionError for maximum BERT tokens allowed.
            
                markers (bool): if set, the resolved spans
                    in text will be quoted using '*'.
                    For debugging purposes only. 

            Returns:
                resolved (list): Same list of input sentences with
                    coreferences resolved.
           
            Notes:
                Assumed that the paragraphs are separated by'\n'.
        """
        # list of resolved paragraphs as string
        resolved = list() 
        # store for inter paragraph first mention of entities
        global_mentions = LazyStringSet() 
        
        for idx, sent in enumerate(sents):
            sent = sent.strip()
            para = "\s".join(resolved[-overlap:] + [sent])

            # Coreference Prediction
            para_resolved = self._resolve(para, global_mentions, markers=markers)
            
            # append to resolved
            resolved.append(para_resolved.split("\s")[-1].strip())
        return resolved
    

    def get_entities(self, sentences, allowed_types=None, ent_span=False):
        """
            Get entities for a given text. 

            Args:
                sentences (list): list of string sentences to 
                    obtain entities from.
                
                allowed_types (list): list of entity types
                    that must be detected. Can include any of 
                    the entity types provided by Flair conll-2003 model.
                    
                    if None given, all types will be allowed.

            Returns:
                ents (dict): dictionary of entities indexed
                    by sentence id. 
        """
        ents = dict()
        
        # dependency parsing on sentences
        docs = [self.dep_parser(s) for s in sentences]
        
        for idx, s in enumerate(sentences):
            sent = Sentence(s)
            self.ner_tagger.predict(sent)
            # noun chunks to replace genetives
            noun_chunks = list(docs[idx].noun_chunks)
            ents_cache = ""
            
            ents[idx] = list()
            for ent in sent.get_spans('ner'):
                # check entity type
                if allowed_types and ent.tag not in allowed_types:
                    continue
                
                # avoid substring entities and appositional modifiers
                ent_span = docs[idx].char_span(ent.start_pos, ent.end_pos)
                if ent.text in ents_cache or str(ent_span.root) in ents_cache:
                    continue
                
                # Flair Interface
                ent_str, start, end = ent.text, ent.start_pos, ent.end_pos
                
                # check genetive
                if ent.text.endswith("'s") or ent.text.endswith("’s"):
                    ent_str = ent.text[:-2]
#                     # Spacy Interface
#                     for nc in noun_chunks:
#                         if ent.text in str(nc) and ent.start_pos >= nc.start:
#                             ent_str = str(nc)
#                             start, end = nc.start, nc.end
#                             break

                            
                # strip punctuation from the entity name 
                if ent_str[0] in "!\"#$%&\'*+,-./:;<=>?@[\\]^_`{|}~’“":
                    start += 1
                    ent_str = ent_str[1:]
                if ent_str[-1] in "!\"#$%&\'*+,-./:;<=>?@[\\]^_`{|}~’“":
                    end -= 1
                    ent_str = ent_str[:-1]

                # append to entities
                ents[idx].append((ent_str, start, end))
                ents_cache += " " + ent_str

        return ents

    
    def generate_queries(self, text, use_sent=False, overlap=1, bidirectional=False, allowed_types=None):
        """
            Generates a pandas.DataFrame of Relation Extraction
            queries.

            Args:
                text (str): document to determine relations from. 

                bidirectional (bool): If True, two queries are
                    formed for each potential relation with
                    head and tail switched. Otherwise the order
                    is with head as the earlier occuring span in text.
                
                allowed_types (list): list of entity types
                    that must be detected.
                    Can include 'PER', 'LOC', 'ORG', 'MISC'
                    if set to None, all types will detected. 

            Returns:
                queries (dict): dictionary of potential relations
                    note - Use pandas.DataFrame.from_dict() to 
                    convert to dataframe. 
                    columns = ['sentence', 'head', 'tail'].
        """
        # get sentences
        sents = text.split('\n')
        
        # resolve
        if use_sent:
        	resolved = self.sent_resolve(sents, markers=False)
        else:
            resolved = self.para_resolve(sents, overlap=overlap, markers=False) 

        # get entities
        ents = self.get_entities(resolved, allowed_types=allowed_types)

        # create queries using dataframe
        queries = {'sentence': [], 'head': [], 'tail': [], 
                   'head_start': [], 'head_end': [],
                   'tail_start': [], 'tail_end': []}

        # iterate over potential entity pairs for each sentence in text
        for idx, ent_list in ents.items():
            pairs = list(combinations(set(ent_list), 2))
            
            # remove similar entity mention pairs            
            pairs_cp = [p for p in pairs if p[0][0] != p[1][0]]

            # sentences with no entitiess
            if len(pairs_cp) == 0:
                for k in queries.keys():
                    if k == 'sentence':
                        queries['sentence'].append(resolved[idx])
                    else:
                        queries[k].append(None)
                continue
                
            heads, tails = zip(*pairs_cp)
            h_ents, h_starts, h_ends = zip(*heads)
            t_ents, t_starts, t_ends = zip(*tails)
            queries['sentence'].extend( len(pairs_cp)*[resolved[idx]] )
            queries['head'].extend(h_ents)
            queries['tail'].extend(t_ents)
            queries['head_start'].extend(h_starts)
            queries['head_end'].extend(h_ends)
            queries['tail_start'].extend(t_starts)
            queries['tail_end'].extend(t_ends)
            
            if bidirectional:
                queries['sentence'].extend( len(pairs_cp)*[resolved[idx]] )
                queries['head'].extend(t_ents)
                queries['tail'].extend(h_ents)
                queries['head_start'].extend(t_starts)
                queries['head_end'].extend(t_ends)
                queries['tail_start'].extend(h_starts)
                queries['tail_end'].extend(h_ends)
        
        return queries


if __name__ == "__main__":
    with open("../../test/article.txt", encoding='utf-8') as f:
        text = f.read()
    
    resolver = NERCoref()
    queries = resolver.generate_queries(text, use_sent=False)
    
    for i in range(len(queries['head'])):
        print("--------------------------------------------------------")
        for k in queries.keys():
            if type(queries[k][i]) == str:
                print(f"{k}: {queries[k][i].encode('utf-8')}")
            else:
                print(f"{k}: {queries[k][i]}")
