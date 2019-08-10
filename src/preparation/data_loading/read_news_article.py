from newspaper import Article

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
