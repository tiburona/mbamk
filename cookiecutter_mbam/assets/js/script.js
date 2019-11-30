// App initialization code goes here
//$("#test").on("click",function() {
//    console.log("ok clicked")
//})
var spiro=1;

var scroll_pos = 0;
$(document).scroll(function() {
   scroll_pos = $(this).scrollTop();
   if(scroll_pos > 850) {
       alert("hey")
       $(".navbar").css('background', '#fff');
   } 
   else {
       $(".navbar").css('background', 'transparent');

   }
});

