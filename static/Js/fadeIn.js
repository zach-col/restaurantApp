/* function for animating content on scroll with the class slideanim */
  $(window).scroll(function() {
    $(".slideanim").each(function(){
      var pos = $(this).offset().top;

      var winTop = $(window).scrollTop();
        if (pos < winTop + 500) {
          $(this).addClass("slide");
        }
    });
  });