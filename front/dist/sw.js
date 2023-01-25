importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.4.1/workbox-sw.js')

workbox.routing.registerRoute(
	({url, sameOrigin}) => sameOrigin && !url.pathname.startsWith('/ws'),
	new workbox.strategies.StaleWhileRevalidate()
)
