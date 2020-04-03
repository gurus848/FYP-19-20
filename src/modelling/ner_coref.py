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
        for idx, tok in enumerate(tokens[:-1]):
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

        # Resolution
        # store all coreferences
        corefs = dict()
        for cluster in example["predicted_clusters"]:
            i, j = cluster[0] # indices of first mention
            first_mention = example['sentences'][0][i:j+1]
            # take one less for customising last token's spacing
            fm_space_map = example['space_map'][i:j]
            # fm_str = self._bert_detokenize(first_mention, fm_space_map)

            # check for global coreference: inter paragraph. 
            # (Inefficent from detokenizer calls)
#             gm = global_mentions.get(fm_str)
#             if gm:
#                 first_mention = self.tokenizer.tokenize(gm)
#             else:
#                 global_mentions.put(fm_str)

            # store other mentions indices by first mention
            for (i, j) in cluster:
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
    

    def sent_resolve(self, text, overlap=1, markers=False):
        """
            Performs Coreference Resolution for a given text.
            The text is partitioned into sentences in 
            waterfall style. For each sentence to be resolved, 
            overlap number of resolved sentences will be 
            concatenated for context.
 
            the maximum number of allowed bert tokens 
            for Coreference resolution at once is 512. 

            Args:
                text (str): The document to be resolved.
                
                overlap (int): number of sentences to use
                    for each resolve for context.
                    Recommended range: 1, 2, 3. 
                    Note: If set too high, will face 
                    AssertionError
            for maximum BERT tokens allowed.
                
                markers (bool): if set, the resolved spans
                    in text will be quoted using '*'.
                    For debugging purposes only. 

            Returns:
                resolved (str): The input text with all references
                    replaced with first mentions. 
           
            Notes:
                Assumed that the sentences are separated by'\n'.
        """
        sentences = text.split('\n')
        # list of resolved sentences as list of sentences tokenized
        resolved = list()
        # store for inter paragraph first mention of entities
        global_mentions = LazyStringSet() 
        
        for idx, sent in enumerate(sentences):
            sent = sent.strip()
            para = " ".join(resolved[-overlap:] + [sent])
            # Coreference Prediction
            para_resolved = self._resolve(para, global_mentions, markers=markers)
            
            # append to resolved
            resolved.append(para_resolved.split(".")[-2].strip() + ".")
        
        return resolved
    
    
    def para_resolve(self, text, markers=False):
        """
            Performs Coreference Resolution for a given text.
            The text is partitioned into paragraphs since
            the maximum number of allowed bert tokens 
            for Coreference resolution at once is 512. 

            Args:
                text (str): The document to be resolved.
                
                markers (bool): if set, the resolved spans
                    in text will be quoted using '*'.
                    For debugging purposes only. 

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
            para = para.strip()
            para_resolved = self._resolve(para, global_mentions, markers=markers)
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
                    

    def get_entities(self, text, disable_types=None, ent_span=False):
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
        t = TextBlob(text)
        sentences = [str(s) for s in t.sentences]
        for idx, s in enumerate(sentences):
            # improves NER prediction
            sent = [" "+t if t in string.punctuation else t for t in s]
            sent = "".join(sent)
            sent = Sentence(sent)
            self.ner_tagger.predict(sent)

            ents[idx] = list()
            for ent in sent.get_spans('ner'):
                if disable_types and ent.tag in disable_types:
                    continue
                else:
                    ents[idx].append(ent.text)
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
        resolved = self.para_resolve(text)

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
    import codecs
    with codecs.open("../../../temp.txt", encoding='utf-8') as f:
        text = f.read()

    resolver = NERCoref()
    resolved = resolver.para_resolve(text, markers=False)
    print(resolved.encode('utf-8'))