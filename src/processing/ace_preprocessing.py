from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm


with open('../../data/ACE2005/data/English/nw/FileList', 'r') as f:
	FileList = f.read()
	filenames = [f.split('\t')[0] for f in FileList.split('\n')][1:-3]

ace_entities = []
ace_relations = []

for filename in tqdm(filenames):
	with open('../../data/ACE2005/data/English/nw/fp1/' + filename + '.apf.xml', 'r') as f:
		soup = BeautifulSoup(f.read(), 'lxml')

		entry = dict()
		for ent in tqdm(soup.find_all('entity')):
			for mention in ent.find_all('entity_mention'):
				entry['entity_id'] = ent['id']
				entry['type'] = ent['type']
				entry['subtype'] = ent['subtype']
				entry['class'] = ent['class']
				entry['mention_id'] = mention['id']
				entry['mention_type'] = mention['type']
				entry['ldctype'] = mention['type']
				entry['start'] = mention.extent.charseq['start']
				entry['end'] = mention.extent.charseq['end']
				entry['mention'] = mention.extent.charseq.get_text()
				ace_entities.append(entry)


		for rel in tqdm(soup.find_all('relation')):
			for mention in rel.find_all('relation_mention'):
				entry['relation_id'] = rel['id']
				entry['type'] = rel['type']
				entry['subtype'] = rel['subtype']
				entry['tense'] = rel['tense']
				entry['modality'] = rel['modality']
				entry['mention_id'] = mention['id']
				entry['start'] = mention.extent.charseq['start']
				entry['end'] = mention.extent.charseq['end']
				entry['mention'] = mention.extent.charseq.get_text()
				arg1 = mention.find('relation_mention_argument', {'role': 'Arg-1'})
				arg2 = mention.find('relation_mention_argument', {'role': 'Arg-2'})
				entry['arg1_mention_id'] = arg1['refid']
				entry['arg1_mention'] = arg1.extent.charseq.get_text()
				entry['arg2_mention_id'] = arg2['refid']
				entry['arg2_mention'] = arg2.extent.charseq.get_text()
				ace_relations.append(entry)

# save results
ents_df = pd.DataFrame(ace_entities)
cols = ace_entities[0].keys()
ents_df.to_csv('../../data/processed/ace_entities.csv', columns=cols)

rels_df = pd.DataFrame(ace_relations)
cols = ace_relations[0].keys()
rels_df.to_csv('../../data/processed/ace_relations.csv', columns=cols)

