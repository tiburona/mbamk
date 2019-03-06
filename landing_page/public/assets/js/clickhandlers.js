
$( document ).ready(function() {
  var expanded = $(".navbar-toggle").attr("aria-expanded")
  if (expanded==="true") {
    $(".navbar").css("padding-bottom", "18rem")
  } else {
    $(".navbar").css("padding-bottom", "0rem")
  }
});



$(".navbar-toggle").click(function() {
  var expanded = $(".navbar-toggle").attr("aria-expanded")
  console.log("EXPANDED", expanded)
  if (expanded==="true") {
      $(".navbar").css("padding-bottom", "0rem")
  } else {
    $(".navbar").css("padding-bottom", "18rem")
  }
})
