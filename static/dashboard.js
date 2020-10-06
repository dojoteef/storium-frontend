function setupSuggestionsTable() {
  suggestions_table = $("#suggestions-table").DataTable({
    "columnDefs": [
      // Suggestion #
      {"targets": 0, "orderData": 0, "type": "num", "searchable": false},

      // Game PID
      {"targets": 1, "orderData": 1, "searchable": true},

      // Model
      {"targets": 2, "orderData": [0, 2]},

      // Sentence stats
      {"targets": 3, "orderData": 3, "type": "num", "searchable": false},
      {"targets": 4, "orderData": 4, "type": "num", "searchable": false},
      {"targets": 5, "orderData": 5, "type": "num", "searchable": false},

      // Rouge Precision
      {"targets": 6, "orderData": 6, "type": "num", "visible": false, "searchable": false},
      {"targets": 7, "orderData": 7, "type": "num", "visible": false, "searchable": false},
      {"targets": 8, "orderData": 8, "type": "num", "visible": false, "searchable": false},
      {"targets": 9, "orderData": 9, "type": "num", "visible": false, "searchable": false},

      // Rouge Recall
      {"targets": 10, "orderData": 10, "type": "num", "visible": false, "searchable": false},
      {"targets": 11, "orderData": 11, "type": "num", "visible": false, "searchable": false},
      {"targets": 12, "orderData": 12, "type": "num", "visible": false, "searchable": false},
      {"targets": 13, "orderData": 13, "type": "num", "visible": false, "searchable": false},

      // Rouge F1
      {"targets": 14, "orderData": 14, "type": "num", "visible": false, "searchable": false},
      {"targets": 15, "orderData": 15, "type": "num", "visible": false, "searchable": false},
      {"targets": 16, "orderData": 16, "type": "num", "visible": false, "searchable": false},
      {"targets": 17, "orderData": 17, "type": "num", "visible": false, "searchable": false}
    ]
  });

  // Create the select list and search operation
  model_column = suggestions_table.column(2);
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
  $("[name='avg-rating-table']").each(function() {
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
  $(".sentence-histogram").each(function() {
    var graphData = {
      datasets: [{
        label: "Position of sentence overlaps",
        borderWidth: 1,
        backgroundColor: "rgba(0, 0, 255, 0.4)"
      }]
    };

    var model_name = $(this).attr("name");
    var count = $(".histogram-count", this);
    var canvas = $(".histogram-canvas", this);
    var exportButton = $(".histogram-export", this);

    var histogram = new Chart(canvas, {
      type: 'bar',
      data: graphData,
      options: {
        scales: {
          yAxes: [{
            ticks: {
              beginAtZero: true
            }
          }]
        }
      }
    });

    exportButton.click(
      function () {
        var svgContext = C2S(400, 400);
        var exportableHistogram = new Chart(svgContext, {
          type: 'bar',
          data: histogram.data,
          options: Object.assign(
            // deactivate responsiveness and animation
            {}, histogram.options, {"responsive": false, "animation": false}
          )
        });

        var output = new Blob([svgContext.getSerializedSvg()], {type: 'text/plain'});
        var url = window.URL.createObjectURL(output);
        var link = document.createElement("a");
        link.download = "sentence_histogram.svg";
        link.href = url;
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      });

    // Make the requests to setup the histograms
    var httpRequest = new XMLHttpRequest();
    if (!httpRequest) {
      alert("Cannot contact server!");
      return false;
    }

    urlParams = new URLSearchParams(window.location.search);
    urlParams.append("model", model_name);

    httpRequest.onreadystatechange = setupHistogram;
    httpRequest.open('GET', '/dashboard/sentence/histogram?' + urlParams.toString());
    httpRequest.send();

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
      count.text(
        "Total Overlaps: " + Object.values(response).reduce((a, b) => a + b, 0)
      );

      // Then update the histogram
      histogram.data.labels = Object.keys(response).map((num) => Number(num) + 1);
      histogram.data.datasets[0].data = Object.values(response);
      histogram.update();
    }
  });
}

function setupJudgmentsButton() {
  $(".judgements.btn").click(
    function () {
      makeRequest($(this));
    });

  function makeRequest(element) {
    httpRequest = new XMLHttpRequest();
    if (!httpRequest) {
      alert("Cannot contact server!");
      return false;
    }

    var spinner = $('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>')
      .appendTo(
        element
      )
    text = element.children().first().detach()

    // Must open the GET request before setting headers
    httpRequest.open('GET', '/dashboard/judgement/contexts?limit=' + $('#judgementCount').val());
    if (element.prop('id') == 'judgementCSV') {
      httpRequest.setRequestHeader('Accept', 'text/csv');
      httpRequest.onreadystatechange = downloadJudgements(httpRequest, element, spinner, text, 'csv');
    }
    else if (element.prop('id') == 'judgementJSON') {
      httpRequest.setRequestHeader('Accept', 'text/json');
      httpRequest.onreadystatechange = downloadJudgements(httpRequest, element, spinner, text, 'json');
    }

    element.prop('disabled', true);
    httpRequest.send();
  }

  function downloadJudgements(httpRequest, element, spinner, text, ext) {
    return function() {
      if (httpRequest.readyState != XMLHttpRequest.DONE) {
        return;
      }

      spinner.remove()
      text.appendTo(element)
      element.prop('disabled', false);

      if (httpRequest.status != 200) {
        alert("Invalid response from server!");
        return;
      }

      var output = new Blob([httpRequest.responseText], {type: 'text/plain'});
      var url = window.URL.createObjectURL(output);
      var link = document.createElement("a");
      link.download = "judgement_contexts." + ext;
      link.href = url;
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    }
  }
}

function enableDropdowns() {
  $('.dropdown-item').on('click',  function() {
    var button = $(this).parent().siblings('button');
    $(button).text($(this).text());
    $(button).val($(this).text());
  });

  $('.dropdown-toggle').each(function() {
    if (!$(this).hasClass("nav-link")) {
      var originalText = $(this).text();
      $(this).click(function() {
        $(this).text(originalText);
        $(this).removeClass("active");
        $(this).siblings('.dropdown-menu').children('.dropdown-item').each(function() {
          $(this).removeClass("active");
        });
      });
    }
  });
}

function enableMultitabs() {
  $('[data-toggle="tab"]').on('click',  function() {
    var target = $(this).attr('data-target');
    if (!$(target).hasClass("active")) {
      $(target).addClass("active");
    }

    var button = $(this).parent().siblings('button');
    $(button).on('click', function() {
      if ($(target).hasClass("active")) {
        $(target).removeClass("active");
      }
    });
  });
}

function enableTooltips() {
  $('[data-toggle="tooltip"]').tooltip();
}

function enablePopovers() {
  $('[data-toggle="popover"]').popover();
}

$(document).ready(function () {
  setupRatingsTables();
  setupSuggestionsTable();
  setupSentenceHistogram();
  setupJudgmentsButton();

  enableDropdowns();
  enableMultitabs();
  enablePopovers();
  enableTooltips();
});
