// Vercel Speed Insights
// This file injects the Speed Insights tracking script
// Documentation: https://vercel.com/docs/speed-insights/quickstart

(function() {
  // Initialize the queue
  if (window.si) return;
  window.si = function() {
    (window.siq = window.siq || []).push(arguments);
  };

  // Load the Speed Insights script
  var script = document.createElement('script');
  script.src = 'https://cdn.vercel-insights.com/v1/speed-insights/script.js';
  script.defer = true;
  script.setAttribute('data-sdkn', '@vercel/speed-insights');
  script.setAttribute('data-sdkv', '1.3.1');
  
  // Insert the script
  var firstScript = document.getElementsByTagName('script')[0];
  if (firstScript && firstScript.parentNode) {
    firstScript.parentNode.insertBefore(script, firstScript);
  } else {
    document.head.appendChild(script);
  }
})();
