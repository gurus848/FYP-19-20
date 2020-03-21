from django import forms

class RelationSupportCSVDatasetForm(forms.Form):
    relation_support_dataset = forms.FileField()

class QueriesCSVDatasetForm(forms.Form):
    queries_dataset = forms.FileField()
    
class TextDatasetForm(forms.Form):
    text_file_dataset = forms.FileField()
    
class NewsArticleURLForm(forms.Form):
    news_article_url = forms.URLField()
    
class IndividualSentenceForm(forms.Form):
    sentence = forms.CharField()
    
class ExistingCSVForm(forms.Form):
    existing_csv_file = forms.FileField()