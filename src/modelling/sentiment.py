"""
    Sentiment Library for targeted sentiment
    analysis between pairs of entities in text.
"""

import spacy
from transformers import pipeline


class TargetSentiment(object):
    """
        Framework for targeted sentiment analysis. 

        Attributes:
            dep_parser: dependency parser for targeting
                a part of the text from Spacy library.

            sernt_analyzer: sentiment analyzer from
                transformers library.
    """
    def __init__(self):
        self.dep_parser = spacy.load("en_core_web_sm", disable=['ner', 'tagger'])
        self.sent_analyzer = pipeline("sentiment-analysis")


    def _get_subtext(self, text, head, tail):
        """
            Returns the subtext between two entity mentions
            head and tail in text using dependency parsing.

            Args:
                text(str): the sentence containing
                    the two entities.
                head (str): entity mention in the text.
                tail (str): entity mention in the text.

            Returns:
                subtext (str): the text between two 
                entities. 
        """
        doc = self.dep_parser(text)
        res = set()
        inds = list() 
        for ent in (head, tail):
            n = len((ent.split(" ")))
            for i in range(len(doc)):
                if str(doc[i:i+n]) == ent:
                    inds.extend([i, i+n-1])
                    res.update([j for j in range(i, i+n)])
                    res.update([anc.i for anc in doc[i+n-1].ancestors])
                    break
        min_, max_ = min(inds), max(inds)
        res = [j for j in sorted(list(res)) if j >= min_ and j <= max_]
        return " ".join([str(doc[j]) for j in sorted(res)])


    def predict(self, text, head, tail, threshold=0.9, return_dict=False):
        """
            Predicts sentiment targeted on the text
            between e1 and e2.

            Args:
                text (str): the sentence containing
                    the two entities.
                head (str): entity mention in text.
                tail (str): entity mention in text.

            Returns:
                label (str): sentiment label
                    either NEGATIVE or POSITIVE,
                    if return_dict is False.

                res (dict): dictionary of metadata including
                    sentiment label, if return_dict is True.
                    Note: useful for debugging.
        """
        subtext = self._get_subtext(text, head, tail)
        sentiment = self.sent_analyzer(subtext)[0]
        
        # threshold the sensitivity of the sentiment for more neutrality
        if sentiment["score"] > threshold:
            label = sentiment["label"]
        else:
            label = "NEUTRAL"

        if not return_dict:
            return label

        else:
            res = dict()
            res["subtext"] = self._get_subtext(text, head, tail)
            res["head"] = head
            res["tail"] = tail
            res["label"] = label
            res["score"] = sentiment["score"]
            if sentiment["label"] == "NEGATIVE":
                res["score"] *= -1
            return res