# Welcome to the SYQ1 FYP Web App!
By: SENTHIL, Guru Sarjith and VALLAPURAM, Anish Krishna

[Access Website Here](http://vml1wk184.cse.ust.hk:3389)

## Project Overview
In today’s Information Era, there is a plethora of information available on the Internet about many different topics, with a huge number of articles and other types of text content being posted or published every single day. For example, four million blog posts are published every single day. Many of these information sources record interactions between important social entities, such as politicians, social media influencers, governments and companies, with different sources having different perspectives on each situation. The interactions and relations between these different social entities change over time as their needs and goals change, and this will be reflected in what is posted online. These changing relations could have wide-ranging consequences, especially in the case of the political elite, so there is a growing interest in tracking them and also seeing how different news sources interpret the same event. 


Social Network Analysis (SNA) is an approach used in political science to study patterns, relationships and interactions among various social entities by constructing and analyzing social networks. An important step before SNA is Relation Extraction, a task in Natural Language Processing (NLP) to automatically extract relations between social entities from text data. These relations could indicate whether 2 people like or dislike each other, whether they have met each other etc. While there are various methodologies in place to perform relation extraction using different types of data, most are still very primitive and cannot effectively model the dynamic, fast-moving relations among today’s elite economic and political entities. Therefore, in this project, we are applying relation extraction to online newspaper articles and other text data sources to automatically extract relations and sentiments between important social entities. We are also developing algorithms to analyze the results and a visualization tool to present them to the user in an easily comprehensible form. 

## Web Application Overview
This web application can be used to do Few-Shot Relation Classification on a variety of input data types, and then perform SNA on the extracted results and also view visualizations of the results. The primary machine learning model used is the BERT-PAIR model by Han et al. available [here.](https://github.com/thunlp/FewRel)

## Sample Datasets for Download
[Sample Relation Support Dataset](../static/help_page/test_relation_support_dataset.csv)

[Sample Query CSV Dataset](../static/help_page/test_queries_with_head_tail.csv)

[Sample Entities CSV Dataset](../static/help_page/test_entities_dataset.csv)

## Pages

* **Rel Ex** - to perform relation extraction
* **Saved Results** - to view relation extraction results from the past
* **SNA and Viz** - to perform SNA and create visualizations using the extracted relations
* **Dataset Constructor** - tool which can be used to construct the relation support dataset
* **Help** - this help page

## Terminology
* **Head and Tail** - This project assumes that the relations that are being extracted are between 2 entities which are mentioned in the same sentence. One of the entities is called the head, and the other entity is called the tail. 
* **Relation Support Dataset** - The relation support dataset contains the **list of relations** that you want to predict and a set number of **examples** for each relation type. This dataset is meant to teach the machine learning model about the possible relations that you want it to be able to extract. The structure of the dataset is referred to as N-way K-shot, where N is the number of relations possible and K is the number of example sentences provided for each relation. Each relation much have the same number of examples provided. For each example, the sentence, the head and the tail must be provided. The model will use the relation support dataset to determine the relation present in each query sentence, so changing any aspect of the relation support dataset could change the analysis results. It is recommended that you use 5-way 5-shot or close to that. **Only the relations that are mentioned in the relation support dataset can be predicted by the model.**
* **Query Dataset** - This is the data that you want to actually perform relation extraction on. **The relation support dataset should be different from the query dataset.** For example, the query dataset could be an extract from a book, a news article, etc.

## Instructions

* First, find text sources that you want to perform relation extraction on. These sources are called the **query datasets**. They could be Text files, a News article reference by an URL, plain text or HTML news article files. You could also use a specially formatted query CSV file, in which you can also specify the head the tail for each sentence. An example of such a CSV can be downloaded in the sample dataset download section. 
    * The application supports the analysis of multiple text files or multiple HTML files in one go. 
    * News articles from The New York Times, CNN, and Fox News will work well. If you use another source the news text extraction may not be accurate. This applies for articles both referenced by a URL and provided as an HTML file.
* Second, construct the relation support dataset that you want to use. You can use the dataset constructor to do so and download the constructed dataset as a CSV which can then be directly used with the app. **The relation support dataset should be different from the query dataset.** Multiple relation support datasets can be used at the time, in which case for each query sentence the model will be run once with each support dataset. 
* Select the relation extraction model checkpoint that you want to use. (The default one which can predict NA as a relation is recommended)
* Click 'Do Analysis'. The first time the analysis is run after the server is started up there will be a long delay of up to a few minutes as all of the machine learning models are loaded into memory for the first time.
* The analysis can be cancelled in the middle by clicking 'Cancel Analysis'. If the analysis is cancelled then any results which have already been extracted will not be written to the database.
* The webpage will automatically reload with the analysis results. These can then be downloaded by clicking the 'Download as CSV' button. 
* The analysis results from the last run will be shown when you navigate to the "Rel Ex" page.
* Previously computed results can be retrieved by going to the 'Saved Results' page and selecting the time at which the analysis was done and clicking 'Retrieve'.
* SNA and vizualizations can be done on the 'SNA and Viz' page. 

## Relation Support Dataset

* For the relation support dataset, it is best that you use approximately **5-way 5-shot**, though other settings may also work well.
* The sentences used for the relation support dataset should be from newspaper articles or similar sources for best results. For each of the relations, the sentences used should be varied in the way in which they depict the relation. For examples, look at the sample relation support dataset. 
* The relations used should ideally be very different from each other, so that there is no ambiguity in the meaning of a relationship (ex. 'like' and 'love' are too similar).
* In the dataset, the spelling and capitalization and punctuation of the heads and tails should be exactly that in the example sentence. Please ensure that there are no extra spaces at the end of the head/tail etc. Coreference resolution will not be done on the sentences by the system, though you can do it beforehand in the sentence if you like. 
* The column names in the relation support dataset should be exactly the same as that in the sample dataset. This rule applies to all datasets used throughout the app.
* ALL of the relation support datasets which have been uploaded will be used during the analysis (with each query being done once with each relation support dataset). If you do not want to use a particular dataset anymore please delete it before running a new analysis.

## SNA and Viz

* For the CSVs which are uploaded if necessary, the format should be the same as the CSVs which are downloaded from the Saved Results page.

## Saved Results

* When uploading a CSV to delete relation extraction records, the CSV should have a column called 'rel_id'. The relations with those ids will be deleted. The ids of the relations in the database can be found by clicking the 'Retrieve All Results' button to download all of the extracted relations in the database. 

## User Accounts

* You can can create a user account and login to the app with it. When logged in only results associated with the logged in user can be retrieved. 
* The admin account has username 'admin' and password 'admin'. The django admin interface can be accessed when logged into this account at http://website_base/admin, with the correct website_base substituted.
* The user can store some information about themselves in the 'My Account' page.
* Only one user can use the system to run an analysis at once, due to the computational power required. 
* The relation support datasets are separate for each user, so different users will not automatically share an uploaded dataset.

## Django Instructions

* The first time you run the server after setting it up, run 'python manage.py makemigrations' and then 'python manage.py migrate'. To make the admin user run 'python manage.py createsuperuser'.

## Admin Interface

* You can access the admin interface at http://website_url/admin. In the admin interface you can directly manipulate the database if you want to. 

