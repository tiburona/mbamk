
$( document ).ready(function() {
  var expanded = $(".navbar-toggle").attr("aria-expanded")
  if (expanded==="true") {
    $(".navbar").css("padding-bottom", "22rem")
  } else {
    $(".navbar").css("padding-bottom", "0rem")
  }
});

$(".navbar-toggle").click(function() {
  var expanded = $(".navbar-toggle").attr("aria-expanded")
  if (expanded==="true") {
      $(".navbar").css("padding-bottom", "0rem")
  } else {
    $(".navbar").css("padding-bottom", "22rem")
  }
})

$("#find-out-more").click(function(){
  $("#welcome-text-container").css("display", "block")
  $(".google-form").css("display", "block")
  $("#find-out-more").text("Welcome!")
  $("#find-out-more").css("color", "#ffb366")
  $(".learn-more").css("display", "none")

})
