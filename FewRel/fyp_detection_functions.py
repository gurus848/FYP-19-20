from fewshot_re_kit.data_loader import FewRelDatasetPair, get_loader_pair
from fewshot_re_kit.framework import FewShotREFramework
from fewshot_re_kit.sentence_encoder import BERTPAIRSentenceEncoder
from models.pair import Pair
import os
import torch
import spacy
# import neuralcoref
# from itertools import combinations
import gc
import math

class Detector:
    #RUNS USING GPU if available and pytoch has CUDA support
    

    def __init__(self, chpt_path, max_length=128):
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

#         self.nlp_coref = spacy.load("en_core_web_sm")
#         neuralcoref.add_to_pipe(self.nlp_coref)
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
            
#     def spacy_tokenize_coref(self,sentence):
#         """
#             Tokenizes the sentence using spacy
#         """
#         return list(map(str, self.nlp_coref(sentence)))
    
    def spacy_tokenize_no_coref(self,sentence):
        """
            Tokenizes the sentence using spacy
        """
        try:
            return list(map(str, self.nlp_no_coref(sentence)))
        except TypeError as e:
            print("problem sentence: '{}'".format(sentence))
            raise e

#     def get_head_tail_pairs(self,sentence):
#         """
#             Gets pairs of heads and tails of named entities so that relation identification can be done on these.
#         """
#         acceptable_entity_types = ['PERSON', 'NORP', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'LAW', 'LOC', 'FAC']
#         doc = self.nlp_coref(sentence)
#         entity_info = [(X.text, X.label_) for X in doc.ents]
#         entity_info = set(map(lambda x:x[0], filter(lambda x:x[1] in acceptable_entity_types, entity_info)))

#         return combinations(entity_info, 2)
    
    def _get_indices_alt(self, tokens, tokenized_head, tokenized_tail):
        """
            Alternative implemention for getting the indices of the head and tail if exact matches cannot be done.
        """
        head_indices = None
        tail_indices = None
        for i in range(len(tokens)):
            if tokens[i] in tokenized_head[0] or tokenized_head[0] in tokens[i]:
                broke = False
                for k, j in zip(tokens[i:i+len(tokenized_head)], tokenized_head):
                    if k not in j and j not in k:
                        broke = True
                        break
                if not broke:
                    head_indices = list(range(i,i+len(tokenized_head)))
                    break
        for i in range(len(tokens)):
            if tokens[i] in tokenized_tail[0] or tokenized_tail[0] in tokens[i]:
                broke = False
                for k, j in zip(tokens[i:i+len(tokenized_tail)], tokenized_tail):
                    if k not in j and j not in k:
                        broke = True
                        break
                if not broke:
                    tail_indices = list(range(i,i+len(tokenized_tail)))
                    break
        return head_indices, tail_indices
    
    def _calculate_conf(self, logits, order, pred):
        exp = list(float(i) for i in logits[0][0])
        exp = [math.exp(i) for i in exp]
        if pred == 'NA':
            return exp[-1]*100/sum(exp)
        return exp[order.index(pred)]*100/sum(exp)
    
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
        tokens = self.spacy_tokenize_no_coref(query['sentence'])
        
        print("head: '{}' tail: '{}' sentence: '{}'".format(head, tail, query['sentence']))
        
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
            head_indices, tail_indices = self._get_indices_alt(tokens, tokenized_head, tokenized_tail)
            
        if head_indices is None or tail_indices is None:
            print(tokenized_head)
            print(tokenized_tail)
            print(tokens)
            raise ValueError("Head/Tail indices error: head: {} \n tail: {} \n sentence: {}".format(head, tail, query['sentence']))
        
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
                    raise ValueError("Head/Tail indices error: head: {} \n tail: {} \n sentence: {}".format(ex['head'], ex['tail'], ex['sentence']))
                
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
        gc.collect()
        order = list(r['name'] for r in relation_data)
        pred_relation = relation_data[pred.item()]['name'] if pred.item() < len(relation_data) else 'NA'
        return {'sentence': query['sentence'], 'head': head, 'tail': tail, 'pred_relation': pred_relation, 'conf': int(self._calculate_conf(logits, order, pred_relation))}  #returns (sentence, head, tail, prediction relation name)
        
    def print_result(self,sentence, head, tail, prediction):
        """
            Helper function to print the results to the stdout.
        """
        print('Sentence: \"{}\", head: \"{}\", tail: \"{}\", prediction: {}'.format(sentence, head, tail, prediction))
        
