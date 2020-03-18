"""
	Sentiment Library for targeted sentiment
	analysis between pairs of entities in text.
"""

import spacy

# load dependency parser
dep_parser = spacy.load("en_core_web_sm", disable=['ner', 'tagger'])


def get_subtext(text, e1, e2):
	"""
		Returns the subtext between two entity mentions
		e1 and e2 in text using dependency parsing.

		Args:
			text(str): the sentence containing
				the two entities.
			e1 (str): entity mention in the text.
			e2 (str): entity mention in the text.

		Returns:
			subtext (str): the text between two 
			entities. 
	"""
	pass


def predict(text, e1, e2):
	"""
		Predicts sentiment targeted on the text
		between e1 and e2.

		Args:
			text (str): the sentence containing
				the two entities.
			e1 (str): entity mention in text.
			e2 (str): entity mention in text.
		
		Returns:
			polarity (float): sentiment score.
	"""
	pass
