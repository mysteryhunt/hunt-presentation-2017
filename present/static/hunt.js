console.log('script tag');

$(document).ready(function() {
  $('a#header-inventory-control').click(function() {
    $('#header-inventory-grid').toggle();
  });
});
