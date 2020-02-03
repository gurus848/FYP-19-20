import spacy
import pandas as pd
import random
from fyp_detection_functions import Detector

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
                print("Problem sentence: {}".format(sentence))
                print("Problem sentence head: {}".format(head))
                print("Problem sentence tail: {}".format(tail))
                raise ValueError
    
    @staticmethod
    def load_relation_support_csv_dataframe(filepath):
        """
            Loads the mentioed csv into a pandas dataframe and checks that it is valid. Returns the dataframe.
            
            The format should be correct: csv should contain 'sentence', 'head', 'tail' and 'reldescription' columns. More could be added later.
        """
        df = pd.read_csv(filepath)
        try:
            DataLoader.check_loaded_relation_support_dataframe(df)
        except ValuError:
            raise ValueError("In the mentioned dataset {} at least one of the heads and tails doesn't match the provided sentence. Please correct the dataset and try again. The spelling and capitalization should match exactly.".format(filepath))
        return df
    
    @staticmethod
    def load_relation_support_csv(filepath, K=3,random_seed=2020, min_instance=3):
        """
            Loads the mentioned csv and returns it in the correct json format.
            
            filepath - the path to the csv file to load
            K - the number of examples per relation to use. if there are less than this number of examples for that relation then some examples will be repeated to get up to K
            random_seed - the random seed for the random number generator
            min_instance - if there are less than min_instance examples for a relation in the dataset, then that relation will not be considered
        """
        random.seed(random_seed)
        df = DataLoader.load_relation_support_csv_dataframe(filepath)
        counts = df['reldescription'].value_counts()
        counts = counts[counts >= min_instance]
        df = df[df['reldescription'].isin(counts.index)].copy().reset_index(drop=True)
        support_relation_info = []
        for rel_type in counts.index.tolist():
            dft = df[df['reldescription'] == rel_type].copy()
            random_sample = dft.sample(min(K, dft.shape[0]), replace=False, random_state=random_seed)  
            while random_sample.shape[0] < K:
                new_sample = dft.sample(min(K - random_sample.shape[0], dft.shape[0]), replace=False, random_state=random_seed)  
                random_sample = pd.concat([random_sample, new_sample])
            
            info = {
                'name':rel_type,
                'examples':[]
            }
            for _, row in random_sample.iterrows():
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
        df = pd.read_csv(filepath)
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
        df = pd.read_csv(filepath)
        for _, row in df.iterrows():
            queries.append({'sentence':row['sentence'], 'head':row['head'], 'tail':row['tail']})
        
        return queries
    
        
    
class DetectionFramework:
    """
        Runs the detection model/algorithm on queries in different ways.
    """
    def __init__(self, ckpt_path="checkpoint/pair-bert-train_wiki-val_wiki-5-1.pth.tar"):
        """
        Initializer
        """
        
        self.support = []   #stores the list of relation support examples which have been loaded
        self.detector = Detector(chpt_path=ckpt_path)   #the detector/model
        self.queries = []
    
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
        
    def load_support(self, path, K=3, min_instance=3):
        """
        Loads the relation support data which is mentioned.
        """
        self._add_support(DataLoader.load_relation_support_csv(path, K=K, min_instance=min_instance))
        
    def load_queries(self, path):
        """
        Loads the queries which are contained at the passed path. 
        """
        self.queries = DataLoader.load_query_csv(path)
        
    def load_queries_predefined_head_tail(self, path):
        """
        Loads the queries which are contained at the passed path, these queries are supposed to have the head and tail to use defined. 
        """
        self.queries = DataLoader.load_query_with_head_tail_csv(path)
    
    def detect(self, N=5):
        """
            Runs the detection algorithm for the particular queries
            
            queries - the set of queries to run the algorithm on
            N - for N-way detection. TODO: To be implemented in the future. 
            
        """
        if len(self.support) == 0:
            raise ValueError("No relation support has been added!")
            
        if len(self.queries) == 0:
            raise ValueError("No queries have been added!")
            
        results = []
        
        for q in self.queries:
            # for some reason the python combinations function returns the head the tail consistently backwards
            if 'head' not in q:
                #head and tail are not predefined, so NER is used to find the potential heads and tails
                for tail, head in self.detector.get_head_tail_pairs(q['sentence']):    #iterating through all possible head and tail pairs
                    q['head'] = head
                    q['tail'] = tail
                    result = self.detector.run_detection_algorithm(q, self.support)
                    self.detector.print_result(*(result[:-1]))
                    results.append(result)

                    tail, head = head, tail   #for testing

                    q['head'] = head
                    q['tail'] = tail
                    result = self.detector.run_detection_algorithm(q, self.support)
                    self.detector.print_result(*(result[:-1]))
                    results.append(result)
            else:
                #the head and tail are predefined in the query, so just those are used.
                
                result = self.detector.run_detection_algorithm(q, self.support)
                self.detector.print_result(*(result[:-1]))
                results.append(result)


        return results