import time
import pandas as pd
import unittest

# import ner_coref module
import sys
sys.path.append("../")
from src.modelling.ner_coref import NERCoref


class NERCorefTest(unittest.TestCase):
    """All test cases for the NERCoref class."""
    
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv("relation_support_Keller_updated.csv")
        cls.times = dict()
        t1 = time.time()
        cls.resolver = NERCoref()
        t2 = time.time()
        cls.times["NERCoref initialisation time"] = t2 - t1
    
    
    def testDetokenization(self):
        """Test that the implemented BERT detokenizer NERCoref._bert_detokenize  is the inverse of BERT Tokenizer."""
        # _get_space_map
        # _tokenize
        # _bert_detokenize
        sents = list(self.__class__.data['sentence'].unique())
        
        # tokenise
        toks = [self.__class__.resolver.tokenizer.tokenize(s) for s in sents]
        # detokenise
        spaces = [self.__class__.resolver._get_space_map(s, t) for s, t in zip(sents, toks)]
        detoks = [self.__class__.resolver._bert_detokenize(t, sp[1:-1]) for t, sp in zip(toks, spaces)]
        
        # test
        self.assertListEqual(sents, detoks)

        
    def testSentResolve(self):
        """Test that the number of sentences resolved must be same as the sentences given using NERCoref.sent_resolve."""
        sents = list(self.__class__.data['sentence'].unique())
        t1 = time.time()
        resolved = self.__class__.resolver.sent_resolve(sents)
        t2 = time.time()

        # test number of resolved sentences must be same as number of given sentences
        self.assertTrue(len(resolved) == len(sents))
        self.__class__.times["avg. sent resolve time"] = (t2 - t1)/len(sents)
    
    
    def testParaResolve(self):
        """Test that the number of sentences resolved must be same as the sentences given using NERCoref.para_resolve."""
        with open("article.txt", encoding="utf-8") as f:
            paras = f.readlines()
        
        t1 = time.time()
        resolved = self.resolver.para_resolve(paras)
        t2 = time.time()
        
        # test number of resolved sentences must be same as number of given sentences
        self.assertTrue(len(resolved) == len(paras))
        self.__class__.times["avg. para resolve time"] = (t2 - t1)/len(paras)
   

    def testGetEntities(self):
        """All entitites extracted must be present in the entities list of given test sentences."""
        sents = list(self.__class__.data['sentence'])
        heads = list(self.__class__.data['head'])
        tails = list(self.__class__.data['tail'])
        
        t1 = time.time()
        ents = self.__class__.resolver.get_entities(sents)
        t2 = time.time()
        
        head_asserts = list()
        tail_asserts = list()
        for idx, ent_list in ents.items():
            head_asserts += [any([e[0] in heads[idx] for e in ent_list])]
            tail_asserts += [any([e[0] in tails[idx] for e in ent_list])]

        # test
        self.assertTrue(all(head_asserts))
        self.assertTrue(all(tail_asserts))
        
        self.__class__.times["avg. entity extraction time"] = (t2 - t1) / len(sents)
   
    
    def testGenerateQueries(self):
        """All queries extracted must be present in the query list of given test sentences."""
        sents = list(self.__class__.data['sentence'])
        heads = list(self.__class__.data['head'])
        tails = list(self.__class__.data['tail'])
        pairs = list(zip(heads, tails))
        
        t1 = time.time()
        queries = self.__class__.resolver.generate_queries('\n'.join(sents))
        t2 = time.time()
        
        pred_pairs = list(zip(queries['head'], queries['tail']))
        
        query_asserts = list()
        for e1, e2 in pairs:
            e1 = " ".join(e1.split('. ')[1:]) if any([m in e1 for m in ('Mr.', 'Mrs.')]) else e1
            e2 = " ".join(e2.split('. ')[1:]) if any([m in e2 for m in ('Mr.', 'Mrs.')]) else e2
            query_asserts += [(e1, e2) in pred_pairs or (e2, e1) in pred_pairs]

        self.assertTrue(all(query_asserts))

        self.__class__.times["avg. query generation time"] = (t2 - t1) / len(sents)

    
    @classmethod
    def tearDownClass(cls):
        """Print a report all the runtimes for implementations in the NERCoref."""
        [print(f"{k}: {v}") for k, v in cls.times.items()]
        