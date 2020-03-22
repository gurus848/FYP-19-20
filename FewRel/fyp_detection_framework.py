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

class DataLoader:
    """
        Used to load data, such as the relation support dataset. Loads the data in the current format
    """

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
                if tokens[i] == tokenized_tail[0] and tokens[i:i+len(tokenized_tail)] == tokenized_tail:
                    tail_indices = list(range(i,i+len(tokenized_tail)))
                    break
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
            queries.append({'sentence':row['sentence']})
        
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
            queries.append({'sentence':row['sentence'], 'head':row['head'], 'tail':row['tail']})
        
        return queries
    
        
    
class DetectionFramework:
    """
        Runs the detection model/algorithm on queries in different ways.
    """
    def __init__(self, ckpt_path):
        """
        Initializer
        """
        
        self.support = []   #stores the list of relation support examples which have been loaded
        self.detector = Detector(chpt_path=ckpt_path)   #the detector/model
        self.queries = []
        self.ckpt_path = ckpt_path
        self.ner_coref = None
    
    def _add_support(self, support):
        """
            Adds relation support examples which have been loaded to this detection framework. Augments the existing data if necessary. 
        """
        if len(self.support) == 0:
            self.support = support
            return
        
        to_add = []
        for support_i in support:
            found = False
            for support_j in self.support:
                if support_i['name'] == support_j['name']:
                    support_j['examples'].extend(support_i['examples'])
                    found = True
                    break
                    
            if not found:
                to_add.append(support_i)
        self.support.extend(to_add)
        
    def clear_support_queries(self):
        """
            Clears any support or queries that have already been loaded.
        """
        self.support = []
        self.queries = []
    
    def load_support(self, path):
        """
        Loads the relation support data which is mentioned.
        """
        self._add_support(DataLoader.load_relation_support_csv(path))
        
    def load_queries_csv(self, path):
        """
        Loads the queries which are contained at the passed path. 
        Detects if the head and tail are specified. If so, these are loaded using a special function.
        """
        df = pd.read_csv(path, engine='python')
        if "head" in df.columns:
            self._load_queries_predefined_head_tail_csv(path)
        else:
            self.queries = DataLoader.load_query_csv(path)
            
    def load_url(self, url):
        """
            Loads a URL.
        """
        title = read_news_article.process_online_articles([url])[0]
        proj_path = os.path.abspath(os.path.dirname(__file__)).split("fyp_detection_framework.py")[0]
        df = pd.read_csv("{}/nlp_code/data/extracted_article_data.csv".format(proj_path))
        text = df[df['title'] == title].iloc[0]['text']
        if self.ner_coref is None:
            self.ner_coref = NERCoref()
        results = self.ner_coref.generate_queries(text)
        self.queries = []
        for i in range(len(results['sentence'])):
            self.queries.append({'sentence':results['sentence'][i], 'head':results['head'][i], 'tail':results['tail'][i]})
        
    def load_text_file(self, path):
        """
            Loads from a file.
        """
        text = open(path).read()
        if self.ner_coref is None:
            self.ner_coref = NERCoref()
        results = self.ner_coref.generate_queries(text)
        self.queries = []
        for i in range(len(results['sentence'])):
            self.queries.append({'sentence':results['sentence'][i], 'head':results['head'][i], 'tail':results['tail'][i]})
        
    def load_ind_sentence(self, text):
        """
            Loads an individual sentence.
        """
        if self.ner_coref is None:
            self.ner_coref = NERCoref()
        results = self.ner_coref.generate_queries(text)
        self.queries = []
        for i in range(len(results['sentence'])):
            self.queries.append({'sentence':results['sentence'][i], 'head':results['head'][i], 'tail':results['tail'][i]})
        
    def _load_queries_predefined_head_tail_csv(self, path):
        """
        Loads the queries which are contained at the passed path, these queries are supposed to have the head and tail to use defined. 
        """
        self.queries = DataLoader.load_query_with_head_tail_csv(path)
        
    
    def _calculate_conf(self, logits, order, pred):
        exp = list(float(i) for i in logits[0][0])
        exp = [math.exp(i) for i in exp]
        if pred == 'NA':
            return exp[-1]*100/sum(exp)
        return exp[order.index(pred)]*100/sum(exp)
    
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
        
        for q in self.queries:
            if cancel_flag[0]:
                break
            
            # for some reason the python combinations function returns the head the tail consistently backwards
            sentence = q['sentence']
            if 'head' not in q:
                #head and tail are not predefined, so NER is used to find the potential heads and tails
                for tail, head in self.detector.get_head_tail_pairs(q['sentence']):    #iterating through all possible head and tail pairs
                    q['head'] = head
                    q['tail'] = tail
                    result = self.detector.run_detection_algorithm(q, self.support)
                    self.detector.print_result(*(result[:-1]))

                        
                    #TODO: fix sentiment analyses
                    result.append('TODO')
                    order = list(r['name'] for r in self.support)
                    result.append(int(self._calculate_conf(result[-2], order, result[3])))
                    results.append(result)

                    tail, head = head, tail   #for testing

                    q['head'] = head
                    q['tail'] = tail
                    result = self.detector.run_detection_algorithm(q, self.support)
                    self.detector.print_result(*(result[:-1]))
                        
                    #TODO: fix sentiment analyses
                    result.append('TODO')
                    order = list(r['name'] for r in self.support)
                    result.append(int(self._calculate_conf(result[-2], order, result[3])))
                    results.append(result)
                    if rt_results is not None:
                        rt_results.append(result)
            else:
                #the head and tail are predefined in the query, so just those are used.
                
                result = self.detector.run_detection_algorithm(q, self.support)
                self.detector.print_result(*(result[:-1]))
                   
                #TODO: fix sentiment analyses
                result.append('TODO')
                order = list(r['name'] for r in self.support)
                result.append(int(self._calculate_conf(result[-2], order, result[3])))
                results.append(result)
                if rt_results is not None:
                    rt_results.append(result)

        return results