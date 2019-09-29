from newspaper import Article
from bs4 import BeautifulSoup

# TODO: return more of the information rather than just the text.


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
        'text': text
    }
    return result_dict


def main():
    print(read_html_file('test_nyt.html'))


if __name__ == '__main__':
    main()
