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
    $('.analysis_status_spinner').hide();
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
            $('#sup_relations_p').text('Currently Supported Relations: '+json.sup_relations);
            alert('Uploaded relation support CSV successfully!');
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
});

// called when the do analysis button is clicked for the queries csv dataset
$('#query_csv_form').on('submit', function(event){
    event.preventDefault();
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
});

// called when the do analysis button is clicked for the text file upload
$('#text_file_form').on('submit', function(event){
    event.preventDefault();
    var formData = new FormData();
    var text_file_name = $('#id_text_file_dataset')[0].files[0].name
    //validating that only csv files can be uploaded
    if (text_file_name.slice(-3) != 'txt'){
        alert('Please upload txt files only!');
        return;
    }
    
    formData.append('text_file', $('#id_text_file_dataset')[0].files[0]);
    formData.append('ckpt', $('#ckpt_selector').val());
    formData.append('queries_type', $("#query_datset_type_selection label.active input").val())
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
});

// called when the do analysis button is clicked for the news article method
$('#news_article_form').on('submit', function(event){
    event.preventDefault();
    $.ajax({
        url : "select_news_article/", // the endpoint
        type : "POST", // http method
        data : {'article_url': $('#id_news_article_url').val(), 'ckpt': $('#ckpt_selector').val(), 'queries_type': $("#query_datset_type_selection label.active input").val()},

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
});

// called when the do analysis button is clicked for the news article method
$('#ind_sent_form').on('submit', function(event){
    event.preventDefault();
    $.ajax({
        url : "ind_sent_query/", // the endpoint
        type : "POST", // http method
        data : {'ind_sent': $('#id_sentence').val(), 'ckpt': $('#ckpt_selector').val(), 'queries_type': $("#query_datset_type_selection label.active input").val()},

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
            }
            if(json.status == 'analysis_not_running'){
                do_check_request = false;
                $('#analysis_status_indicator').text('Analysis Status: Not Running');
                $('.analysis_status_spinner').hide();
                return;
            }
            if(json.status == 'error'){
                do_check_request = false;
                $('#analysis_status_indicator').text('Analysis Status: Error');
                $('#error_here_yet').empty();
                alert('Error! Please see errors during analysis table');
                var d = new Date();
                for(var i = 0; i < json.errors.length; i++){
                    $('#errors_div').append("<p>"+d+": "+json.errors[i]+"</p>");
                }
                $('.analysis_status_spinner').hide();
                return;
            }
            
            //process new data retrieved
            var new_data = json.new_data;
            for(var i = 0; i < new_data.length; i++){
                $('#result_table').append('<tr><td>'+new_data[i].sentence+'</td> <td class="align-middle">'+new_data[i].head+'</td><td class="align-middle">'+new_data[i].tail+'</td><td>'+new_data[i].pred_relation+'</td><td>'+new_data[i].pred_sentiment+'</td><td>'+new_data[i].conf.toString()+"%"+'</td></tr>');
            }
            cur_index_reached += new_data.length;
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

//update the analysis form view dynamically when the radio buttons are clicked.
$("input:radio").change(function () {
   if ($(this).val() == "csv_option"){
       $('#query_csv_form').show();
       $("#text_file_form").hide();
       $('#news_article_form').hide();
       $('#ind_sent_form').hide();
   }else if($(this).val() == "txt_option"){
       $('#query_csv_form').hide();
       $("#text_file_form").show();
       $('#news_article_form').hide();
       $('#ind_sent_form').hide();
   }else if($(this).val() == "url_option"){
       $('#query_csv_form').hide();
       $("#text_file_form").hide();
       $('#news_article_form').show();
       $('#ind_sent_form').hide();
   }else if($(this).val() == "ind_sentence_option"){
        $('#query_csv_form').hide();
        $("#text_file_form").hide();
        $('#news_article_form').hide();
        $('#ind_sent_form').show();
   }
});

//when the download results csv button is clicked
$('#download_results_csv').click(function() {
   //TODO 
});