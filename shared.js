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

    function autoReply(userText) {
      var lower = userText.toLowerCase();
      var reply = 'Thanks for reaching out! I\'ll connect you with a real human shortly. In the meantime, you can also email us at grow@localboostlab.com — we respond within 24 hours.';

      if (lower.includes('pricing') || lower.includes('price') || lower.includes('cost') || lower.includes('plan')) {
        reply = 'Great question! We have 3 plans:\n• Reviews — $97/mo (reputation management)\n• Presence — $157/mo (posts + reviews, most popular)\n• Complete — $217/mo (everything + priority support)\nAnnual billing saves you 15%. See full details at our pricing page!';
      } else if (lower.includes('cancel') || lower.includes('stop') || lower.includes('quit')) {
        reply = 'No problem — you can cancel anytime by emailing grow@localboostlab.com. We process cancellations within 24 hours, no questions asked. Service continues through your current billing period.';
      } else if (lower.includes('negative') || lower.includes('bad review') || lower.includes('1 star') || lower.includes('2 star')) {
        reply = 'We NEVER auto-respond to negative reviews. For 1–2 star reviews, you\'ll get an urgent alert within 5 minutes. For 3-star, an alert within 15 minutes with a draft you can approve or edit.';
      } else if (lower.includes('setup') || lower.includes('start') || lower.includes('how long') || lower.includes('onboard')) {
        reply = 'Setup takes 5–7 minutes — just fill out our onboarding form after payment. Your first post goes live within 48 hours. You\'ll get a notification when we go live!';
      } else if (lower.includes('google') || lower.includes('gbp') || lower.includes('profile')) {
        reply = 'We manage your Google Business Profile — review responses, weekly posts, monthly reports. You grant us Manager access (never Owner), and we handle everything from there.';
      }

      if (typing) {
        typing.classList.add('show');
        msgs.scrollTop = msgs.scrollHeight;
      }

      setTimeout(function () {
        if (typing) typing.classList.remove('show');
        appendMsg(reply, 'agent');
      }, 2000);
    }

    function sendMessage() {
      if (!input) return;
      var text = input.value.trim();
      if (!text) return;
      appendMsg(text, 'user');
      input.value = '';
      autoReply(text);
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
