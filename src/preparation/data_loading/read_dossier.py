# reads from Steele_dossier.txt
# TODO: make it return the data as a specialized data structure rather than just text
import os

proj_path = __file__.split("src")[0]

def read_dossier(paragraphs=False):
    # store information
    articles = []
    # open file
    # relative path to file used, always do this
    dossier = open(proj_path + 'data/Steele_dossier.txt', 'r',
                   encoding='ascii', errors='ignore').read()
    # split the individual texts
    texts = dossier.split("-----------------------------------------------------------------------------------")
    for t in range(len(texts)):
        # get info
        texts[t] = texts[t].strip()
        info = texts[t].split('Summary')[0]
        info_clean = info.split('\n')
        info = [i for i in info_clean if i != '']
        # get text
        try:
            text = texts[t].split('Detail')[1]
        except IndexError:
            continue
        # update
        author = ['Christopher Steele']
        try:
            source_name = info[0].replace('COMPANY INTELLIGENCE REPORT ',
                                          'Steele dossier ')
        except IndexError:
            source_name = 'source not found'
        try:
            date = info[1].replace('[ ', '').replace(' ]', '')
            # weird exception
            if "DEMISE" in date:
                date = info[2].replace('[ ', '').replace(' ]', '')
        except IndexError:
            date = None
        # case of assumed gender (important for co-referencing)
        text = text.replace('S/he', 'She').replace('s/he', 'she')

        
        if paragraphs:
            # convert newlines to paragraphs
            paras = [p.strip() for p in text.split("\n\n") if len(p) > 2]
            text = "\n".join(paras)
        
        else:
            # or Gets rid of newlines and other white space which is mixed in for some reason
            text = " ".join(text.split())

        # append to result
        articles.append(text)
    # return information
    return articles

