
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

$("#tell-us").click(function(){
  $(".survey").css("display", "block")
  $(".email").css("display", "none")
})

$("#participate-survey").click(function(){
  $(".survey").css("display", "block")
  $(".email").css("display", "none")
})

$("#get-updates").click(function(){
  $(".email").css("display", "block")
  $(".survey").css("display", "none")
})
