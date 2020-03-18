//called when the webpage has been fully loaded.
$(document).ready(function() {
    $("#saved_results_nav").addClass("active");
});

var selected_timestamp_tracker = null;

//When the retrieve results button is clicked
$('#retrieve_result_button').click(function() {
    selected_timestamp_tracker = $("#timestamp_selector").val();
   $.ajax({
        url : "get/", // the endpoint
        type : "GET", // http method
        data : {'source_id': $("#timestamp_selector").val()},

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            var new_data = json.data;
            for(var i = 0; i < new_data.length; i++){
                $('#result_table').append('<tr><td>'+new_data[i].sentence+'</td> <td class="align-middle">'+new_data[i].head+'</td><td class="align-middle">'+new_data[i].tail+'</td><td>'+new_data[i].pred_relation+'</td><td>'+new_data[i].pred_sentiment+'</td><td>'+new_data[i].conf.toString()+"%"+'</td></tr>');
            }
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    }); 
});

//When the download results as csv button is clicked
$('#download_results_csv').click(function() {
    if(selected_timestamp_tracker != null){
        var link = document.createElement('a');
        link.href = "/saved_results/get_csv/?source_id="+selected_timestamp_tracker;
        link.download = "analysis_results.csv";
        link.click();
    }
});