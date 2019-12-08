// App initialization code goes here
//$("#test").on("click",function() {
//    console.log("ok clicked")
//})
var spiro=1;



$(document).ready(function() {  
	  if ($('#detect-this').length) {
	       $(".navbar").css('background', '#193b48');
	 }
	 else {
	 	var scroll_pos = 0;
		$(document.body).scroll(function() {
			   scroll_pos = $(this).scrollTop();
			   if(scroll_pos > 370) {
			       // alert("scroll_pos > 850")
			       $(".navbar").css('background', '#193b48');
			   } else {
			       $(".navbar").css('background', 'transparent');
			   }

		});
	 }

});






