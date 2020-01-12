from fewshot_re_kit.data_loader import FewRelDatasetPair, get_loader_pair
from fewshot_re_kit.framework import FewShotREFramework
from fewshot_re_kit.sentence_encoder import BERTPAIRSentenceEncoder
from models.pair import Pair
import os
import torch

#RUNS USING GPU

checkpoint_path = "checkpoint/pair-bert-train_wiki-val_wiki-5-1.pth.tar"
bert_pretrained_checkpoint = 'bert-base-uncased'
max_length = 128


sentence_encoder = BERTPAIRSentenceEncoder(
                    bert_pretrained_checkpoint,
                    max_length)

model = Pair(sentence_encoder, hidden_size=768).cuda()

def __load_model__(ckpt):
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

        
def item(x):
    '''
    PyTorch before and after 0.4
    '''
    torch_version = torch.__version__.split('.')
    if int(torch_version[0]) == 0 and int(torch_version[1]) < 4:
        return x[0]
    else:
        return x.item()
    
def tokenize(tokens, head_indices, tail_indices):
    word = sentence_encoder.tokenize(tokens,
            head_indices,
            tail_indices)
    return word

model.eval()
state_dict = __load_model__(checkpoint_path)['state_dict']
own_state = model.state_dict()
for name, param in state_dict.items():
    if name not in own_state:
        continue
    own_state[name].copy_(param)

N = 5
K = 2
Q = 1
na_rate = 0
example_relation_data = [
    {'name':'love',
    'examples':[
        {'sentence':'meow loves mo', 'head':'meow', 'tail':'mo'},
        {'sentence':'tom is in love with jull', 'head':'tom', 'tail':'jull'}
    ]},
    {'name':'hate',
    'examples':[
        {'sentence':'trump hates the mooch', 'head':'trump', 'tail':'mooch'},
        {'sentence':'ivanka and jared dislike each other intensely', 'head':'ivanka', 'tail':'jared'}
    ]},
    {'name':'spouse',
    'examples':[
        {'sentence':'trump is married to ivanka', 'head':'trump', 'tail':'ivanka'},
        {'sentence':"bill went out with his wife jill on saturday", 'head':'bill', 'tail':'jill'}
    ]},
        {'name':'insult',
    'examples':[
        {'sentence':'The president said that michael cohen is a rat', 'head':'president', 'tail':'michael'},
        {'sentence':'meow and tom threw jabs at each other', 'head':'meow', 'tail':'tom'}
    ]},
        {'name':'capital',
    'examples':[
        {'sentence':'austin is the capital of texas', 'head':'austin', 'tail':'texas'},
        {'sentence':"the capital of china is located in beijing", 'head':'beijing', 'tail':"china"}
    ]}
    
]

queries = [{
    'sentence':'furball and fluffy are very loving to each other','head':'furball','tail':'fluffy'
},
{
    'sentence':'washington is the capital of the US','head':'washington','tail':'US'
}]

max_length = 128
for q in queries:
    fusion_set = {'word': [], 'mask': [], 'seg': []}
    tokens = q['sentence'].split(" ")  #TODO: generalize, make it tokenize like in the example wikidata, would probably need to use some nlp library to do it
    head_indices = list(range(tokens.index(q['head']), tokens.index(q['head'])+len(q['head'].split(" "))))   #TODO: make it work with multi-word entities
    tail_indices = list(range(tokens.index(q['tail']), tokens.index(q['tail'])+len(q['tail'].split(" "))))
    bert_query_tokens = tokenize(tokens, head_indices, tail_indices)
    for relation in example_relation_data:
        for ex in relation['examples']:
            tokens = ex['sentence'].split(" ")  #TODO: generalize
            head_indices = list(range(tokens.index(ex['head']), tokens.index(ex['head'])+len(ex['head'].split(" "))))
            tail_indices = list(range(tokens.index(ex['tail']), tokens.index(ex['tail'])+len(ex['tail'].split(" "))))
            bert_relation_example_tokens = tokenize(tokens, head_indices, tail_indices)
            
            SEP = sentence_encoder.tokenizer.convert_tokens_to_ids(['[SEP]'])
            CLS = sentence_encoder.tokenizer.convert_tokens_to_ids(['[CLS]'])
            word_tensor = torch.zeros((max_length)).long()
            
            new_word = CLS + bert_relation_example_tokens + SEP + bert_query_tokens + SEP
            for i in range(min(max_length, len(new_word))):
                word_tensor[i] = new_word[i]
            mask_tensor = torch.zeros((max_length)).long()
            mask_tensor[:min(max_length, len(new_word))] = 1
            seg_tensor = torch.ones((max_length)).long()
            seg_tensor[:min(max_length, len(bert_relation_example_tokens) + 1)] = 0
            fusion_set['word'].append(word_tensor)
            fusion_set['mask'].append(mask_tensor)
            fusion_set['seg'].append(seg_tensor)
    
    fusion_set['word'] = torch.stack(fusion_set['word']).cuda()
    fusion_set['seg'] = torch.stack(fusion_set['seg']).cuda()
    fusion_set['mask'] = torch.stack(fusion_set['mask']).cuda()
    logits, pred = model(fusion_set, N, K, 1)
    print(pred, logits)
    
            
            
