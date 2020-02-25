from newspaper import Article
from bs4 import BeautifulSoup
import pandas as pd
import os
from enum import Enum
import urllib.request, urllib.error, urllib.parse


project_data_folder_path = "../../../data"


class ArticleType(Enum):
    NYT = 1
    FOX = 2
    OTHER = 3
    WSJ = 4
    CNN = 5


def read_html_file(file):
    """
    returns a string of the html file which is stored in the filesystem

    :param file: the path to the file
    :return:
    """

    return open(file).read()


def process_html_file(file):
    """
    Processes the file which has been passed to the function.

    :param file:   filepath to the file to be processed
    :return:
    """
    publisher = determine_publisher(read_html_file(file))
    if publisher == ArticleType.NYT:
        return read_nyt_article(read_html_file(file))
    elif publisher == ArticleType.FOX:
        return read_fox_article(read_html_file(file))
    elif publisher == ArticleType.OTHER:
        return read_other_article(read_html_file(file))
    elif publisher == ArticleType.CNN:
        return read_other_article(read_html_file(file))


def process_text_file(file):
    """
        Process an inputted raw text file and adds it to the overall csv file.
    :param file: path to the text file
    :return: object (dictionary) representing the parsed file
    """

    text = open(file).read()

    result_dict = {
        'title': file,
        'authors': 'N/A',
        'text': text,
        'date': 'N/A',
        'publisher': 'raw_text_file'
    }
    return result_dict


def process_url(url):
    """
    Processes the news article webpage pointed to by the url. Downloads the html file and calls the code for processing a local file.
    :param url: url to the article
    :return:
    """
    response = urllib.request.urlopen(url)
    webContent = response.read()

    f = open('temp.html', 'wb')
    f.write(webContent)
    f.close()
    return process_html_file('temp.html')


def determine_publisher(htmltext):
    """
        Determines the published of the particular article pointed to by the file path, so that the appropriate
        functions can be called in other parts of the code.
    :param file:
    :return:
    """
    soup = BeautifulSoup(htmltext, 'lxml')
    title = soup.html.head.title.text  # extracts the title
    if "The New York Times" in title:
        return ArticleType.NYT
    elif "Fox News" in title:
        return ArticleType.FOX
    elif "cnn" in title.lower():
        return ArticleType.CNN
    elif "WSJ" in title:
        return ArticleType.WSJ
    else:
        return ArticleType.OTHER


def read_nyt_article(htmltext):
    """

    uses the string of the new york times article which is passed to it to extract the important information

    :param htmltext: a string which contains the html of the new york times article

    :return:   returns a dict which stores the extracted result
    """
    soup = BeautifulSoup(htmltext, 'lxml')
    title = soup.html.head.title.text  # extracts the title
    ps = soup.body.find_all('p')
    i = 0

    article = Article('')  # so that you can use local files with newspaper3k
    article.set_html(htmltext)
    article.parse()
    authors = article.authors

    date = article.publish_date  # TODO: date not extracted here properly
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
    text = " ".join([" ".join(i.text.split()) for i in ps])

    result_dict = {
        'title': title,
        'authors': authors,
        'text': text,
        'date': date,
        'publisher': 'nytimes'
    }
    return result_dict


def read_fox_article(htmltext):
    """

    uses the string of the fox news article which is passed to it to extract the important information

    :param htmltext: a string which contains the html of the fox news article

    :return:  returns a dict which stores the extracted result
    """

    soup = BeautifulSoup(htmltext, 'lxml')
    title = soup.html.head.title.text  # extracts the title
    ps = soup.body.find_all('p')

    article = Article('')  # so that you can use local files with newspaper3k
    article.set_html(htmltext)
    article.parse()
    authors = article.authors    # sometimes is extracts stuff like "Reporter for Fox News. Follow Her on Twitter.."

    date = article.publish_date    # TODO: date not extracted here properly
    if date is not None:
        date = article.publish_date.strftime('%d/%m/%Y')

    # gets rid of useless sections. should be changed according to each particular website's format
    ps = [i for i in ps if i.text != '']
    ps = [i for i in ps if i.text != 'Advertisement']
    ps = [i for i in ps if 'Now in print:' not in i.text]
    ps = [i for i in ps if 'This material may not be published,' not in i.text]
    ps = [i for i in ps if not (i.next_element is not None and (i.next_element.name == 'strong' or i.next_element.name == 'em'))]
    text = " ".join([" ".join(i.text.split()) for i in ps])

    result_dict = {
        'title': title,
        'authors': authors,
        'text': text,
        'date': date,
        'publisher': 'fox'
    }
    return result_dict


def read_other_article(htmltext):
    """
        Processes articles other than the ones for which specific rules have been written
    :param htmltext: the htmltext of the article
    :return:
    """
    article = Article('')  # so that you can use local files with newspaper3k
    article.set_html(htmltext)
    article.parse()
    authors = article.authors  # sometimes is extracts stuff like "Reporter for Fox News. Follow Her on Twitter.."

    date = article.publish_date  # TODO: date not extracted here properly
    if date is not None:
        date = article.publish_date.strftime('%d/%m/%Y')

    text = article.text
    text = "".join(i for i in text if i != '\n')
    title = article.title

    publisher = 'other'
    if determine_publisher(htmltext) == ArticleType.CNN:
        publisher = 'cnn'

    result_dict = {
        'title': title,
        'authors': authors,
        'text': text,
        'date': date,
        'publisher': publisher
    }
    return result_dict


def process_file_articles(file_list):
    """
        Given a list of filepaths, process all of them and extracts their data and adds it to the csv file.
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
        res_dict = process_html_file(file)
        if (data['title'] == res_dict['title']).sum() == 0:
            data = data.append(res_dict, ignore_index=True)
    data.to_csv(csv_file, index=False)


def process_online_articles(url_list):
    """
            Given a list of urls, process all of them and extracts their data and adds it to the csv file.
        :param url_list: list of urls which need text and other info extracted from them
        :return:
    """
    csv_file = os.path.join(project_data_folder_path, "extracted_article_data.csv")
    open(csv_file, 'a').close()  # to create the file if it doesn't exist
    if os.path.getsize(csv_file) > 0:
        data = pd.read_csv(csv_file)
    else:
        data = pd.DataFrame(columns=['title', 'authors', 'text', 'date', 'publisher'])
    for url in url_list:
        res_dict = process_url(url)
        if (data['title'] == res_dict['title']).sum() == 0:
            data = data.append(res_dict, ignore_index=True)
    data.to_csv(csv_file, index=False)


def process_text_files(file_list):
    """

        Given a list of filepaths, processes all of them and adds them to the extracted data csv file
    :param file_list: The list of filepaths to process
    :return:
    """
    csv_file = os.path.join(project_data_folder_path, "extracted_article_data.csv")
    open(csv_file, 'a').close()  # to create the file if it doesn't exist
    if os.path.getsize(csv_file) > 0:
        data = pd.read_csv(csv_file)
    else:
        data = pd.DataFrame(columns=['title', 'authors', 'text', 'date', 'publisher'])
    for file in file_list:
        res_dict = process_text_file(file)
        if (data['title'] == res_dict['title']).sum() == 0:
            data = data.append(res_dict, ignore_index=True)
    data.to_csv(csv_file, index=False)


def main():
    # process_file_articles(['fox_news_article_example.html', 'test_nyt.html'])
    process_online_articles(['https://us.cnn.com/2020/02/14/us/donald-lee-moore-shawn-marie-neal-dna-serial-podcast-trnd/index.html'])
    # process_text_files(['read_dossier.py'])


if __name__ == '__main__':
    main()
