/* ============================================================
   Local Boost Lab — Shared JavaScript
   shared.js v1.0
   ============================================================ */

(function () {
  'use strict';

  /* ─── Smart Sticky Nav ──────────────────────────────── */
  function initNav() {
    var nav = document.querySelector('.nav');
    if (!nav) return;

    var lastY = 0;
    var ticking = false;

    function onScroll() {
      var y = window.scrollY;

      if (y > 80) {
        nav.classList.add('nav--scrolled');
      } else {
        nav.classList.remove('nav--scrolled');
        nav.classList.remove('nav--hidden');
      }

      if (y > lastY && y > 200) {
        nav.classList.add('nav--hidden');
      } else if (y < lastY) {
        nav.classList.remove('nav--hidden');
      }

      lastY = y;
      ticking = false;
    }

    window.addEventListener('scroll', function () {
      if (!ticking) {
        requestAnimationFrame(onScroll);
        ticking = true;
      }
    }, { passive: true });

    /* Mobile hamburger */
    var hamburger = document.querySelector('.nav__hamburger');
    var overlay   = document.querySelector('.nav__mobile-overlay');
    if (hamburger && overlay) {
      hamburger.addEventListener('click', function () {
        var open = overlay.style.display === 'flex';
        if (!open) {
          overlay.style.display = 'flex';
          requestAnimationFrame(function () { overlay.classList.add('open'); });
          hamburger.classList.add('active');
          document.body.style.overflow = 'hidden';
        } else {
          overlay.classList.remove('open');
          hamburger.classList.remove('active');
          document.body.style.overflow = '';
          setTimeout(function () { overlay.style.display = 'none'; }, 300);
        }
      });

      overlay.querySelectorAll('a').forEach(function (a) {
        a.addEventListener('click', function () {
          overlay.classList.remove('open');
          hamburger.classList.remove('active');
          document.body.style.overflow = '';
          setTimeout(function () { overlay.style.display = 'none'; }, 300);
        });
      });
    }
  }

  /* ─── Chat Widget ───────────────────────────────────── */
  function initChat() {
    var bubble  = document.querySelector('.chat-bubble');
    var window_ = document.querySelector('.chat-window');
    var close   = document.querySelector('.chat-header__close');
    var input   = document.querySelector('.chat-input');
    var sendBtn = document.querySelector('.chat-send');
    var msgs    = document.querySelector('.chat-messages');
    var typing  = document.querySelector('.chat-typing');
    if (!bubble || !window_) return;

    function openChat() {
      window_.classList.add('open');
    }
    function closeChat() {
      window_.classList.remove('open');
    }

    bubble.addEventListener('click', function () {
      window_.classList.contains('open') ? closeChat() : openChat();
    });
    if (close) close.addEventListener('click', closeChat);

    function appendMsg(text, type) {
      var div = document.createElement('div');
      div.className = 'chat-msg chat-msg--' + type;
      div.textContent = text;
      msgs.appendChild(div);
      msgs.scrollTop = msgs.scrollHeight;
      return div;
    }

    var chatHistory = [];
    var chatSessionId = null;
    var API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
      ? 'http://localhost:3000'
      : 'https://powerful-balance-production-971d.up.railway.app';

    function sendMessage() {
      if (!input) return;
      var text = input.value.trim();
      if (!text) return;
      appendMsg(text, 'user');
      input.value = '';
      input.disabled = true;
      if (sendBtn) sendBtn.disabled = true;

      if (typing) {
        typing.classList.add('show');
        msgs.scrollTop = msgs.scrollHeight;
      }

      fetch(API_BASE + '/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message:   text,
          history:   chatHistory,
          sessionId: chatSessionId,
        }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          chatSessionId = data.sessionId;
          chatHistory.push({ role: 'user', content: text });
          chatHistory.push({ role: 'assistant', content: data.reply });
          if (chatHistory.length > 20) chatHistory = chatHistory.slice(-20);
          if (typing) typing.classList.remove('show');
          appendMsg(data.reply, 'agent');
        })
        .catch(function () {
          if (typing) typing.classList.remove('show');
          appendMsg("I'm having a quick digital hiccup — email us at grow@localboostlab.com and we'll reply within 2 hours.", 'agent');
        })
        .finally(function () {
          input.disabled = false;
          if (sendBtn) sendBtn.disabled = false;
          input.focus();
        });
    }

    if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    if (input) {
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
    }

    /* Mobile full-screen */
    function checkMobile() {
      if (window.innerWidth <= 768 && window_.classList.contains('open')) {
        window_.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;border-radius:0;bottom:auto;right:auto;';
      } else {
        window_.style.cssText = '';
      }
    }
    window.addEventListener('resize', checkMobile);
  }

  /* ─── Cookie Consent ────────────────────────────────── */
  function initCookies() {
    var bar = document.querySelector('.cookie-bar');
    if (!bar) return;

    if (localStorage.getItem('lbl_cookie_consent')) {
      bar.style.display = 'none';
      return;
    }

    var acceptBtn = bar.querySelector('[data-cookie-accept]');
    var prefBtn   = bar.querySelector('[data-cookie-prefs]');

    if (acceptBtn) {
      acceptBtn.addEventListener('click', function () {
        localStorage.setItem('lbl_cookie_consent', 'accepted');
        bar.classList.add('hidden');
        setTimeout(function () { bar.style.display = 'none'; }, 300);
      });
    }

    if (prefBtn) {
      prefBtn.addEventListener('click', function () {
        var modal = document.getElementById('cookie-prefs-modal');
        if (modal) modal.style.display = 'flex';
      });
    }

    var modalClose = document.querySelector('[data-cookie-modal-close]');
    var modalSave  = document.querySelector('[data-cookie-modal-save]');
    if (modalClose) {
      modalClose.addEventListener('click', function () {
        var modal = document.getElementById('cookie-prefs-modal');
        if (modal) modal.style.display = 'none';
      });
    }
    if (modalSave) {
      modalSave.addEventListener('click', function () {
        localStorage.setItem('lbl_cookie_consent', 'custom');
        var modal = document.getElementById('cookie-prefs-modal');
        if (modal) modal.style.display = 'none';
        bar.classList.add('hidden');
        setTimeout(function () { bar.style.display = 'none'; }, 300);
      });
    }
  }

  /* ─── Fade-up on Scroll ─────────────────────────────── */
  function initFadeUp() {
    var els = document.querySelectorAll('.fade-up');
    if (!els.length || !('IntersectionObserver' in window)) {
      els.forEach(function (el) { el.classList.add('in-view'); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });

    els.forEach(function (el) { io.observe(el); });
  }

  /* ─── Form Validation Helpers ───────────────────────── */
  window.LBL = window.LBL || {};

  window.LBL.validateField = function (field) {
    var val = field.value.trim();
    var valid = field.checkValidity() && val !== '';
    if (field.type === 'email') {
      valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
    }
    field.classList.toggle('valid',   valid);
    field.classList.toggle('invalid', !valid && val !== '');

    var err = field.parentElement.querySelector('.form-error');
    if (err) err.classList.toggle('show', !valid && val !== '');
    return valid;
  };

  window.LBL.validateForm = function (form) {
    var fields = form.querySelectorAll('[required]');
    var allValid = true;
    fields.forEach(function (f) {
      if (!window.LBL.validateField(f)) allValid = false;
    });
    return allValid;
  };

  /* ─── Init on DOM ready ─────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    initNav();
    initChat();
    initCookies();
    initFadeUp();
  });
})();
