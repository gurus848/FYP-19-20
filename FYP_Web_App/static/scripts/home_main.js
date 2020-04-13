// using jQuery - to ensure that the csrf token is set when a form is submitted
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue =   decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// to make form submits work - need to pass the CSRF token
var csrftoken = getCookie('csrftoken');
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

//called when the webpage has been fully loaded.
$(document).ready(function() {
       $('#query_csv_form').show();
       $("#text_file_form").hide();
       $('#news_article_form').hide();
       $('#ind_sent_form').hide(); 
    $('#html_files_form').hide();
    if($('#analysis_status_indicator').text() == "Analysis Status: Not Running"){   //only hide if the analysis is not running
        $('.analysis_status_spinner').hide();
    }
    $("#home_nav").addClass("active");
});

function analysis_start_success_check(json) {
    if (json.hasOwnProperty('success')){
        cur_index_reached = 0;
        setTimeout(check_analysis_results, 3000);
        do_check_request = true;
        $('#result_table').html('');
        $('#analysis_status_indicator').text('Analysis Status: Running Right Now');
        alert('Started analysis successfully!');
        $('.analysis_status_spinner').show();
    }else{
        alert('Error!');
    }
}

// called when the file upload button is clicked for the relation support csv dataset
$('#rel_sup_csv_form').on('submit', function(event){
    event.preventDefault();
    var formData = new FormData();
    var sup_dataset_name = $('#id_relation_support_dataset')[0].files[0].name
    //validating that only csv files can be uploaded
    if (sup_dataset_name.slice(-3) != 'csv'){
        alert('Please upload csv files only!');
        return;
    }
    
    
    formData.append('relation_support_dataset', $('#id_relation_support_dataset')[0].files[0]);
    formData.append('ckpt', $('#ckpt_selector').val());
    formData.append('queries_type', $("#query_datset_type_selection label.active input").val())
    $.ajax({
        url : "rel_sup_csv_upload/", // the endpoint
        type : "POST", // http method
        data : formData,
        processData: false,
        contentType: false,

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            if(json.hasOwnProperty('success')){
                window.location.replace('');   //redirect
                
            }else if(json.hasOwnProperty('error')){
                alert('Error when uploading relation support CSV! Please check the error section!');
                $('#error_here_yet').empty();
                $('#errors_div').prepend("<p> Relation CSV Issue: "+json.error+"</p>");
            }

        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
});

function do_csv_file_queries() {
    var formData = new FormData();
    var queries_name = $('#id_queries_dataset')[0].files[0].name
    //validating that only csv files can be uploaded
    if (queries_name.slice(-3) != 'csv'){
        alert('Please upload csv files only!');
        return;
    }
    
    
    formData.append('queries_dataset', $('#id_queries_dataset')[0].files[0]);
    formData.append('ckpt', $('#ckpt_selector').val());
    formData.append('queries_type', $("#query_datset_type_selection label.active input").val())
    formData.append('entities_type', $('input[name="entities_dataset_selection"]:checked').val());
    $.ajax({
        url : "query_csv_upload/", // the endpoint
        type : "POST", // http method
        data : formData,
        processData: false,
        contentType: false,

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            analysis_start_success_check(json);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}

// called when the do analysis button is clicked for the queries csv dataset
$('#query_csv_form').on('submit', function(event){
    event.preventDefault();
    upload_entities_dataset_csv_then_run(do_csv_file_queries);
});

function do_text_file_queries() {
    var formData = new FormData();
    
    var files = $('#id_text_file_dataset')[0].files
    for(var j = 0; j < files.length; j++){
        //validating that only txt files can be uploaded
        var text_file_name = files[j].name
        if (text_file_name.slice(-3) != 'txt'){
            alert('Please upload txt files only!');
            return;
        }
    }
    
    for(var j = 0; j < files.length; j++){
        formData.append('text_file', files[j]);
    }
    
    formData.append('ckpt', $('#ckpt_selector').val());
    formData.append('queries_type', $("#query_datset_type_selection label.active input").val())
    formData.append('entities_type', $('input[name="entities_dataset_selection"]:checked').val());
    $.ajax({
        url : "text_file_upload/", // the endpoint
        type : "POST", // http method
        data : formData,
        processData: false,
        contentType: false,

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            analysis_start_success_check(json);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}

// called when the do analysis button is clicked for the text file upload
$('#text_file_form').on('submit', function(event){
    event.preventDefault();
    upload_entities_dataset_csv_then_run(do_text_file_queries);
});

function do_news_article_queries() {
    console.log({'entities_type': $('input[name="entities_dataset_selection"]:checked').val()})
    $.ajax({
        url : "select_news_article/", // the endpoint
        type : "POST", // http method
        data : {'article_url': $('#id_news_article_url').val(), 'ckpt': $('#ckpt_selector').val(), 'queries_type': $("#query_datset_type_selection label.active input").val(), 'entities_type': $('input[name="entities_dataset_selection"]:checked').val()},

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            analysis_start_success_check(json);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}

// called when the do analysis button is clicked for the news article method
$('#news_article_form').on('submit', function(event){
    event.preventDefault();
    upload_entities_dataset_csv_then_run(do_news_article_queries);
});

function do_ind_sentence_queries() {
    $.ajax({
        url : "ind_sent_query/", // the endpoint
        type : "POST", // http method
        data : {'ind_sent': $('#id_sentence').val(), 'ckpt': $('#ckpt_selector').val(), 'queries_type': $("#query_datset_type_selection label.active input").val(),
                   'entities_type': $('input[name="entities_dataset_selection"]:checked').val()},

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            analysis_start_success_check(json);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}

// called when the do analysis button is clicked for the news article method
$('#ind_sent_form').on('submit', function(event){
    event.preventDefault();
    upload_entities_dataset_csv_then_run(do_ind_sentence_queries);
});

//Does GET results periodically to load the results of the analysis.
var do_check_request = false;
var cur_index_reached = 0;   //flag indicating whether the requests to get new results should still be done or not
function check_analysis_results() {
    $.ajax({
        url: "get_analysis_results/",
        type: "GET",
        data: {'cur_index_reached':cur_index_reached},
        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            if(json.status == 'finished_analysis'){
                //stop the requests in the future
                do_check_request = false;
                $('#analysis_status_indicator').text('Analysis Status: Finished Analyzing');
                $('.analysis_status_spinner').hide();
                $('#num_results_indicator').html('Num Results: '+json.num_results.toString());
            }
            if(json.status == 'analysis_not_running'){
                do_check_request = false;
                $('#analysis_status_indicator').text('Analysis Status: Not Running');
                $('.analysis_status_spinner').hide();
                $('#num_results_indicator').html('Num Results: '+json.num_results.toString());
                return;
            }
            if(json.status == 'error'){
                do_check_request = false;
                $('#analysis_status_indicator').text('Analysis Status: Error');
                $('#error_here_yet').empty();
                alert('Error! Please see errors during analysis table');
                var d = new Date();
                for(var i = 0; i < json.errors.length; i++){
                    $('#errors_div').prepend("<p>"+d+": "+json.errors[i]+"</p>");
                }
                $('.analysis_status_spinner').hide();
                return;
            }
            
            //process new data retrieved
            var new_data = json.new_data;
            for(var i = 0; i < new_data.length; i++){
                $('#result_table').append('<tr><td>'+new_data[i].sentence+'</td> <td class="align-middle">'+new_data[i].head+'</td><td class="align-middle">'+new_data[i].tail+'</td><td>'+new_data[i].pred_relation+'</td><td>'+new_data[i].pred_sentiment+'</td><td>'+new_data[i].conf.toString()+"%"+'</td><td>'+new_data[i].dataset+'</td></tr>');
            }
            cur_index_reached += new_data.length;
            $('#num_results_indicator').html('Num Results: '+json.num_results.toString());
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        },
        
        complete: function() {
            // Schedule the next request when the current one's complete, even if it fails
            if(do_check_request){
                setTimeout(check_analysis_results, 2000);
            }
        }
    });
}

//called when the cancel analysis button is clicked
$('#cancel_analysis_button').click(function() {
   $.ajax({
        url: "cancel_analysis/",
        type: "GET",
        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            if (json.hasOwnProperty('success')){
                alert('Cancelled analysis successfully!');
                $('#analysis_status_indicator').text('Analysis Status: Cancelled');
                do_check_request = false;
                $('.analysis_status_spinner').hide();
            }else{
                alert('Error!');
            } 
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
});

//update the analysis form view dynamically when the radio buttons for the type of query are clicked.
$("input:radio").change(function () {
   if ($(this).val() == "csv_option"){
       $('#query_csv_form').show();
       $("#text_file_form").hide();
       $('#news_article_form').hide();
       $('#ind_sent_form').hide();
       $('#html_files_form').hide();
   }else if($(this).val() == "txt_option"){
       $('#query_csv_form').hide();
       $("#text_file_form").show();
       $('#news_article_form').hide();
       $('#ind_sent_form').hide();
       $('#html_files_form').hide();
   }else if($(this).val() == "url_option"){
       $('#query_csv_form').hide();
       $("#text_file_form").hide();
       $('#news_article_form').show();
       $('#ind_sent_form').hide();
       $('#html_files_form').hide();
   }else if($(this).val() == "ind_sentence_option"){
        $('#query_csv_form').hide();
        $("#text_file_form").hide();
        $('#news_article_form').hide();
        $('#ind_sent_form').show();
       $('#html_files_form').hide();
   }else if($(this).val() == "html_option"){
        $('#query_csv_form').hide();
        $("#text_file_form").hide();
        $('#news_article_form').hide();
        $('#ind_sent_form').hide();
       $('#html_files_form').show();
   }
});

//when the download results csv button is clicked
$('#download_results_csv').click(function() {
    var x = document.getElementById("results_table_overall").rows.length;
    if(x > 1){
        var link = document.createElement('a');
        link.href = "/dwn_analysis_csv";
        link.download = "analysis_results.csv";
        link.click();
    }else{
        alert("Error no results yet!");
    }
   
});

//called when the button is clicked to delete a relation support dataset
$('#rel_sup_dataset_info').on('click', '.rel_sup_deletor', function(){
    console.log($(this).val());
    var link = document.createElement('a');
    link.href = "/del_rel_sup_csv?i="+$(this).val();
    link.click();
});

//called when the button is clicked to download a relation support dataset
$('#rel_sup_dataset_info').on('click', '.rel_sup_downloader', function(){
    console.log($(this).val());
    var link = document.createElement('a');
    link.href = "/dwn_rel_sup_csv?i="+$(this).val();
    link.download = "relation_support_dataset_"+$(this).val()+".csv";
    link.click();
});

function do_html_file_queries() {
    var formData = new FormData();
    var files = $('#id_html_files_dataset')[0].files
    for(var j = 0; j < files.length; j++){
        //validating that only html files can be uploaded
        var text_file_name = files[j].name
        if (text_file_name.slice(-4) != 'html'){
            alert('Please upload html files only!');
            return;
        }
    }
    
    for(var j = 0; j < files.length; j++){
        formData.append('html_file', files[j]);
    }
    
    formData.append('ckpt', $('#ckpt_selector').val());
    formData.append('queries_type', $("#query_datset_type_selection label.active input").val());
    formData.append('entities_type', $('input[name="entities_dataset_selection"]:checked').val());
    $.ajax({
        url : "html_files_upload/", // the endpoint
        type : "POST", // http method
        data : formData,
        processData: false,
        contentType: false,

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            analysis_start_success_check(json);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}

//Called with the html files form is submitted
$('#html_files_form').on('submit', function(){
    event.preventDefault();
    upload_entities_dataset_csv_then_run(do_html_file_queries);
});

//uploads a csv dataset to the server if necessary and then runs the callback specified by the user to do further requests
function upload_entities_dataset_csv_then_run(callback) {
    event.preventDefault();
    if($('input[name="entities_dataset_selection"]:checked').val() == "all"){
        callback.call();
        return;
    }
    var formData = new FormData();
    if($('#entities_csv_file').val() == ""){
        alert('Error! No file selected!');
        return;
    }
    var dataset_name = $('#entities_csv_file')[0].files[0].name
    //validating that only csv files can be uploaded
    if (dataset_name.slice(-3) != 'csv'){
        alert('Please upload csv files only!');
        return;
    }
    
    
    formData.append('entities_csv_file', $('#entities_csv_file')[0].files[0]);
    $.ajax({
        url : "upload_request_entities_csv/", // the endpoint
        type : "POST", // http method
        data : formData,
        processData: false,
        contentType: false,

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            callback.call();
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}