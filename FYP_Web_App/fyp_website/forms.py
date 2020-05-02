from django import forms

class RelationSupportCSVDatasetForm(forms.Form):
    """
        The form which is used to upload a relation support dataset
    """
    relation_support_dataset = forms.FileField(label="Add Relation Support Dataset")

class QueriesCSVDatasetForm(forms.Form):
    """
        The form which is used to upload a queries CSV dataset
    """
    queries_dataset = forms.FileField(label='Queries CSV Dataset')
    
class TextDatasetForm(forms.Form):
    """
        The form which is used to upload a text dataset
    """
    text_file_dataset = forms.FileField(label='Text File Datasets', widget=forms.ClearableFileInput(attrs={'multiple': True}))
    
class NewsArticleURLForm(forms.Form):
    """
        The form which is used to select a news article using a URL
    """
    news_article_url = forms.URLField(label='News Article URL')
    
class IndividualSentenceForm(forms.Form):
    """
        The form which is used to specify an individual sentence from which queries are to be made
    """
    sentence = forms.CharField(label='Individual Sentence')
    
class HTMLFilesForm(forms.Form):
    """
        The form which is used to upload HTML files as queries
    """
    html_files_dataset = forms.FileField(label='News HTML Files', widget=forms.ClearableFileInput(attrs={'multiple': True}))
    
class ExistingCSVForm(forms.Form):
    """
        The form which is used to upload an existing relation support CSV in the dataset constructor page
    """
    existing_csv_file = forms.FileField(label='Existing Dataset CSV')
    
class DeleteRelsCSVForm(forms.Form):
    """
        The form which is used to upload a CSV to delete relation records in the database
    """
    delete_rels_csv = forms.FileField(label='Select CSV')