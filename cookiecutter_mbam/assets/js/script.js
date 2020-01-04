// App initialization code goes here
//$("#test").on("click",function() {
//    console.log("ok clicked")
//})
var spiro=1;

// $( '.navbar-menu a' ).on( 'click', function () {
// 	$( '.navbar-menu' ).find( 'li.active' ).removeClass( 'active' );
// 	$( this ).parent( 'li' ).addClass( 'active' );
// });

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

$('#editScanModal').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget) // Button that triggered the modal
  var url= button.data('url') // Extract info from data-* attributes
	var label=button.data('label')

	$('#label').val(label)
	// for (var key in obj) {
	// 	$("#" + key).val(obj[key])
	// }
  $("#editScanForm").attr("action", url);
})
