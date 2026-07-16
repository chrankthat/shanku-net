// resume.js - the one deliberate JS exception on this page: video
// facades pop a youtube-nocookie iframe only on activation. Everything
// else (including every venture disclosure) works with JS off.
// Bound via addEventListener per site convention (js/filmstrip.js),
// never inline onclick - inline handlers race the defer load.
(function () {
  'use strict';

  function playFacade(el) {
    if (el.querySelector('iframe')) return;
    var src = el.getAttribute('data-embed') + '?autoplay=1&rel=0';
    el.innerHTML = '';
    var iframe = document.createElement('iframe');
    iframe.src = src;
    iframe.title = 'Demo video';
    iframe.allow = 'autoplay; encrypted-media; picture-in-picture';
    iframe.allowFullscreen = true;
    el.appendChild(iframe);
  }

  document.querySelectorAll('.facade[data-embed]').forEach(function (el) {
    el.addEventListener('click', function () {
      playFacade(el);
    });
    // Keyboard path (tabindex + role="button" are in the markup):
    // Enter and Space must both activate, Space must not scroll.
    el.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        playFacade(el);
      }
    });
  });
})();
