from fewshot_re_kit.data_loader import FewRelDatasetPair, get_loader_pair
from fewshot_re_kit.framework import FewShotREFramework
from fewshot_re_kit.sentence_encoder import BERTPAIRSentenceEncoder
from models.pair import Pair
import os
import torch
import spacy
import neuralcoref

#RUNS USING GPU if available

checkpoint_path = "checkpoint/pair-bert-train_wiki-val_wiki-5-1.pth.tar"
bert_pretrained_checkpoint = 'bert-base-uncased'
max_length = 128


sentence_encoder = BERTPAIRSentenceEncoder(
                    bert_pretrained_checkpoint,
                    max_length)

model = Pair(sentence_encoder, hidden_size=768)

if torch.cuda.is_available():
    model = model.cuda()

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

    
def bert_tokenize(tokens, head_indices, tail_indices):
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

nlp = spacy.load("en_core_web_sm")
neuralcoref.add_to_pipe(nlp)

max_length = 128
for q in queries:
    fusion_set = {'word': [], 'mask': [], 'seg': []}
    doc = nlp(q['sentence'])
    doc = nlp(doc._.coref_resolved)  #use neuralcoref to do coreference resolution and then do NER again
    tokens = list(map(str, doc))
    
    #TODO: use NER entities to find all pairs to check
    
    tokenized_head = list(map(str, nlp(q['head'])))  #TODO: remove once the NER pair thing has been written.
    tokenized_tail = list(map(str, nlp(q['tail'])))
    
    head_indices = list(range(tokens.index(tokenized_head[0]), tokens.index(tokenized_head[0])+len(tokenized_head)))   
    tail_indices = list(range(tokens.index(tokenized_tail[0]), tokens.index(tokenized_tail[0])+len(tokenized_tail)))
    bert_query_tokens = bert_tokenize(tokens, head_indices, tail_indices)
    for relation in example_relation_data:
        for ex in relation['examples']:
            
            doc = nlp(ex['sentence'])
            doc = nlp(doc._.coref_resolved)  #use neuralcoref to do coreference resolution, and then do tokenization. coreference resolution is not a perfect process
            tokens = list(map(str, doc))
            
            tokenized_head = list(map(str, nlp(ex['head'])))   #head and tail spelling and punctuation should match the corefered output exactly
            tokenized_tail = list(map(str, nlp(ex['tail'])))
            head_indices = list(range(tokens.index(tokenized_head[0]), tokens.index(tokenized_head[0])+len(tokenized_head)))   
            tail_indices = list(range(tokens.index(tokenized_tail[0]), tokens.index(tokenized_tail[0])+len(tokenized_tail)))
            bert_relation_example_tokens = bert_tokenize(tokens, head_indices, tail_indices)
            
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
    
    
    fusion_set['word'] = torch.stack(fusion_set['word'])
    fusion_set['seg'] = torch.stack(fusion_set['seg'])
    fusion_set['mask'] = torch.stack(fusion_set['mask'])
    
    if torch.cuda.is_available():
        fusion_set['word'] = fusion_set['word'].cuda()
        fusion_set['seg'] = fusion_set['seg'].cuda()
        fusion_set['mask'] = fusion_set['mask'].cuda()
        
    logits, pred = model(fusion_set, N, K, 1)
    print('Sentence: \"{}\", prediction: {}'.format(q['sentence'], example_relation_data[pred.item()]['name']))   #todo: handle na case, which would be out of bounds
    
            
            
