// App initialization code goes here


// Below function determines when navbar should be transparent as user scrolls
$(document).ready(function() {
	 if ($('#detect-this').length) {
	    var scroll_pos = 0;
		$(document.body).scroll(function() {
			   scroll_pos = $(this).scrollTop();
			   if(scroll_pos > 370) {
			       $(".navbar").css('background', '#193b48');
			   } else {
			       $(".navbar").css('background', 'transparent');
			   }

		});
	 }
	 else {
		$(".navbar").css('background', '#193b48');
	 }
});

// Below modals appear after user hits edit/delete icons in the displays dashboard
$('#editScanModal').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget) // Button that triggered the modal
  var url = button.data('url') // Extract info from data-* attributes
	var label = button.data('label')

	// Attach query param to determine where to redirect user after editing
	if ($('#papayaContainer0').length) {
		var action_url = url + '?next=slice_view'
	} else {
		var action_url = url + '?next=displays'
	}

	$('#label').val(label)
  $("#editScanForm").attr("action", action_url);
})

$('#deleteScanModal').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget) // Button that triggered the modal
  var url = button.data('url') // Extract info from data-* attributes

  $("#deleteScanForm").attr("action", url);
})

$('#editSessionModal').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget) // Button that triggered the modal
  var url = button.data('url') // Extract info from data-* attributes
	var date = button.data('date')
	var field_strength = button.data('field_strength')
  var scanner = button.data('scanner')

	$('#date').val(date)
	$('#field_strength').val(field_strength)
	$('#scanner').val(scanner)
  $("#editSessionForm").attr("action", url);
})

$('#deleteSessionModal').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget) // Button that triggered the modal
  var url = button.data('url') // Extract info from data-* attributes

  $("#deleteSessionForm").attr("action", url);
})
