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
    $("#sna_viz_nav").addClass("active");
});

do_check_request = false;
//starts the AJAX node link graph generation checks
function start_node_link_success_check(json) {
    if (json.hasOwnProperty('status')){
        $("#node_link_viz").html('Loading Graph....');
        alert('Generating Graph! Please Wait!');
        setTimeout(check_node_link_results, 3000);
        do_check_request = true;
    }else{
        alert('Error!');
    }
}

//periodically does an AJAX get request to check the results of the node link graph generation
function check_node_link_results() {
    $.ajax({
        url : "gen_node_link/", // the endpoint
        type : "GET", // http method
 
        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            if(json.hasOwnProperty('error')){
                do_check_request = false;
                alert('Error!');
                return;
            }
            if(json.status == "finished"){
                do_check_request = false;
                $.get("../static/node_link_viz.html", function( my_var ) {
                    $("#node_link_viz").html('<br/>'+my_var)
                }, 'html');
            }else if(json.status == "error"){
                do_check_request = false;
                $("#node_link_viz").html('');
                $('#error_here_yet').empty();
                alert('Error! Please see errors table');
                var d = new Date();
                for(var i = 0; i < json.errors.length; i++){
                    $('#errors_div').prepend("<p>"+d+": "+json.errors[i]+"</p>");
                }
                return;
            }
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        },
        
        complete: function() {
            // Schedule the next request when the current one's complete, even if it fails
            if(do_check_request){
                setTimeout(check_node_link_results, 2000);
            }
        }
    });
}

do_edge_bundle_check_request = false;

//starts the AJAX edge bundle graph generation checks
function start_edge_bundle_success_check(json) {
    if (json.hasOwnProperty('status')){
        $("#edg_bundle_viz").html('Loading Visualization....');
        alert('Generating Edge Bundling! Please Wait!');
        setTimeout(check_edge_bundle_results, 3000);
        do_edge_bundle_check_request = true;
    }else{
        alert('Error!');
    }
}

//periodically does an AJAX get request to check the results of the edge bundle graph generation
function check_edge_bundle_results() {
    $.ajax({
        url : "gen_edg_bundle/", // the endpoint
        type : "GET", // http method
 
        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            if(json.hasOwnProperty('error')){
                do_edge_bundle_check_request = false;
                alert('Error!');
                return;
            }
            if(json.status == "finished"){
                do_edge_bundle_check_request = false;
                vegaEmbed('#edg_bundle_viz', edge_bundle_schema);
            }else if(json.status == "error"){
                do_edge_bundle_check_request = false;
                $("#edg_bundle_viz").html('');
                $('#error_here_yet').empty();
                alert('Error! Please see errors table');
                var d = new Date();
                for(var i = 0; i < json.errors.length; i++){
                    $('#errors_div').prepend("<p>"+d+": "+json.errors[i]+"</p>");
                }
                return;
            }
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        },
        
        complete: function() {
            // Schedule the next request when the current one's complete, even if it fails
            if(do_edge_bundle_check_request){
                setTimeout(check_edge_bundle_results, 2000);
            }
        }
    });
}

//uploads a csv dataset to the server if necessary and then runs the callback specified by the user to do further requests
function upload_dataset_csv_then_run(callback) {
    event.preventDefault();
    if($('input[name="dataset_selection"]:checked').val() == "db"){
        callback.call();
        return;
    }else if($('input[name="dataset_selection"]:checked').val() == "specific_timestamp"){
        callback.call();
        return;
    }
    var formData = new FormData();
    if($('#rel_csv_file').val() == ""){
        alert('Error! No file selected!');
        return;
    }
    var dataset_name = $('#rel_csv_file')[0].files[0].name
    //validating that only csv files can be uploaded
    if (dataset_name.slice(-3) != 'csv'){
        alert('Please upload csv files only!');
        return;
    }
    
    
    formData.append('dataset', $('#rel_csv_file')[0].files[0]);
    $.ajax({
        url : "upload_csv/", // the endpoint
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

//starts the node link graph generation process
function gen_node_link_graph() {
    $.ajax({
        url : "gen_node_link/", // the endpoint
        type : "POST", // http method
        data : {"dataset": $('input[name="dataset_selection"]:checked').val(), 'source_id': $("#timestamp_selector").val()},
 
        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            start_node_link_success_check(json);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}

//when the generate node link graph button is clicked
$('#gen_node_link_graph').click(function(){
    
    upload_dataset_csv_then_run(gen_node_link_graph);
    
});

//starts the edge bundling generation process
function gen_edge_bundling() {
    $.ajax({
        url : "gen_edg_bundle/", // the endpoint
        type : "POST", // http method
        data : {"dataset": $('input[name="dataset_selection"]:checked').val(), 'source_id': $("#timestamp_selector").val()},
 
        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            start_edge_bundle_success_check(json);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}

//starts the SNA process
function do_sna(){
    $.ajax({
        url : "get_sna_results/", // the endpoint
        type : "POST", // http method
        data : {"dataset": $('input[name="dataset_selection"]:checked').val(), 'source_id': $("#timestamp_selector").val()},
 
        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            alert("SNA finished!")
            result_dict = json.result_dict
            console.log(result_dict)
            $('#sna_metrics_results').html(result_dict.sna_html)
            
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}

//called when the generate edge bundling button is clicked
$('#gen_edg_bundling').click(function() {
    upload_dataset_csv_then_run(gen_edge_bundling);
});

//called when the do SNA button is clicked
$('#do_sna').click(function() {
    upload_dataset_csv_then_run(do_sna);
});