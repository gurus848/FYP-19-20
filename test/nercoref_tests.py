"""
    Speed Tests for src.modelling.ner_coref
    
    1. import speeds
    2. NERCoref initialisation speeds
    3. coreference resolution speeds
    4. NER speeds
    5. Query generation speeds
"""
import time
import sys
sys.path.append("../")


indent = "|----|"
def report_time(fname, timing):
    """Standard times report format"""
    print(indent + "function:", fname)
    print(indent + "time:", timing)


def import_speed():
    """Speed of importing ner_coref dependencies"""
    t1 = time.time()
    from src.modelling import ner_coref
    t2 = time.time()
    report_time("import_speed", t2-t1)


def init_NERCoref_speed():
    """Speed of initialising an instance of NERCoref"""
    from src.modelling import ner_coref
    t1 = time.time()
    resolver = ner_coref.NERCoref()
    t2 = time.time()
    report_time("import_speed", t2-t1)

        
def coref_dossier_speed():
    """Speed of running NERCoref.para_resolve() on entire data/Steele_dossier.report"""
    from src.modelling import ner_coref
    from src.preparation.data_loading import read_dossier
    
    dos = read_dossier.read_dossier(paragraphs=True)
    resolver = ner_coref.NERCoref()
    
    sum_times = 0
    for idx, article in enumerate(dos):
        t1 = time.time()
        resolver.para_resolve(article)
        t2 = time.time()
        sum_times += t2-t1
        report_time(f"coref_dossier_speed_{idx}", t2-t1)
    
    # average timing per article in dossier
    report_time(f"coref_dossier_speed_avg", sum_times/len(dos))


if __name__=="__main__":
    coref_dossier_speed()