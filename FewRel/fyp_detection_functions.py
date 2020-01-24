from fewshot_re_kit.data_loader import FewRelDatasetPair, get_loader_pair
from fewshot_re_kit.framework import FewShotREFramework
from fewshot_re_kit.sentence_encoder import BERTPAIRSentenceEncoder
from models.pair import Pair
import os
import torch
import spacy
import neuralcoref
from itertools import combinations

class Detector:
    #RUNS USING GPU if available
    
    #sample relation data. this format should be followed for both queries and example relations (support)
    example_relation_data = [
        {'name':'love',
        'examples':[
            {'sentence':'Meow loves Mo', 'head':'Meow', 'tail':'Mo'},
            {'sentence':'Tom is in love with Jull', 'head':'Tom', 'tail':'Jull'}
        ]},
        {'name':'hate',
        'examples':[
            {'sentence':'Trump hates the Mooch', 'head':'Trump', 'tail':'Mooch'},
            {'sentence':'Ivanka and Jared dislike each other intensely', 'head':'Ivanka', 'tail':'Jared'}
        ]},
        {'name':'spouse',
        'examples':[
            {'sentence':'Trump is married to Ivanka', 'head':'Trump', 'tail':'Ivanka'},
            {'sentence':"Bill went out with his wife Jill on saturday", 'head':'Bill', 'tail':'Jill'}
        ]},
            {'name':'insult',
        'examples':[
            {'sentence':'The President said that Michael Cohen is a rat', 'head':'The President', 'tail':'Michael'},
            {'sentence':'Meow and Tom threw jabs at each other', 'head':'Meow', 'tail':'Tom'}
        ]},
            {'name':'capital',
        'examples':[
            {'sentence':'Austin is the capital of Texas', 'head':'Austin', 'tail':'Texas'},
            {'sentence':"the capital of China is located in Beijing", 'head':'Beijing', 'tail':"China"}
        ]}

    ]

    queries = [{
        'sentence':'Cohen and Fluffy are very loving to each other','head':'Cohen','tail':'Fluffy'
    },
    {
        'sentence':"""The US's capital is Washington""",'head':'Washington','tail':'US'
    }]

    def __init__(self, chpt_path="checkpoint/pair-bert-train_wiki-val_wiki-5-1.pth.tar", max_length=128):
        """
            Initializer
        """
        self.checkpoint_path = chpt_path
        self.bert_pretrained_checkpoint = 'bert-base-uncased'
        self.max_length = max_length
        self.sentence_encoder = BERTPAIRSentenceEncoder(
                    self.bert_pretrained_checkpoint,
                    self.max_length)

        self.model = Pair(self.sentence_encoder, hidden_size=768)
        if torch.cuda.is_available():
            self.model = self.model.cuda()
        self.model.eval()

        self.nlp_coref = spacy.load("en_core_web_sm")
        neuralcoref.add_to_pipe(self.nlp_coref)
        self.nlp_no_coref = spacy.load("en_core_web_sm")
        self.load_model()
        
    def __load_model_from_checkpoint__(self,ckpt):
        '''
        ckpt: Path of the checkpoint
        return: Checkpoint dict
        '''
        if os.path.isfile(ckpt):
            checkpoint = torch.load(ckpt)
            print("Successfully loaded checkpoint '%s'" % ckpt)
            return checkpoint
        else:
            raise Exception("No checkpoint found at '%s'" % ckpt)


    def bert_tokenize(self,tokens, head_indices, tail_indices):
        word = self.sentence_encoder.tokenize(tokens,
                head_indices,
                tail_indices)
        return word
    
    def load_model(self):
        """
            Loads the model from the checkpoint
        """
        state_dict = self.__load_model_from_checkpoint__(self.checkpoint_path)['state_dict']
        own_state = self.model.state_dict()
        for name, param in state_dict.items():
            if name not in own_state:
                continue
            own_state[name].copy_(param)
            
    def spacy_tokenize_coref(self,sentence):
        """
            Tokenizes the sentence using spacy
        """
        return list(map(str, self.nlp_coref(sentence)))
    
    def spacy_tokenize_no_coref(self,sentence):
        """
            Tokenizes the sentence using spacy
        """
        return list(map(str, self.nlp_no_coref(sentence)))

    def get_head_tail_pairs(self,sentence):
        """
            Gets pairs of heads and tails of named entities so that relation identification can be done on these.
        """
        acceptable_entity_types = ['PERSON', 'NORP', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'LAW', 'LOC', 'FAC']
        doc = self.nlp_coref(sentence)
        entity_info = [(X.text, X.label_) for X in doc.ents]
        entity_info = set(map(lambda x:x[0], filter(lambda x:x[1] in acceptable_entity_types, entity_info)))

        return combinations(entity_info, 2)
    
    def run_detection_algorithm(self, query, relation_data):
        """
            Runs the algorithm/model on the given query using the given support data.
        """
        N = len(relation_data)
        K = len(relation_data[0]['examples'])
        Q = 1
        head = query['head']
        tail = query['tail']
        fusion_set = {'word': [], 'mask': [], 'seg': []}
        tokens = self.spacy_tokenize_coref(query['sentence'])
        
        tokenized_head = self.spacy_tokenize_no_coref(head)
        tokenized_tail = self.spacy_tokenize_no_coref(tail)
        
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
            raise ValueError
        
        bert_query_tokens = self.bert_tokenize(tokens, head_indices, tail_indices)
        for relation in relation_data:
            for ex in relation['examples']:
                tokens = self.spacy_tokenize_no_coref(ex['sentence'])
                tokenized_head = self.spacy_tokenize_no_coref(ex['head'])  #head and tail spelling and punctuation should match the corefered output exactly
                tokenized_tail = self.spacy_tokenize_no_coref(ex['tail'])
                
                
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
                    raise ValueError
                
                bert_relation_example_tokens = self.bert_tokenize(tokens, head_indices, tail_indices)

                SEP = self.sentence_encoder.tokenizer.convert_tokens_to_ids(['[SEP]'])
                CLS = self.sentence_encoder.tokenizer.convert_tokens_to_ids(['[CLS]'])
                word_tensor = torch.zeros((self.max_length)).long()

                new_word = CLS + bert_relation_example_tokens + SEP + bert_query_tokens + SEP
                for i in range(min(self.max_length, len(new_word))):
                    word_tensor[i] = new_word[i]
                mask_tensor = torch.zeros((self.max_length)).long()
                mask_tensor[:min(self.max_length, len(new_word))] = 1
                seg_tensor = torch.ones((self.max_length)).long()
                seg_tensor[:min(self.max_length, len(bert_relation_example_tokens) + 1)] = 0
                fusion_set['word'].append(word_tensor)
                fusion_set['mask'].append(mask_tensor)
                fusion_set['seg'].append(seg_tensor)

        fusion_set['word'] = torch.stack(fusion_set['word'])
        fusion_set['seg'] = torch.stack(fusion_set['seg'])
        fusion_set['mask'] = torch.stack(fusion_set['mask'])

        if torch.cuda.is_available():
            fusion_set['word'] = fusion_set['word'].cuda()
            fusion_set['seg'] = fusion_set['seg'].cuda()
            fusion_set['mask'] = fusion_set['mask'].cuda()

        logits, pred = self.model(fusion_set, N, K, Q)
        return (query['sentence'], head, tail, relation_data[pred.item()]['name'] if pred.item() < len(relation_data) else 'NA', logits)  #returns (sentence, head, tail, prediction relation name)
        
    def print_result(self,sentence, head, tail, prediction):
        """
            Helper function to print the results to the stdout.
        """
        print('Sentence: \"{}\", head: \"{}\", tail: \"{}\", prediction: {}'.format(sentence, head, tail, prediction))
        
    
    def run_on_sample_data(self):
        """
            Runs the model on the sample data which is hardcoded in this file.
        """
        for q in self.queries:
            for head, tail in self.get_head_tail_pairs(q['sentence']):  #iterating through all possible combinations of 2 named entities
                q['head'] = head
                q['tail'] = tail
                self.print_result(*(self.run_detection_algorithm(q, self.example_relation_data)[:-1]))
