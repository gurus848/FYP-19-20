"""
    Test cases for the BERT detokenization.
"""
import codecs
from string import punctuation
import sys
sys.path.append("../")
from models.coref.bert import tokenization

# from src.modelling.ner_coref import NERCoref

#resolver = NERCoref()


# class TestTokenizer(unittest.TestCase):
#     def setUp(self):
#         """
#             Instantiate coref resolver.
#         """
#         print('here')
#         self.resolver = NERCoref()
        
        
#     def detokenizeTest1(self):
#         """Punctuation around numbers."""

#         text = "On Capitol Hill, Republicans presented a bill that would offer bridge loans of up to $10 million each to small businesses, extend hundreds of billions of dollars in loans to large corporations in distressed industries and send checks as large as $1,200 per adult to individuals earning less than $99,000 per year. The payments would phase in for earners up to $75,000 — meaning lower earners would get smaller checks — and then phase out again at $99,000."

#         tokenized = self.resolver.tokenizer.tokenize(text)
#         detokenized = self.resolver._bert_detokenize(tokenized)
#         self.assertTrue(text == detokenized)
   
    
#     def detokenizeTest2(self):
#         """Punctuation around numbers and money."""
        
#         text = "WASHINGTON — The White House and lawmakers scrambled on Thursday to flesh out details of a $1 trillion economic stabilization plan to help workers and businesses weather a potentially deep recession, negotiating over the size and scope of direct payments to millions of people and aid for companies facing devastation in the coronavirus pandemic."
        
#         tokenized = self.resolver.tokenizer.tokenize(text)
#         detokenized = self.resolver._bert_detokenize(tokenized)
#         self.assertTrue(text == detokenized)    

tokenizer = tokenization.FullTokenizer(
    vocab_file = "../models/bert_large/vocab.txt", do_lower_case=False)

def get_space_map(tokens, text):
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
    
    return spaces
            


def detokenizeTest():
    with codecs.open("../../temp.txt", encoding='utf-8') as f:
        text = f.readlines()
        
   
    text = " ".join(list(map(lambda x: x.strip('\n'), text)))
    sys.stdout.buffer.write(text.encode('utf-8'))
    print('==========================================================')
    tokenized = resolver.tokenizer.tokenize(text)
    detokenized = resolver._bert_detokenize(tokenized)
    sys.stdout.buffer.write(detokenized.encode('utf-8'))
    

if __name__ == "__main__":
    text = "On Capitol Hill, Republicans presented a bill that would offer bridge loans of up to $10 million each to small businesses, extend hundreds of billions of dollars in loans to large corporations in distressed industries and send checks as large as $1,200 per adult to individuals earning less than $99,000 per year."
    tokens = tokenizer.tokenize(text)
    print(get_space_map(tokens, text))
    