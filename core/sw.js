self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (_) { data = {body: event.data ? event.data.text() : ''}; }
  const title = data.title || 'د ادارې متحد سیستم';
  const options = {body: data.body || data.msg || 'نوې خبرتیا لرئ', icon: '/static/core/img/icon-192.png', badge: '/static/core/img/icon-192.png', data: {url: data.url || '/'}, tag: data.tag || 'agency-notification'};
  event.waitUntil(self.registration.showNotification(title, options));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = event.notification.data && event.notification.data.url || '/';
  event.waitUntil(clients.matchAll({type: 'window', includeUncontrolled: true}).then(list => {
    for (const client of list) { if ('focus' in client) { client.navigate(target); return client.focus(); } }
    return clients.openWindow(target);
  }));
});
