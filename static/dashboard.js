function setupSuggestionsTable() {
  suggestions_table = $("#suggestions-table").DataTable({
    "columnDefs": [
      {"targets": 4, "orderData": 4, "type": "num"},
      {"targets": 3, "orderData": 3, "type": "num"},
      {"targets": 2, "orderData": 2, "type": "num"},
      {"targets": 1, "orderData": [0, 1]},
      {"targets": 0, "orderData": 0, "type": "num"}
    ]
  });

  // Create the select list and search operation
  model_column = suggestions_table.column(1);
  var select = $('<select aria-controls="suggestions-table" class="custom-select custom-select-sm form-control form-control-sm" />')
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

$(document).ready(function () {
  setupRatingsTables();
  setupSuggestionsTable();
  setupSentenceHistogram();
});
