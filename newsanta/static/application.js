$(function() {

  for (var i = 0; i < 100; i++) {
    setTimeout(makeSnowflake, Math.random() * 10 * 1000);
  }

  function makeSnowflake() {
    var r = Math.random() * 10;
    var x = Math.round(Math.random() * $(document).width());
    var speed = Math.round(Math.random() * 20) + 10 + 's';
    var snowflake = $('<div></div>').addClass('snowflake');

    snowflake.css({
      width: r + 'px',
      height: r + 'px',
      right: x + 'px',
      webkitAnimationDuration: speed,
      mozAnimationDuration: speed,
      animationDuration: speed
    });

    $('.snow-container').prepend(snowflake);

    snowflake.on('animationend webkitAnimationEnd oanimationend msAnimationEnd', function() {
      $(this).remove();
      makeSnowflake();
    });
  }

  var scrolled = false;
  var lastScrollTop = 0;

  $(window).scroll(function() {
    scrolled = true;
  });

  setInterval(function() {
    if (scrolled) {
      handleScroll();
      scrolled = false;
    }
  }, 250);

  function handleScroll() {
    var st = $(this).scrollTop();

    // Make sure they scroll more than delta
    if (Math.abs(lastScrollTop - st) <= 5) {
      return;
    }

    // If they scrolled down and are past the navbar, add class .nav-up.
    // This is necessary so you never see what is "behind" the navbar.
    if (st > lastScrollTop && st > 89) {
      // Scroll Down
      $('.timetable').addClass('nav-up');
    } else {
      // Scroll Up
      if (st + $(window).height() < $(document).height()) {
        $('.timetable').removeClass('nav-up');
      }
    }

    lastScrollTop = st;
  }

  var cloud = $('<div class="cloud"></div>');
  cloud.text($('.banner-welcome h2 abbr').attr('title'));
  $('.banner-welcome h2 abbr').attr('title', '');
  $('.banner-welcome').append(cloud);
  $('.banner-welcome h2 abbr').hover(function() {
    cloud.fadeIn('slow');
  }, function() {
    cloud.fadeOut('slow');
  });
});