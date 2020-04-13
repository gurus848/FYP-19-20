import pytest
import read_news_article_old
import pandas as pd

output_file = "data/extracted_article_data.csv"


def test_nytimes_test1():
    url = "https://www.nytimes.com/2020/03/19/us/politics/1000-checks-coronavirus-stimulus.html?action=click&module=Top%20Stories&pgtype=Homepage"
    titles = read_news_article_old.process_online_articles([url])
    df = pd.read_csv(output_file)
    last_row = df.iloc[list(df['title']).index(titles[0])]

    assert last_row['publisher'] == 'nytimes'
    assert "Emily Cochrane" in last_row['authors']
    assert 'Mnuchin Proposes $1,000' in last_row['title']
    assert 'The White House and lawmakers scrambled on Thursday to flesh out details of a $1 trillion economic stabilization plan to help workers and businesses weather a potentially deep recession, negotiating over the size and scope of direct payments to millions of people and aid for companies facing devastation in the coronavirus pandemic.' in last_row['text']


def test_cnn_test1():
    url = "https://edition.cnn.com/2020/04/09/world/lockdown-lift-vaccine-coronavirus-lancet-intl/index.html"
    titles = read_news_article_old.process_online_articles([url])
    df = pd.read_csv(output_file)
    last_row = df.iloc[list(df['title']).index(titles[0])]

    assert last_row['publisher'] == 'cnn'
    assert "Emma Reynolds" in last_row['authors']
    assert "Lockdowns shouldn't be fully lifted until coronavirus vaccine found" in last_row['title']
    assert "China's draconian restrictions on daily life appear to have halted the first wave of Covid-19 across much of the country, but the researchers used mathematical modeling to show that premature lifting of measures could result in a sweeping second wave of infection." in last_row['text']
    assert "The estimates also suggest that once the burden of rising cases is elevated, simply tightening interventions again would not reduce the burden back to its original level." in last_row['text']


def test_fox_test1():
    url = "https://www.foxnews.com/media/twitter-china-disinformation-coronavirus"
    titles = read_news_article_old.process_online_articles([url])
    df = pd.read_csv(output_file)
    last_row = df.iloc[list(df['title']).index(titles[0])]

    assert last_row['publisher'] == 'fox'
    assert "Brian Flood" in last_row['authors']
    assert "Twitter lets pro-China disinformation linger on its platform" in last_row['title']
    assert "Social media sites such as Twitter are banned in China, but that hasn’t stopped government officials from the communist nation" in last_row['text']
    assert "The spokesperson did not immediately respond to another follow-up question asking if the WHO and Zhao tweets will be placed behind the notice to provide context and why China’s Foreign Ministry spokesperson is considered a world leader." in last_row['text']


def test_other_straittimes1():
    url = "https://www.straitstimes.com/asia/australianz/a-bed-in-economy-class-air-new-zealand-unveils-sleeping-pod-concept"
    titles = read_news_article_old.process_online_articles([url])
    df = pd.read_csv(output_file)
    last_row = df.iloc[list(df['title']).index(titles[0])]

    assert last_row['publisher'] == 'other'
    assert "Some economy-class travellers envying those at the front of the plane with lie-flat beds may soon have another option" in last_row['text']
    assert '"But it was a prize worth chasing and one that we think has the potential to be a game changer for economy class travellers on all airlines around the world," Mr Reeves said' in last_row['text']


def test_other_cnbc1():
    url = "https://www.cnbc.com/2020/04/09/coronavirus-could-push-half-a-billion-people-into-poverty-globally.html"
    titles = read_news_article_old.process_online_articles([url])
    df = pd.read_csv(output_file)
    last_row = df.iloc[list(df['title']).index(titles[0])]

    assert last_row['publisher'] == 'other'
    assert 'Vicky Mckeever' in last_row['authors']
    assert "The coronavirus pandemic could result in between 420 million and 580 million more people, or 8% of the global population, living in poverty, a study by the United Nations University has found." in last_row['text']
    assert "The United Nations' International Labour Organisation estimated that the pandemic could result in 35 million more people falling into working poverty than before the outbreak, in its figures released in March." in last_row['text']


def test_other_vox1():
    url = "https://www.vox.com/policy-and-politics/2020/4/9/21213793/biden-presumptive-democratic-nominee-trump-2020-polls-swing-state"
    titles = read_news_article_old.process_online_articles([url])
    df = pd.read_csv(output_file)
    last_row = df.iloc[list(df['title']).index(titles[0])]

    assert last_row['publisher'] == 'other'
    assert 'Sean Collins' in last_row['authors']
    assert "Joe Biden, now the presumptive Democratic presidential nominee, has told voters throughout the primary that he is the candidate who can defeat President Donald Trump in the fall" in last_row['text']
    assert "All this means that it’s hard to say whether Biden can actually beat Trump. Right now the polls suggest he has about a 50-50 chance." in last_row['text']


def test_other_buzzfeed1():
    url = "https://www.buzzfeednews.com/article/anthonycormier/trump-moscow-micheal-cohen-felix-sater-campaign"
    titles = read_news_article_old.process_online_articles([url])
    df = pd.read_csv(output_file)
    last_row = df.iloc[list(df['title']).index(titles[0])]

    assert last_row['publisher'] == 'other'
    assert 'Anthony Cormier' in last_row['authors']
    assert "All through the hot summer campaign of 2016, as Donald Trump and his aides dismissed talk of unseemly ties to Moscow, two of his key business partners" in last_row['text']
    assert "Early the next morning, Sater asked if Cohen could take a phone call with “the guy coordinating” — whom Sater later testified to the Senate Intelligence Committee was the former GRU officer. " in last_row['text']
