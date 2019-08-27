
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
  // $(".learn-more").css("display", "none")

})

$("#tell-us").click(function(){
  $(".survey").css("display", "block")
  $(".email").css("display", "none")
  // $(".learn-more").css("display", "none")
})

$("#get-updates").click(function(){
  $(".email").css("display", "block")
  $(".survey").css("display", "none")
  // $(".learn-more").css("display", "none")
})
