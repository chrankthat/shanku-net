// ─── Scroll-triggered fade-in ───
(function () {
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.fade-in').forEach(function (el) {
    observer.observe(el);
  });
})();

// ─── Nav scroll background ───
(function () {
  var nav = document.querySelector('.nav');
  if (!nav) return;

  function checkScroll() {
    if (window.scrollY > 40) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  }

  window.addEventListener('scroll', checkScroll, { passive: true });
  checkScroll();
})();

// ─── Stat count-up ───
(function () {
  var counted = false;
  var statNumbers = document.querySelectorAll('.stat-number');
  if (statNumbers.length === 0) return;

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting && !counted) {
        counted = true;
        countUp();
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });

  observer.observe(document.querySelector('.stats'));

  function countUp() {
    statNumbers.forEach(function (el) {
      var target = parseInt(el.getAttribute('data-target'), 10);
      var duration = 800;
      var start = 0;
      var startTime = null;

      function animate(currentTime) {
        if (!startTime) startTime = currentTime;
        var progress = Math.min((currentTime - startTime) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.floor(eased * target);
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          el.textContent = target;
        }
      }

      requestAnimationFrame(animate);
    });
  }
})();

// ─── Copy email ───
(function () {
  var copyBtn = document.querySelector('.copy-btn');
  if (!copyBtn) return;

  copyBtn.addEventListener('click', function () {
    var email = 'chris@shanku.net';
    navigator.clipboard.writeText(email).then(function () {
      copyBtn.textContent = 'Copied';
      copyBtn.classList.add('copied');
      setTimeout(function () {
        copyBtn.textContent = 'Copy';
        copyBtn.classList.remove('copied');
      }, 2000);
    });
  });
})();

// ─── Smooth scroll for nav links ───
(function () {
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
})();
