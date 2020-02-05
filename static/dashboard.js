$(document).ready(function () {
  suggestions_table = $("#suggestions-table").DataTable({
    "columnDefs": [
      {"targets": 5, "orderable": false},
      {"targets": 4, "orderData": 4, "type": "num"},
      {"targets": 3, "orderData": 3, "type": "num"},
      {"targets": 2, "orderData": 2, "type": "num"},
      {"targets": 1, "orderData": [0, 1]},
      {"targets": 0, "orderData": 0, "type": "html-num"}
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

  var all_rating_tables = document.getElementsByName("avg-rating-table");
  for (var i=0, len=all_rating_tables.length|0; i<len; i=i+1|0) {
    $("#" + all_rating_tables[i].id).DataTable({
      "info": false,
      "paging": false,
      "searching": false,
      "order": [1, 'dsc'],
      "columnDefs": [
        {"targets": [1, 2], "type": "num"}
      ]
    });
  }
});
