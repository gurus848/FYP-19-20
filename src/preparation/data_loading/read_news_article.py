from newspaper import Article
from bs4 import BeautifulSoup
import pandas as pd
import sys
import os


project_data_folder_path = "../../../data"

def read_news_article(url):
    """
    Reads a news article from online given a URL
    :return:
    """

    article = Article(url)
    article.download()
    article.parse()
    authors = article.authors
    date = article.publish_date
    if date is not None:
        date = article.publish_date.strftime('%d/%m/%Y')
    source_url = url
    # weird work-around
    article_ascii = article.text.encode('ascii', 'ignore')
    text = article_ascii.decode('utf-8').replace('\n\n', ' ')

    return text


def read_html_file(file):
    """
    returns a string of the html file

    :param file: the path to the file
    :return:
    """
    return read_nyt_article(open(file).read())


def read_nyt_article(htmltext):
    """

    uses the string of the article which is passed to it to extract the important information

    :param htmltext: a string which contains the html of the new york times article

    :return:
    """
    soup = BeautifulSoup(htmltext, 'lxml')
    title = soup.html.head.title.text  # extracts the title
    ps = soup.body.find_all('p')
    i = 0

    article = Article('')  # so that you can use local files with newspaper3k
    article.set_html(htmltext)
    article.parse()
    authors = article.authors

    date = article.publish_date
    if date is not None:
        date = article.publish_date.strftime('%d/%m/%Y')

    # used to find where the article text start - it always starts with a '-'
    while '—' not in ps[i].text:
        i += 1
    ps = ps[i:]

    # gets rid of useless sections
    ps = [i for i in ps if i.text != '']
    ps = [i for i in ps if i.text != 'Advertisement']
    ps = [i for i in ps if 'Now in print:' not in i.text]
    ps = [i for i in ps if 'And here\'s our email' not in i.text]
    ps = [i for i in ps if 'The Times is committed' not in i.text]
    ps = [i for i in ps if 'We\'d like to hear' not in i.text]
    ps = [i for i in ps if 'Follow The New York Times' not in i.text]
    ps = [i for i in ps if 'on Twitter: @' not in i.text]
    ps = [i for i in ps if 'on Twitter at' not in i.text]
    ps = [i for i in ps if 'contributed reporting' not in i.text]
    ps = [i for i in ps if 'contributed research' not in i.text]
    text = " ".join([i.text for i in ps])

    result_dict = {
        'title': title,
        'authors': authors,
        'text': text,
        'date': date,
        'publisher': 'nytimes'
    }
    return result_dict


def process_file_articles(file_list):
    """



    :param file_list: list of paths to files which need text and other info extracted from them
    :return:
    """
    csv_file = os.path.join(project_data_folder_path, "extracted_article_data.csv")
    open(csv_file, 'a').close()  # to create the file if it doesn't exist
    if os.path.getsize(csv_file) > 0:
        data = pd.read_csv(csv_file)
    else:
        data = pd.DataFrame(columns=['title', 'authors', 'text', 'date', 'publisher'])
    for file in file_list:
        res_dict = read_html_file(file)
        # d = pd.Series(res_dict)
        if (data['title'] == res_dict['title']).sum() == 0:
            data = data.append(res_dict, ignore_index=True)
    data.to_csv(csv_file, index=False)


def main():
    process_file_articles(['test_nyt.html'])


if __name__ == '__main__':
    main()
