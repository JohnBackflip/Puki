(function($) {

	'use strict';

  $('.site-menu-toggle').click(function(){
    var $this = $(this);
    if ( $('body').hasClass('menu-open') ) {
      $this.removeClass('open');
      $('.js-site-navbar').fadeOut(400);
      $('body').removeClass('menu-open');
    } else {
      $this.addClass('open');
      $('.js-site-navbar').fadeIn(400);
      $('body').addClass('menu-open');
    }
  });

	
	$('nav .dropdown').hover(function(){
		var $this = $(this);
		$this.addClass('show');
		$this.find('> a').attr('aria-expanded', true);
		$this.find('.dropdown-menu').addClass('show');
	}, function(){
		var $this = $(this);
			$this.removeClass('show');
			$this.find('> a').attr('aria-expanded', false);
			$this.find('.dropdown-menu').removeClass('show');
	});



	$('#dropdown04').on('show.bs.dropdown', function () {
	  console.log('show');
	});

  // aos
  AOS.init({
    duration: 1000
  });

	// home slider
	$('.home-slider').owlCarousel({
    loop:true,
    autoplay: true,
    margin:10,
    animateOut: 'fadeOut',
    animateIn: 'fadeIn',
    nav:true,
    autoplayHoverPause: true,
    items: 1,
    autoheight: true,
    navText : ["<span class='ion-chevron-left'></span>","<span class='ion-chevron-right'></span>"],
    responsive:{
      0:{
        items:1,
        nav:false
      },
      600:{
        items:1,
        nav:false
      },
      1000:{
        items:1,
        nav:true
      }
    }
	});

	// owl carousel
	var majorCarousel = $('.js-carousel-1');
	majorCarousel.owlCarousel({
    loop:true,
    autoplay: true,
    stagePadding: 7,
    margin: 20,
    animateOut: 'fadeOut',
    animateIn: 'fadeIn',
    nav: true,
    autoplayHoverPause: true,
    items: 3,
    navText : ["<span class='ion-chevron-left'></span>","<span class='ion-chevron-right'></span>"],
    responsive:{
      0:{
        items:1,
        nav:false
      },
      600:{
        items:2,
        nav:false
      },
      1000:{
        items:3,
        nav:true,
        loop:false
      }
  	}
	});

	// owl carousel
	var major2Carousel = $('.js-carousel-2');
	major2Carousel.owlCarousel({
    loop:true,
    autoplay: true,
    stagePadding: 7,
    margin: 20,
    // animateOut: 'fadeOut',
    // animateIn: 'fadeIn',
    nav: true,
    autoplayHoverPause: true,
    autoHeight: true,
    items: 3,
    navText : ["<span class='ion-chevron-left'></span>","<span class='ion-chevron-right'></span>"],
    responsive:{
      0:{
        items:1,
        nav:false
      },
      600:{
        items:2,
        nav:false
      },
      1000:{
        items:3,
        dots: true,
        nav:true,
        loop:false
      }
  	}
	});

  var siteStellar = function() {
    $(window).stellar({
      responsive: false,
      parallaxBackgrounds: true,
      parallaxElements: true,
      horizontalScrolling: false,
      hideDistantElements: false,
      scrollProperty: 'scroll'
    });
  }
  siteStellar();

  var smoothScroll = function() {
    var $root = $('html, body');

    $('a.smoothscroll[href^="#"]').click(function () {
      $root.animate({
        scrollTop: $( $.attr(this, 'href') ).offset().top
      }, 500);
      return false;
    });
  }
  smoothScroll();

  var dateAndTime = function() {
    $('#m_date').datepicker({
      'format': 'm/d/yyyy',
      'autoclose': true
    });
    $('#checkin_date, #checkout_date').datepicker({
      'format': 'd MM, yyyy',
      'autoclose': true
    });
    $('#m_time').timepicker();
  };
  dateAndTime();


  var windowScroll = function() {

    $(window).scroll(function(){
      var $win = $(window);
      if ($win.scrollTop() > 200) {
        $('.js-site-header').addClass('scrolled');
      } else {
        $('.js-site-header').removeClass('scrolled');
      }

    });

  };
  windowScroll();


  var goToTop = function() {

    $('.js-gotop').on('click', function(event){
      
      event.preventDefault();

      $('html, body').animate({
        scrollTop: $('html').offset().top
      }, 500, 'easeInOutExpo');
      
      return false;
    });

    $(window).scroll(function(){

      var $win = $(window);
      if ($win.scrollTop() > 200) {
        $('.js-top').addClass('active');
      } else {
        $('.js-top').removeClass('active');
      }

    });
  
  };

})(jQuery);

(function ($) {
  "use strict";

  function redirectToBookingPage() {
    const checkInDate = document.getElementById("checkin_date")?.value || "";
    const checkOutDate = document.getElementById("checkout_date")?.value || "";
    const adults = document.querySelector('[name="adults"]')?.value || "";
    const children = document.querySelector('[name="children"]')?.value || "";

    if (!checkInDate || !checkOutDate || !adults || !children) {
      alert("Please fill in all fields before searching for rooms.");
      return;
    }

    localStorage.setItem("checkInDate", checkInDate);
    localStorage.setItem("checkOutDate", checkOutDate);
    localStorage.setItem("adults", adults);
    localStorage.setItem("children", children);

    window.location.href = "bookroom.html";
  }

  document.addEventListener("DOMContentLoaded", function () {
    const checkAvailabilityButton = document.querySelector(".check-availability-btn");
    if (checkAvailabilityButton) {
      checkAvailabilityButton.addEventListener("click", redirectToBookingPage);
    }
  });
})(jQuery);

// Function to populate booking details on bookroom.html
(function () {
  "use strict";

  function populateBookingDetails() {
    const guestsElement = document.getElementById("guests");
    const datesElement = document.getElementById("dates");

    if (!guestsElement || !datesElement) {
      console.warn("Guests or Dates elements not found in bookroom.html.");
      return;
    }

    const checkIn = localStorage.getItem("checkInDate") || "Not specified";
    const checkOut = localStorage.getItem("checkOutDate") || "Not specified";
    const adults = localStorage.getItem("adults") || "0";
    const children = localStorage.getItem("children") || "0";

    guestsElement.textContent = `${adults} Adults, ${children} Children`;
    datesElement.textContent = `${checkIn} — ${checkOut}`;
  }

  document.addEventListener("DOMContentLoaded", populateBookingDetails);
})();

// Function to handle "Book Now" button click and redirect to payment summary
(function () {
  "use strict";

  function handleBookNowClick(event) {
    const roomCard = event.target.closest(".room-card");
    if (!roomCard) return;

    const roomName = roomCard.querySelector("h3")?.textContent || "Unknown Room";
    const roomPrice = roomCard.querySelector("strong")?.textContent.replace("$", "") || "0";
    const roomImage = roomCard.querySelector("img")?.src || "images/default.jpg";

    localStorage.setItem("roomType", roomName);
    localStorage.setItem("roomPrice", roomPrice);
    localStorage.setItem("roomImage", roomImage);

    window.location.href = "paymentsummary.html";
  }

  document.addEventListener("DOMContentLoaded", function () {
    const bookNowButtons = document.querySelectorAll(".btn-show-rates");

    bookNowButtons.forEach((button) => {
      button.addEventListener("click", handleBookNowClick);
    });
  });
})();
