import unittest
import pandas as pd

import sys
sys.path.append("../")
from src.modelling.sentiment import *


class SentimentTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv("relation_support_Keller_updated.csv")
        cls.sentiment = TargetSentiment()
        
    
    def testCountSpacePunct(self):
        """Test the helper function that counts number of spaces and punctuations in a given string."""
        real_counts = [42, 53, 31, 19, 8, 17, 33, 22, 42, 9, 18, 28, 9, 16, 9, 
                       38, 29, 19, 35, 22, 10, 20, 21, 29, 20, 52, 12]
        
        counts = [self.__class__.sentiment._count_space_punct(s) for s in self.__class__.data.sentence]
        self.assertListEqual(real_counts, counts)
    
    
    def testGetSubtext(self):
        """Test the helper function that obtains the subtext between entity mentions for targeted sentiment."""
        subtexts = list()
        for i, row in self.__class__.data[['sentence', 'head', 'tail']].iterrows():
            subtexts += [self.__class__.sentiment._get_subtext(row['sentence'], row['head'], row['tail'])]
            
        # test
        assert_subtexts = [row['head'] in subtexts[i] and row['tail'] in subtexts[i] 
                           for i, row in self.__class__.data[['head', 'tail']].iterrows()]
        
        self.assertTrue(all(assert_subtexts))
    
    
    def testPredict(self):
        """Test the sentiment prediction function generates the output correctly."""
        # test on labels only
        predictions = list()
        for i, row in self.__class__.data[['sentence', 'head', 'tail']].iterrows():
            predictions += [self.__class__.sentiment.predict(row['sentence'], row['head'], row['tail'])]
        
        assert_preds = [p in ('POSITIVE', 'NEUTRAL', 'NEGATIVE') for p in predictions]
        self.assertTrue(all(assert_preds))
        
        # test on return_dict
        predictions = list()
        for i, row in self.__class__.data[['sentence', 'head', 'tail']].iterrows():
            predictions += [self.__class__.sentiment.predict(row['sentence'], row['head'], row['tail'], return_dict=True)]
        
        assert_preds = [{'subtext', 'head', 'tail', 'label', 'score'} == set(p.keys()) for p in predictions]
        self.assertTrue(all(assert_preds))
        
         
    