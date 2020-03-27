from django import forms

class RelationSupportCSVDatasetForm(forms.Form):
    relation_support_dataset = forms.FileField(label="Add Relation Support Dataset")

class QueriesCSVDatasetForm(forms.Form):
    queries_dataset = forms.FileField(label='Queries CSV Dataset')
    
class TextDatasetForm(forms.Form):
    text_file_dataset = forms.FileField(label='Text File Datasets', widget=forms.ClearableFileInput(attrs={'multiple': True}))
    
class NewsArticleURLForm(forms.Form):
    news_article_url = forms.URLField(label='News Article URL')
    
class IndividualSentenceForm(forms.Form):
    sentence = forms.CharField(label='Individual Sentence')
    
class HTMLFilesForm(forms.Form):
    html_files_dataset = forms.FileField(label='News HTML Files', widget=forms.ClearableFileInput(attrs={'multiple': True}))
    
class ExistingCSVForm(forms.Form):
    existing_csv_file = forms.FileField(label='Existing Dataset CSV')
    
class DeleteRelsCSVForm(forms.Form):
    delete_rels_csv = forms.FileField(label='Select CSV')