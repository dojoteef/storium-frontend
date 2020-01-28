$(document).ready(function () {
  $("#suggestions-table").DataTable({
    "columnDefs": [
      {"targets": 2, "orderable": false},
      {"targets": 1, "orderData": [0, 1]},
      {"targets": 0, "orderData": 0, "type": "html-num"}
    ]
  });
  var all_rating_tables = document.getElementsByName("avg-rating-table");
  for (var i=0, len=all_rating_tables.length|0; i<len; i=i+1|0) {
    $("#" + all_rating_tables[i].id).DataTable({
      "info": false,
      "paging": false,
      "searching": false,
      "columnDefs": [
        {"targets": [1, 2], "type": "num"}
      ]
    });
  }
});
