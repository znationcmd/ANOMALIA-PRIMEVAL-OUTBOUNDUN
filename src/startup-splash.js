/* One-time artwork while the game boots, never persistent menu wallpaper. */
(function () {
  const splash = document.getElementById('launchSplash');
  if (!splash) return;
  const poster = splash.querySelector('img');
  // Fallback to the approved installed-game logo if the full poster has not
  // yet been bundled. Never keep a broken-image placeholder on the screen.
  poster?.addEventListener('error', () => {
    if (poster.dataset.fallback === '1') return;
    poster.dataset.fallback = '1';
    poster.src = '/prigimalia-logo.jpg';
  });
  const startTime = performance.now();
  const MIN_DISPLAY_MS = 1500;
  const MAX_DISPLAY_MS = 5500;
  let closing = false;
  let ready = false;
  const close = () => {
    if (closing) return;
    closing = true;
    splash.classList.add('prigimalia-splash-done');
    // Keep accessible HTML and menu clean after the short fade.
    splash.addEventListener('transitionend', () => splash.remove(), { once: true });
    setTimeout(() => splash.remove(), 700);
  };
  const whenReady = () => {
    if (ready) return;
    ready = true;
    const remaining = Math.max(0, MIN_DISPLAY_MS - (performance.now() - startTime));
    setTimeout(close, remaining);
  };
  // window load waits for the menu's module bundle and the poster image.
  window.addEventListener('load', whenReady, { once: true });
  // Never trap the player behind the splash if an asset fails to load.
  setTimeout(close, MAX_DISPLAY_MS);
})();
