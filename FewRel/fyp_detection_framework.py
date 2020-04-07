import spacy
import pandas as pd
from fyp_detection_functions import Detector
from textblob import TextBlob
import math
import os
import sys
from nlp_code import read_news_article
proj_path = os.path.abspath(os.path.dirname(__file__)).split("FewRel")[0]
sys.path.insert(1, proj_path + 'src/modelling/')
from ner_coref import NERCoref
from unidecode import unidecode
from sentiment import TargetSentiment
import gc

class DataLoader:
    """
        Used to load data, such as the relation support dataset. Loads the data in the current format
    """
    
    @staticmethod
    def _get_indices_alt(tokens, tokenized_head, tokenized_tail):
        """
            Alternative implemention for getting the indices of the head and tail if exact matches cannot be done.
        """
        head_indices = None
        tail_indices = None
        print(tokens, tokenized_head, tokenized_tail)
        for i in range(len(tokens)):
            if tokens[i] in tokenized_head[0]:
                broke = False
                for k, j in zip(tokens[i:i+len(tokenized_head)], tokenized_head):
                    if k not in j:
                        broke = True
                        break
                if not broke:
                    head_indices = list(range(i,i+len(tokenized_head)))
                    break
        for i in range(len(tokens)):
            if head_indices is not None and i in head_indices:
                continue
            if tokens[i] in tokenized_tail[0]:
                broke = False
                for k, j in zip(tokens[i:i+len(tokenized_tail)], tokenized_tail):
                    if k not in j:
                        broke = True
                        break
                if not broke:
                    tail_indices = list(range(i,i+len(tokenized_tail)))
                    break
        return head_indices, tail_indices
    
    @staticmethod
    def check_loaded_relation_support_dataframe(df):
        """
            Checks that the head and tail which are mentioned are actually present in the sentence.
            If there is a problem then value error is raised.
        """
        
        nlp = spacy.load("en_core_web_sm")    #no coref being done here, the assumption is that no coref will be done on the support/training data, only on test data.

        def spacy_tokenize(sentence):
            doc = nlp(sentence)
            return list(map(str, doc))
        
        if 'reldescription' in df.columns:  #because the function is also used to check that a queries dataset with head/tail is correct
            rels = df['reldescription'].unique().tolist()
            count = df[df['reldescription'] == rels[0]].shape[0]
            for r in rels[1:]:
                if count != df[df['reldescription'] == r].shape[0]:
                    raise ValueError("Error the number of examples used for each relation must be the same!")
        
        for _, row in df.iterrows():
            head = row['head']
            tail = row['tail']
            sentence = row['sentence']

            tokens = spacy_tokenize(sentence)

            tokenized_head = spacy_tokenize(head)
            tokenized_tail = spacy_tokenize(tail)

            head_indices = None
            tail_indices = None
            for i in range(len(tokens)):
                if tokens[i] == tokenized_head[0] and tokens[i:i+len(tokenized_head)] == tokenized_head:
                    head_indices = list(range(i,i+len(tokenized_head)))
                    break
            for i in range(len(tokens)):
                if head_indices is not None and i in head_indices:
                    continue
                if tokens[i] == tokenized_tail[0] and tokens[i:i+len(tokenized_tail)] == tokenized_tail:
                    tail_indices = list(range(i,i+len(tokenized_tail)))
                    break
            
            if head_indices is None or tail_indices is None:
                head_indices, tail_indices = DataLoader._get_indices_alt(tokens, tokenized_head, tokenized_tail)
                
            if head_indices is None or tail_indices is None:
                error_string = ""
                error_string += ("Problem sentence: {}\n".format(sentence))
                error_string += ("Problem sentence head: {}\n".format(head))
                error_string += ("Problem sentence tail: {}\n".format(tail))
                raise ValueError(error_string)
    
    @staticmethod
    def load_relation_support_csv_dataframe(filepath):
        """
            Loads the mentioed csv into a pandas dataframe and checks that it is valid. Returns the dataframe.
            
            The format should be correct: csv should contain 'sentence', 'head', 'tail' and 'reldescription' columns. More could be added later.
        """
        df = pd.read_csv(filepath, engine='python')
        try:
            DataLoader.check_loaded_relation_support_dataframe(df)
        except ValueError as e:
            raise ValueError("In the provided relation support dataset at least one of the heads and tails doesn't match the provided sentence. Please correct the dataset and try again. The spelling and capitalization should match exactly. \n {}".format(str(e)))
        return df
    
    @staticmethod
    def load_relation_support_csv(filepath):
        """
            Loads the mentioned csv and returns it in the correct json format.
            
            filepath - the path to the csv file to load
        """

        df = DataLoader.load_relation_support_csv_dataframe(filepath)
        support_relation_info = []
        for rel_type in df['reldescription'].unique().tolist():
            dft = df[df['reldescription'] == rel_type].copy()
            
            info = {
                'name':rel_type,
                'examples':[]
            }
            for _, row in dft.iterrows():
                example_info = {
                    'sentence':row['sentence'],
                    'head':row['head'],
                    'tail':row['tail']
                }
                info['examples'].append(example_info)
            support_relation_info.append(info)
        return support_relation_info
    
    @staticmethod
    def load_query_csv(filepath):
        """
            Loads the passed filepath into a pandas dataframe, then modifies the data into the json format and returns it.
            The file is assumed to be a csv with a column with the heading 'sentence'
        """
        queries = []
        df = pd.read_csv(filepath, engine='python')
        for _, row in df.iterrows():
            queries.append({'sentence':unidecode(row['sentence'])})
        
        return queries
    
    @staticmethod
    def load_query_with_head_tail_csv(filepath):
        """
            Loads the passed filepath into a pandas dataframe, then modifies the data into the json format and returns it.
            The file is assumed to be a csv with a column with the headings 'sentence', 'head' and 'tail'.
        """
        queries = []
        df = pd.read_csv(filepath, engine='python')
        try:
            DataLoader.check_loaded_relation_support_dataframe(df)
        except ValueError as e:
            raise ValueError("In the provided query dataset at least one of the heads and tails doesn't match the provided sentence. Please correct the dataset and try again. The spelling and capitalization should match exactly. \n {}".format(str(e)))
        
        for _, row in df.iterrows():
            queries.append({'sentence':unidecode(row['sentence']), 'head':unidecode(row['head']), 'tail':unidecode(row['tail'])})
        
        return queries
    
        
    
class DetectionFramework:
    """
        Runs the detection model/algorithm on queries in different ways.
    """
    def __init__(self, ckpt_path):
        """
        Initializer
        """
        
        self.support = []   #stores the list of relation support examples which have been loaded. multiple datasets can be used, each dataset is a separate list.
        self.detector = Detector(chpt_path=ckpt_path)   #the detector/model
        self.queries = []
        self.ckpt_path = ckpt_path
        self.ner_coref = None
        self.sentiment = TargetSentiment()
    
        
    def clear_support_queries(self):
        """
            Clears any support or queries that have already been loaded.
        """
        self.support = []
        self.queries = []
    
    def load_support_files(self, path, username):
        """
        Loads the relation support data which is mentioned.
        """
        self.support = []
        for f in [i for i in os.listdir(path) if 'csv' in i and username in i]:
            self.support.append(DataLoader.load_relation_support_csv("{}/{}".format(path, f)))
        
    def load_queries_csv(self, path):
        """
        Loads the queries which are contained at the passed path. 
        Detects if the head and tail are specified. If so, these are loaded using a special function.
        """
        df = pd.read_csv(path, engine='python')
        if "head" in df.columns:
            self._load_queries_predefined_head_tail_csv(path)
        else:
            q = DataLoader.load_query_csv(path)
            text = "\n".join([i['sentence'] for i in q])
            if self.ner_coref is None:
                self.ner_coref = NERCoref()
            results = self.ner_coref.generate_queries(text)
            self.queries = []
            for i in range(len(results['sentence'])):
                self.queries.append({'sentence':results['sentence'][i], 'head':results['head'][i], 'tail':results['tail'][i]})
            
    def load_url(self, url):
        """
            Loads a URL.
        """
        title = read_news_article.process_online_articles([url])[0]
        proj_path = os.path.abspath(os.path.dirname(__file__)).split("fyp_detection_framework.py")[0]
        df = pd.read_csv("{}/nlp_code/data/extracted_article_data.csv".format(proj_path))
        text = df[df['title'] == title].iloc[0]['text']
        text = unidecode(text)
        if self.ner_coref is None:
            self.ner_coref = NERCoref()
        results = self.ner_coref.generate_queries(text)
        self.queries = []
        for i in range(len(results['sentence'])):
            self.queries.append({'sentence':results['sentence'][i], 'head':results['head'][i], 'tail':results['tail'][i]})
        
    def load_text_files(self, path):
        """
            Loads queries from text files.
        """
        fs = [i for i in os.listdir(path) if 'txt' in i]
        if self.ner_coref is None:
            self.ner_coref = NERCoref()
        self.queries = []
        for f in fs:
            text = open("{}/{}".format(path, f)).read()
            text = unidecode(text)
            results = self.ner_coref.generate_queries(text)
            for i in range(len(results['sentence'])):
                self.queries.append({'sentence':results['sentence'][i], 'head':results['head'][i], 'tail':results['tail'][i]})
        
    def load_ind_sentence(self, text):
        """
            Loads an individual sentence as a query.
        """
        if self.ner_coref is None:
            self.ner_coref = NERCoref()
        text = unidecode(text)
        results = self.ner_coref.generate_queries(text)
        self.queries = []
        print(len(results['sentence']), len(results['head']), len(results['tail']))
        for i in range(len(results['sentence'])):
            self.queries.append({'sentence':results['sentence'][i], 'head':results['head'][i], 'tail':results['tail'][i]})
            
    def load_html_file_queries(self, folder_path):
        """
            Loads multiple html files which have been uploaded for analysis.
        """
        if self.ner_coref is None:
            self.ner_coref = NERCoref()
        titles = read_news_article.process_file_articles([i for i in os.listdir(folder_path) if 'html' in i])
        df = pd.read_csv("{}/nlp_code/data/extracted_article_data.csv".format(proj_path))
        self.queries = []
        for t in titles:
            text = df[df['title'] == title].iloc[0]['text']
            text = unidecode(text)
            results = self.ner_coref.generate_queries(text)
            for i in range(len(results['sentence'])):
                self.queries.append({'sentence':results['sentence'][i], 'head':results['head'][i], 'tail':results['tail'][i]})
        
    def _load_queries_predefined_head_tail_csv(self, path):
        """
        Loads the queries which are contained at the passed path, these queries are supposed to have the head and tail to use defined. 
        """
        self.queries = DataLoader.load_query_with_head_tail_csv(path)
        
    
    
    
    def detect(self, rt_results=None, cancel_flag=[False]):
        """
            Runs the detection algorithm for the particular queries
            
            queries - the set of queries to run the algorithm on
            rt_results - real time results list - if specified, then the analysis results will be added to this list as they are evaluated.
            cancel_flag - set the index 0 element to True if you want the analysis to be cancelled.
        """
        if len(self.support) == 0:
            raise ValueError("No relation support has been added!")
            
        if len(self.queries) == 0:
            raise ValueError("No queries have been added!")
            
        results = []
        
        for i, sup in enumerate(self.support):   #iterate through the support datasets
            for q in self.queries:  #iterate through the possible queries
                if cancel_flag[0]:   #if the user has said that it should be cancelled, then cancel it
                    break

                #the head and tail are predefined in the query, so just those are used.

                result = self.detector.run_detection_algorithm(q, sup)
                self.detector.print_result(result['sentence'], result['head'], result['tail'], result['pred_relation'])

                sent_pred = self.sentiment.predict(q['sentence'], q['head'], q['tail'])
                result['sent'] = sent_pred
                result['rel_sup_ind'] = (i+1)  #the index of the relation support dataset which is used
                results.append(result)
                if rt_results is not None:
                    rt_results.append(result)
                gc.collect()

        return results