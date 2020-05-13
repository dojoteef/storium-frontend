function setupSuggestionsTable() {
  suggestions_table = $("#suggestions-table").DataTable({
    "columnDefs": [
      // Suggestion #
      {"targets": 0, "orderData": 0, "type": "num", "searchable": false},

      // Model
      {"targets": 1, "orderData": [0, 1]},

      // Sentence stats
      {"targets": 2, "orderData": 2, "type": "num", "searchable": false},
      {"targets": 3, "orderData": 3, "type": "num", "searchable": false},
      {"targets": 4, "orderData": 4, "type": "num", "searchable": false},

      // Rouge Precision
      {"targets": 5, "orderData": 5, "type": "num", "visible": false, "searchable": false},
      {"targets": 6, "orderData": 6, "type": "num", "visible": false, "searchable": false},
      {"targets": 7, "orderData": 7, "type": "num", "visible": false, "searchable": false},
      {"targets": 8, "orderData": 8, "type": "num", "visible": false, "searchable": false},

      // Rouge Recall
      {"targets": 9, "orderData": 9, "type": "num", "visible": false, "searchable": false},
      {"targets": 10, "orderData": 10, "type": "num", "visible": false, "searchable": false},
      {"targets": 11, "orderData": 11, "type": "num", "visible": false, "searchable": false},
      {"targets": 12, "orderData": 12, "type": "num", "visible": false, "searchable": false},

      // Rouge F1
      {"targets": 13, "orderData": 13, "type": "num", "visible": false, "searchable": false},
      {"targets": 14, "orderData": 14, "type": "num", "visible": false, "searchable": false},
      {"targets": 15, "orderData": 15, "type": "num", "visible": false, "searchable": false},
      {"targets": 16, "orderData": 16, "type": "num", "visible": false, "searchable": false}
    ]
  });

  // Create the select list and search operation
  model_column = suggestions_table.column(1);
  var select = $('<select class="custom-select custom-select-sm form-control form-control-sm" />')
    .appendTo(
      model_column.header()
    )
    .on('change', function() {
      model_column
        .search('^'+$(this).val()+'$', true)
        .draw();
    })
    .append($('<option value=".*">All</option>'));

  // Get the search data for the first column and add to the select list
  model_column
    .cache('search')
    .sort()
    .unique()
    .each(function(d) {
      select.append($('<option value="'+d+'">'+d+'</option>'));
    });

  // Create the Rouge Score selector
  var visible_columns = suggestions_table.columns('.rouge.precision').visible(true, false);
  var select = $('<select class="custom-select custom-select-sm form-control form-control-sm" />')
    .appendTo($('#rouge'))
    .on('change', function() {
      visible_columns.visible(false, false);
      visible_columns = suggestions_table.columns('.rouge.'+$(this).val()).visible(true, false);
    });
  select.append($('<option value="precision">Precision</option>'));
  select.append($('<option value="recall">Recall</option>'));
  select.append($('<option value="f1">F1</option>'));

  suggestions_table.rows().every(function () {
    this.child($('#accordion'+(this.index()+1)).show()).show();
  });

  // Finally reveal the table since it has been properly setup
  $("#suggestions-table").removeClass("invisible");
}

function setupRatingsTables() {
  $("[name=avg-rating-table").each(function() {
    $(this).DataTable({
      "info": false,
      "paging": false,
      "searching": false,
      "order": [1, 'dsc'],
      "columnDefs": [
        {"targets": [1, 2], "type": "num"}
      ]
    });
  });
}

function setupSentenceHistogram() {
  var httpRequest;
  var filtered = false;

  var histogram = new Chart("sentenceHistogram", {
    type: 'bar',
    data: {
      datasets: [{
        label: "Position of sentence overlaps",
        borderWidth: 1
      }]
    }
  });

  // Make an initial request to setup the histogram
  makeRequest();

  $("#sentenceHistogramFilter").click(
    function () {
      filtered = !filtered;
      $(this).text(filtered ? "Show All" : "Filter Unmodified");
      makeRequest();
    });

  function makeRequest() {
    httpRequest = new XMLHttpRequest();
    if (!httpRequest) {
      alert("Cannot contact server!");
      return false;
    }
    httpRequest.onreadystatechange = setupHistogram;
    httpRequest.open('GET', '/dashboard/sentence/histogram?filtered=' + filtered);
    httpRequest.send();
  }

  function setupHistogram() {
    if (httpRequest.readyState != XMLHttpRequest.DONE) {
      return;
    }

    if (httpRequest.status != 200) {
      alert("Invalid response from server!");
      return;
    }

    var response = JSON.parse(httpRequest.responseText);

    // Setup the overlap heading
    $("#sentenceHistogramCount").text(
      "Total Overlaps: " + Object.values(response).reduce((a, b) => a + b, 0)
    );

    // Then update the histogram
    histogram.data.labels = Object.keys(response);
    histogram.data.datasets[0].data = Object.values(response);
    histogram.update();
  }
}

function setupJudgmentsButton() {
  var httpRequest;

  $("#judgementCSV").click(
    function () {
      makeRequest();
    });

  function makeRequest() {
    httpRequest = new XMLHttpRequest();
    if (!httpRequest) {
      alert("Cannot contact server!");
      return false;
    }
    $(this).disabled = true;
    httpRequest.onreadystatechange = downloadCSV;
    httpRequest.open('GET', '/dashboard/judgement/contexts');
    httpRequest.send();
  }

  function downloadCSV() {
    $(this).disabled = false;
    if (httpRequest.readyState != XMLHttpRequest.DONE) {
      return;
    }

    if (httpRequest.status != 200) {
      alert("Invalid response from server!");
      return;
    }

    var csv = new Blob([httpRequest.responseText], {type: 'text/plain'});
    var url = window.URL.createObjectURL(csv);
    var link = document.createElement("a");
    link.download = "judgement_contexts.csv";
    link.href = url;
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
}

$(document).ready(function () {
  setupRatingsTables();
  setupSuggestionsTable();
  setupSentenceHistogram();
  setupJudgmentsButton();
});
