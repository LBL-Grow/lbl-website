(function () {
  'use strict';


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


  function initChat() {
    var bubble  = document.querySelector('.chat-bubble');
    var window_ = document.querySelector('.chat-window');
    var close   = document.querySelector('.chat-header__close');
    var input   = document.querySelector('.chat-input');
    var sendBtn = document.querySelector('.chat-send');
    var msgs    = document.querySelector('.chat-messages');
    var typing  = document.querySelector('.chat-typing');
    if (!bubble || !window_) return;

    var userLocale = (navigator.language || navigator.userLanguage || 'en').toLowerCase();
    var isSpanish  = userLocale.indexOf('es') === 0;
    var CHAT_INITIAL_MESSAGE = isSpanish
      ? '¡Hola! Soy Claire, tu agente de soporte disponible 24/7. Pregúntame sobre nuestros planes, cómo manejamos tu perfil de Google, o qué esperar después de registrarte.'
      : "Hi! I'm Claire, your 24/7 AI support agent. Ask me anything about our plans, how we manage your Google Business Profile, or what to expect after you sign up.";
    var existingInitMsg = msgs ? msgs.querySelector('.chat-msg--agent') : null;
    if (existingInitMsg) {
      existingInitMsg.textContent = CHAT_INITIAL_MESSAGE;
    } else if (msgs) {
      var initDiv = document.createElement('div');
      initDiv.className = 'chat-msg chat-msg--agent';
      initDiv.textContent = CHAT_INITIAL_MESSAGE;
      msgs.insertBefore(initDiv, typing);
    }

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
      : '';

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
          locale:    userLocale,
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
          var errMsg = isSpanish
            ? 'Tengo un problema técnico — escríbenos a grow@localboostlab.com y te respondemos en menos de 2 horas.'
            : "I'm having a quick digital hiccup — email us at grow@localboostlab.com and we'll reply within 2 hours.";
          appendMsg(errMsg, 'agent');
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


    function checkMobile() {
      if (window.innerWidth <= 768 && window_.classList.contains('open')) {
        window_.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;border-radius:0;bottom:auto;right:auto;';
      } else {
        window_.style.cssText = '';
      }
    }
    window.addEventListener('resize', checkMobile);
  }


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


  function initDropdownNav() {
    var trigger = document.querySelector('.nav__dropdown-trigger');
    var menu    = document.querySelector('.nav__dropdown-menu');
    if (!trigger || !menu) return;

    function openMenu() {
      menu.classList.add('open');
      trigger.setAttribute('aria-expanded', 'true');
    }
    function closeMenu() {
      menu.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', function (e) {
      e.stopPropagation();
      menu.classList.contains('open') ? closeMenu() : openMenu();
    });

    var wrapper = trigger.closest('.nav__dropdown');
    if (wrapper) {
      wrapper.addEventListener('mouseenter', openMenu);
      wrapper.addEventListener('mouseleave', closeMenu);
    }

    trigger.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openMenu();
        var first = menu.querySelector('a[role="menuitem"]');
        if (first) first.focus();
      }
      if (e.key === 'Escape') closeMenu();
    });

    menu.addEventListener('keydown', function (e) {
      var items = Array.from(menu.querySelectorAll('a[role="menuitem"]'));
      var idx   = items.indexOf(document.activeElement);
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (idx < items.length - 1) items[idx + 1].focus();
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (idx > 0) items[idx - 1].focus();
        else { closeMenu(); trigger.focus(); }
      }
      if (e.key === 'Escape') { closeMenu(); trigger.focus(); }
      if (e.key === 'Tab')    closeMenu();
    });

    document.addEventListener('click', function (e) {
      if (wrapper && !wrapper.contains(e.target)) closeMenu();
    });

    var mTrigger = document.querySelector('.nav__mobile-industries-trigger');
    var mItems   = document.querySelector('.nav__mobile-industries-items');
    if (mTrigger && mItems) {
      mTrigger.addEventListener('click', function () {
        var open = mItems.classList.contains('open');
        mItems.classList.toggle('open', !open);
        mTrigger.setAttribute('aria-expanded', open ? 'false' : 'true');
      });
    }
  }


  document.addEventListener('DOMContentLoaded', function () {
    initNav();
    initDropdownNav();
    initChat();
    initCookies();
    initFadeUp();
  });
})();
