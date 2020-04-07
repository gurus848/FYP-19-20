# for fyp_website app
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect
from .forms import RelationSupportCSVDatasetForm, QueriesCSVDatasetForm, TextDatasetForm, NewsArticleURLForm, IndividualSentenceForm, ExistingCSVForm, HTMLFilesForm, DeleteRelsCSVForm
import json
from django.views.decorators.cache import never_cache
import os
import sys
proj_path = os.path.abspath(os.path.dirname(__file__)).split("FYP_Web_App")[0]
sys.path.insert(1, proj_path + 'FewRel')  #so that the relation extraction framework can be loaded.
from fyp_detection_framework import DetectionFramework
from threading import Thread
from .models import ExtractedRelation, Source
from .sna_viz import SNAVizualizationManager
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.utils.html import mark_safe
from markdown import markdown
import traceback

@never_cache
@login_required
def home(request):
    """
        Renders the home page of the app.
    """
    rel_sup_csv_form = RelationSupportCSVDatasetForm()
    queries_csv_form = QueriesCSVDatasetForm()
    text_file_form = TextDatasetForm()
    article_url_form = NewsArticleURLForm()
    ind_sent_form = IndividualSentenceForm()
    html_files_form = HTMLFilesForm()
    data = []
    for i in results:
        data.append({'sentence':i['sentence'], 'head':i['head'], 'tail':i['tail'], 'pred_relation':i['pred_relation'], 'pred_sentiment':i['sent'], 'conf':i['conf'], 'dataset':i['rel_sup_ind']})
    proj_path = os.path.abspath(os.path.dirname(__file__)).split("FYP_Web_App")[0]
    ckpts = [f for f in os.listdir(proj_path + "FewRel/checkpoint") if '.pth.tar' in f][::-1]
    _get_sup_relations(request.user)
    rel_sup_datasets = []
    for i in range(len(nk_stat)):
        rel_sup_datasets.append({'i':i+1, 'sup_relations': sup_relations[i], 'nk_stat': nk_stat[i]})
    return render(request, 'home.html', {'rel_sup_csv_form': rel_sup_csv_form, 'queries_csv_form': queries_csv_form, 'text_file_form': text_file_form, 'article_url_form': article_url_form, 'ind_sent_form':ind_sent_form, 'data': data, 'ckpts': ckpts, 'rel_sup_datasets': rel_sup_datasets, 'html_files_form':html_files_form})

@never_cache
@login_required
def sna_viz(request):
    """
        Renders the SNA and vizualizations page
    """
    timestamps = []
    for i in Source.objects.filter(user=request.user):
        timestamps.append({'id':i.source_id, 'val':i.datetime_extracted.strftime('%d/%m/%Y %H:%M') + "    " + i.source})
    return render(request, 'sna_viz.html', {'timestamps':timestamps})

@never_cache
@login_required
def dataset_constructor(request):
    """
        Renders the relation support dataset constructor page
    """
    form = ExistingCSVForm()
    return render(request, 'dataset_cntr.html', {'form':form})

@never_cache
@login_required
def saved_results(request):
    """
        Renders the saved_results page
    """
    timestamps = []
    for i in Source.objects.filter(user=request.user):
        timestamps.append({'id':i.source_id, 'val':i.datetime_extracted.strftime('%d/%m/%Y %H:%M') + "    " + i.source})
    form = DeleteRelsCSVForm()
    return render(request, 'saved_results.html', {'timestamps':timestamps, 'form':form})

@never_cache
@login_required
def help_page(request):
    """
        Renders the help page
    """
    with open('static/help_page/help_page.md') as f:
        md_text = f.read()
    
    help_text = mark_safe(markdown(md_text, safe_mode='escape'))
    return render(request, 'help_page.html', {'help_text':help_text})

sup_relations = []
nk_stat = []
def _get_sup_relations(user):
    global sup_relations, nk_stat
    rel_support_datasets = os.listdir("temp/relation_support_datasets")  #gets a list of the relation support datasets
    rel_support_datasets = sorted([i for i in rel_support_datasets if '.csv' in i and user.username in i])
    sup_relations = []
    nk_stat = []
    for f in rel_support_datasets:
        df = pd.read_csv("temp/relation_support_datasets/"+f, engine='python')
        sup_relations.append(", ".join(list(df['reldescription'].unique())))
        N = df['reldescription'].unique().shape[0]
        K = df[df['reldescription'] == df['reldescription'].loc[0]].shape[0]
        
        nk_stat.append("{}-way {}-shot".format(N, K))

def handle_uploaded_file(f, fname):
    """
        Helper function that takes the uploaded files and saves them appropriately to disk.
    """
    with open(fname, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def rel_sup_csv_upload(request):
    """
        Uploads the selected relation support dataset from the user.
    """
    if request.method == "POST":
        relation_support_dataset = request.FILES['relation_support_dataset']
        _get_sup_relations(request.user)
        handle_uploaded_file(relation_support_dataset, 'temp/relation_support_datasets/relation_support_dataset_{}_{}.csv'.format(len(nk_stat) + 1, request.user.username))
        _get_sup_relations(request.user)
        rel_sup_datasets = []
        for i in range(len(nk_stat)):
            rel_sup_datasets.append({'i':i+1, 'sup_relations': sup_relations[i], 'nk_stat': nk_stat[i]})
        return HttpResponse(
            json.dumps({'success':'success', 'rel_sup_datasets':rel_sup_datasets}),
            content_type="application/json"
        )
    else:
        return HttpResponse(
            json.dumps({"error": "error, GET request not supported"}),
            content_type="application/json"
        )

def del_rel_sup_csv(request):
    """
        Called when a particular relation support CSV is to be deleted.
    """
    if request.method == "GET":
        dataset_index = int(request.GET.get("i"))
        os.remove("temp/relation_support_datasets/relation_support_dataset_{}_{}.csv".format(dataset_index, request.user.username))
        if len(nk_stat) > dataset_index:
            for i in range(dataset_index+1, len(nk_stat)+1):
                os.rename("temp/relation_support_datasets/relation_support_dataset_{}.csv".format(i), "temp/relation_support_datasets/relation_support_dataset_{}.csv".format(i-1))
    return redirect('home')
    
def query_csv_upload(request):
    """
        Uploads the selected queries CSV dataset from the user, and starts the analysis.
    """
    if request.method == "POST":
        queries_dataset = request.FILES['queries_dataset']
        handle_uploaded_file(queries_dataset, 'temp/queries.csv')

        return _start_analysis(request)
    else:
        return HttpResponse(
            json.dumps({"error": "error, GET request not supported"}),
            content_type="application/json"
        )

def text_file_upload(request):
    """
        Uploads the text file dataset from the user, and starts the analysis.
    """
    if request.method == "POST":
        txt_files = request.FILES.getlist('text_file')
        fs = [i for i in os.listdir('temp/text_files') if 'txt' in i]
        #delete old files
        for f in fs:
            os.remove('temp/text_files/{}'.format(f))
        for i, f in enumerate(txt_files):
            handle_uploaded_file(f, 'temp/text_files/text_file_{}.txt'.format(i+1))

        return _start_analysis(request)
    else:
        return HttpResponse(
            json.dumps({"error": "error, GET request not supported"}),
            content_type="application/json"
        )
    
def select_news_article(request):
    """
        Saves the news article url selected by the user, and starts the analysis.
    """
    global results
    if request.method == "POST":
        article_url = request.POST.get('article_url')
        with open('temp/url.txt', 'w') as f:
            f.write(article_url)

        return _start_analysis(request)
    else:
        return HttpResponse(
            json.dumps({"error": "error, GET request not supported"}),
            content_type="application/json"
        )

def select_ind_sentence(request):
    """
        Saves the individual query sentence selected by the user, and starts the analysis.
    """
    global results
    if request.method == "POST":

        return _start_analysis(request)
    else:
        return HttpResponse(
            json.dumps({"error": "error, GET request not supported"}),
            content_type="application/json"
        )


currently_analyzing = False  #flag indicating whether the analysis is currently running or not
results = []  #list of the results which have been generated so far
cancel_flag=[False]  #flag used to indicate whether the analysis should be cancelled or not
errors = []  #list of the errors whcih have been generated
error_i = 0  #index from which new errors can be sent
# d = DetectionFramework(ckpt_path=proj_path + "FewRel/checkpoint/NA-predict-model.pth.tar") #the detection framework
d = None
def do_analysis(ckpt, queries_type, request):
    """
        Runs the actual analysis in a different thread
    """
    global currently_analyzing, results, d
    try:
        print("starting analysis!")
        currently_analyzing = True
        results = []
        proj_path = os.path.abspath(os.path.dirname(__file__)).split("FYP_Web_App")[0]
        ckpt = proj_path + "FewRel/checkpoint/" + ckpt
        if d is None or d.ckpt_path != ckpt:
            d = DetectionFramework(ckpt_path=ckpt)
            
        d.clear_support_queries()
        if  len([i for i in os.listdir("temp/relation_support_datasets") if 'csv' in i and request.user.username in i]) == 0:
            raise ValueError("Please upload relation support dataset!")
            
        d.load_support_files("temp/relation_support_datasets", request.user.username)
        if queries_type == "csv_option":
            if not os.path.exists("temp/queries.csv"):
                raise ValueError("Please upload query CSV dataset!")
            d.load_queries_csv("temp/queries.csv")
            
        elif queries_type == "url_option":
            if not os.path.exists("temp/url.txt"):
                raise ValueError("Please specify news article url!")
            with open("temp/url.txt") as f:
                url = f.read()
            d.load_url(url)
            
        elif queries_type == "txt_option":
            d.load_text_files(os.path.abspath("temp/text_files"))
            
        elif queries_type == "ind_sentence_option":
            ind_sentence = request.POST.get('ind_sent')
            d.load_ind_sentence(ind_sentence)
            
        elif queries_type == "html_option":
            d.load_html_file_queries(os.path.abspath("temp/html_files"))

        d.detect(rt_results=results, cancel_flag=cancel_flag)
        src=None
        if queries_type == "csv_option":
            src = "queries_csv"
        elif queries_type == "txt_option":
            src = "queries_text_file"
        elif queries_type == "ind_sentence_option":
            src = "ind_sentence"
        elif queries_type == "url_option":
            with open("temp/url.txt") as f:
                src = f.read()
        elif queries_type == "html_option":
            src = "html_files"
        
        s = Source(source=src, user=request.user)
        s.save()
        for r in results:
            er = ExtractedRelation(sentence=r['sentence'],head=r['head'],tail=r['tail'],pred_relation=r['pred_relation'],sentiment=r['sent'],conf=r['conf'],ckpt=ckpt, source=s)
            er.save()
    except Exception as e:
        print(len(str(e)))
        print(str(e))
        errors.append(str(e))
        tb = traceback.format_exc()
        print(tb)
    finally:
        currently_analyzing = False
    

def _start_analysis(request):
    """
        Starts the analysis process, called from the upload file functions
    """

    if not currently_analyzing:
        cancel_flag[0] = False
        t = Thread(target=do_analysis, args=(request.POST.get('ckpt'),request.POST.get('queries_type'),request))
        t.start()
        return HttpResponse(
                json.dumps({"success": "analysis started"}),
                content_type="application/json"
            )
    else:
        return HttpResponse(
                json.dumps({"error": "error, analysis already running"}),
                content_type="application/json"
            )

def get_analysis_results(request):
    """
        Returns the periodic analysis results as a specific json list
    """
    global error_i
    if not currently_analyzing and len(results) == 0 and error_i >= len(errors):
        return HttpResponse(
            json.dumps({'status':'analysis_not_running'}),
            content_type="application/json"
        )
    elif error_i < len(errors):
        from_i = error_i
        error_i = len(errors)
        return HttpResponse(
            json.dumps({'status':'error',
                       'errors':errors[from_i:]}),
            content_type="application/json"
        )
    else:
        client_index_till = int(request.GET.get('cur_index_reached', 0))
        new_data = []
        for i in results[client_index_till:]:
            new_data.append({'sentence':i['sentence'], 'head':i['head'], 'tail':i['tail'], 'pred_relation':i['pred_relation'], 'pred_sentiment':i['sent'], 'conf':i['conf'], 'dataset':i['rel_sup_ind']})
        status = 'analysis_in_progress'
        if not currently_analyzing:
            status = 'finished_analysis'
        return HttpResponse(
            json.dumps({'status':status, 'new_data':new_data}),
            content_type="application/json"
        )
    
def cancel_analysis(request):
    """
        Cancels the analysis if it is currently running.
    """
    cancel_flag[0] = True
    if not currently_analyzing:
        return HttpResponse(
            json.dumps({'error':"error"}),
            content_type="application/json"
        )
    else:
        return HttpResponse(
            json.dumps({'success':"success"}),
            content_type="application/json"
        )
    
def dwn_analysis_csv(request):
    """
        Downloads the results of the anlaysis which have been extracted so far as a csv.
    """
    data = []
    for i in results:
        data.append((i['sentence'], i['head'], i['tail'], i['pred_relation'], i['sent'], i['conf']))
    df = pd.DataFrame(data, columns=['Sentence', 'Head', 'Tail', 'Predicted Relation', 'Predicted Sentiment', 'Confidence'])
    df.to_csv("temp/analysis_results.csv", index=False)
    
    return FileResponse(open('temp/analysis_results.csv','rb'))

def get_saved_result(request):
    """
        handles AJAX GET request to retrieve a previous result
    """
    source_id = request.GET.get('source_id')
    data = []
    objs = ExtractedRelation.objects.filter(source=source_id)
    for i in objs:
        data.append({'sentence':i.sentence, 'head':i.head, 'tail':i.tail, 'pred_relation':i.pred_relation, 'pred_sentiment':i.sentiment, 'conf':i.conf})
        
    return HttpResponse(
            json.dumps({'data':data}),
            content_type="application/json"
        )

def dwn_saved_result_csv(request):
    """
        Handles AJAX GET request to retrieve a previous result as a CSV
    """
    source_id = request.GET.get('source_id')
    data = []
    objs = ExtractedRelation.objects.filter(source=source_id)
    s = Source.objects.filter(source_id=source_id)[0]
    for i in objs:
        data.append((i.sentence, i.head, i.tail, i.pred_relation, i.sentiment, i.conf, s.source, i.rel_id, os.path.basename(i.ckpt)))
    
    df = pd.DataFrame(data, columns=['Sentence', 'Head', 'Tail', 'Predicted Relation', 'Predicted Sentiment', 'Confidence', 'Source', 'rel_id', 'Checkpoint'])
    df.to_csv("temp/analysis_results.csv", index=False)
    
    return FileResponse(open('temp/analysis_results.csv','rb'))

def dwn_all_saved_results(request):
    """
        Handles AJAX GET request to retrieve all of the saved results from the past as a CSV
    """
        
    sources = []
    for i in Source.objects.filter(user=request.user):
        sources.append((i.source_id, i.datetime_extracted.strftime('%d/%m/%Y %H:%M'), i.source))
    
    data = []
    for s, timee, s_name in sources:
        objs = ExtractedRelation.objects.filter(source=s)
        for i in objs:
            data.append((i.sentence, i.head, i.tail, i.pred_relation, i.sentiment, i.conf, timee, s_name, i.rel_id, os.path.basename(i.ckpt)))
    
    df = pd.DataFrame(data, columns=['Sentence', 'Head', 'Tail', 'Predicted Relation', 'Predicted Sentiment', 'Confidence', 'Extraction Time', 'Source', 'rel_id', 'Checkpoint'])
    df.to_csv("temp/all_analysis_results.csv", index=False)
    
    return FileResponse(open('temp/all_analysis_results.csv','rb'))
    
    
def dataset_constructor_csv_file_upload(request):
    """
        Converts the uploaded csv into a json which can then be sent to the client to update the table in the app.
    """
    if request.method == "POST":
        relation_support_dataset = request.FILES['csv_file']
        handle_uploaded_file(relation_support_dataset, 'temp/cntr_csv_file.csv')
        df = pd.read_csv('temp/cntr_csv_file.csv')
        ind = {}
        data = []
        for i, row in df.iterrows():
            if row['reldescription'] not in ind:
                data.append({'name':row['reldescription'], 'examples':[]})
                ind[row['reldescription']] = len(data) - 1
            data[ind[row['reldescription']]]['examples'].append({'head':row['head'], 'tail':row['tail'], 'sentence':row['sentence']})
        return HttpResponse(
            json.dumps({'num_rels':len(data), 'num_exs':len(data[0]['examples']), 'data':data}),
            content_type="application/json"
        )

def html_files_upload(request):
    """
        Called when html news files are uploaded to be analyzed
    """
    if request.method == "POST":
        
        html_files = request.FILES.getlist('html_file')
        fs = [i for i in os.listdir('temp/html_files') if 'html' in i]
        #delete old files
        for f in fs:
            os.remove('temp/html_files/{}'.format(f))
        for i, f in enumerate(html_files):
            handle_uploaded_file(f, 'temp/html_files/html_file_{}.html'.format(i+1))

        return _start_analysis(request)
    else:
        return HttpResponse(
            json.dumps({"error": "error, GET request not supported"}),
            content_type="application/json"
        )
    

sna_viz_errors = []  #list of the errors whcih have been generated
sna_viz_error_i = 0  #index from which new errors can be sent
    
node_link_gen_status = "not_generated"
def _gen_node_link_plotly_graph(request, dataset_type):
    global node_link_gen_status
    try:
        if node_link_gen_status == "generating":
            return
        node_link_gen_status = "generating"
        SNAVizualizationManager.make_node_link(request, dataset_type)
        node_link_gen_status = "generated"
    except Exception as e:
        node_link_gen_status = "error"
        print(str(e))
        sna_viz_errors.append(str(e))
        tb = traceback.format_exc()
        print(tb)
    
def gen_node_link(request):
    """
        Generates the node link graph, and also returns the status of whether it has been generated or not.
    """
    global sna_viz_error_i
    if request.method == "POST":
        dataset_type = request.POST.get('dataset')
        if node_link_gen_status == "generating":
            return HttpResponse(
            json.dumps({"error": "started generation"}),
            content_type="application/json"
        )
        t = Thread(target=_gen_node_link_plotly_graph ,args=(request, dataset_type))
        t.start()
        return HttpResponse(
            json.dumps({"status": "started generation"}),
            content_type="application/json"
        )
        
    elif request.method == "GET":
        if node_link_gen_status == "generating":
            return HttpResponse(
                json.dumps({"status": "still generating"}),
                content_type="application/json"
            )
        elif node_link_gen_status == "generated":
            return HttpResponse(
            json.dumps({"status": "finished"}),
            content_type="application/json"
        )
        elif node_link_gen_status == "not_generated":
            return HttpResponse(
            json.dumps({"error": "error, not generated yet"}),
            content_type="application/json"
        )
        elif node_link_gen_status == "error":
            from_i = sna_viz_error_i
            sna_viz_error_i = len(sna_viz_errors)
            return HttpResponse(
                json.dumps({'status':'error',
                           'errors':sna_viz_errors[from_i:]}),
                content_type="application/json"
            )
            
        
def upload_sna_viz_data_csv(request):
    """
        Uploads the extracted relations CSV dataset which is to be used for SNA and Viz.
    """
    if request.method == "POST":
        
        f = request.FILES['dataset']
        handle_uploaded_file(f, 'temp/sna_viz/sna_viz_dataset.csv')

        return HttpResponse(
            json.dumps({"status": "success"}),
            content_type="application/json"
        )
    else:
        return HttpResponse(
            json.dumps({"error": "error, GET request not supported"}),
            content_type="application/json"
        )
    
def del_results_csv(request):
    """
        Called when a CSV is uploaded to delete all relations with the relation ids mentioned.
    """
    if request.method == "POST":
        try:
            sources = set()
            dataset = request.FILES['dataset']
            handle_uploaded_file(dataset, 'temp/del_rels_csv.csv')
            df = pd.read_csv('temp/del_rels_csv.csv')
            for i, row in df.iterrows():
                rel_id = row['rel_id']
                objs = ExtractedRelation.objects.filter(rel_id=rel_id)
                for o in objs:
                    sources.add(o.source)
                objs.delete()
            for s in sources:
                if len(ExtractedRelation.objects.filter(source=s)) == 0:
                    Source.objects.filter(source_id=s.source_id).delete()
        except Exception as e:
            print(str(e))
            tb = traceback.format_exc()
            print(tb)
            
            return HttpResponse(
            json.dumps({"status": "error"}),
            content_type="application/json"
        )
            
        return HttpResponse(
            json.dumps({"status": "success"}),
            content_type="application/json"
        )
    
def gen_edg_bundle(request):
    """
        Handles requests to generate a hierarchical edge bundling visualizations.
    """
    pass


def dwn_rel_sup_csv(request):
    """
        Handles requests to download that specific relation support dataset.
    """
    i = int(request.GET.get('i'))
    
    return FileResponse(open('temp/relation_support_datasets/relation_support_dataset_{}_{}.csv'.format(i, request.user.username),'rb'))

def get_sna_results(request):
    """
        Performs SNA on the selected data and returns the results for the AJAX request.
    """
    dataset_type = request.POST.get('dataset')
    G, rels = SNAVizualizationManager.construct_nx_graph(request, dataset_type)
    result_dict = SNAVizualizationManager.get_SNA_metrics(G)
    print(result_dict)
    
    
    return HttpResponse(
            json.dumps({"status": "success"}),
            content_type="application/json"
        )