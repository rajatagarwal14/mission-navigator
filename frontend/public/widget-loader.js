/**
 * Mission Navigator - Embeddable Chat Widget
 *
 * Add this script to any page to embed the chat widget:
 * <script src="https://your-domain.com/widget-loader.js"></script>
 */
(function() {
  var WIDGET_URL = window.MISSION_NAVIGATOR_URL || '';

  // Create floating button
  var btn = document.createElement('div');
  btn.id = 'mn-widget-btn';
  btn.innerHTML = '<svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>';
  btn.style.cssText = 'position:fixed;bottom:20px;right:20px;width:60px;height:60px;border-radius:50%;background:#1B2A4A;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.3);z-index:99999;transition:transform 0.2s;';
  btn.onmouseover = function() { btn.style.transform = 'scale(1.1)'; };
  btn.onmouseout = function() { btn.style.transform = 'scale(1)'; };

  // Create iframe container
  var container = document.createElement('div');
  container.id = 'mn-widget-container';
  container.style.cssText = 'position:fixed;bottom:90px;right:20px;width:400px;height:600px;border-radius:16px;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.2);z-index:99998;display:none;';

  var iframe = document.createElement('iframe');
  iframe.src = WIDGET_URL || '/';
  iframe.style.cssText = 'width:100%;height:100%;border:none;';
  container.appendChild(iframe);

  var open = false;
  btn.onclick = function() {
    open = !open;
    container.style.display = open ? 'block' : 'none';
    btn.innerHTML = open
      ? '<svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>'
      : '<svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>';
  };

  document.body.appendChild(container);
  document.body.appendChild(btn);
})();
