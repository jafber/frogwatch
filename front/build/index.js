const dynDns = 'https://gist.githubusercontent.com/CheeseCrustery/a80945ec5a6d0dfa8e067b0f9849d71c/raw/ca8e130b39603eddaafb1530bdec2a3e04fbd02a/ipv4.txt'
const localDomain = '192.168.178.102'
let apiDomain = null
let socket = null

async function getApiDomain() {
	try {
		let localReq = $.get({
			url: 'http://' + localDomain,
			timeout: 500
		})
		await localReq
		if (localReq.status < 400) {
			console.log('using local domain ' + localDomain)
			return localDomain
		} else {
			throw 'local url request failed with code ' + localReq.status
		}
	} catch (err) {
		console.log('local connection failed', err)
		let dnsReq = $.get(dynDns)
		let ip = await dnsReq
		if (dnsReq.status < 400) {
			console.log('got dynDns ip ' + ip)
			return ip
		}
	}
	console.log('could neither get local url or dynDns url')
	return null
}

function setupWebsocket(url, canvas) {

	// close old socket and create new
	if (socket) socket.close()
	socket = new WebSocket(url)

	socket.addEventListener('open', function () {
		socket.send('');
	});
	
	socket.addEventListener('message', async function (event) {
		const blob = event.data
		const bitmap = await createImageBitmap(blob)
		const context = canvas.getContext('2d')
		context.drawImage(bitmap, 0, 0)
		socket.send('')
	});
}

async function reloadStream(canvas) {
	console.log('reloading stream')
	apiDomain = await getApiDomain()
	if (apiDomain) {
		const wsUrl = 'ws://' + apiDomain + '/ws'
		console.log('starting websocket ' + wsUrl)
		setupWebsocket(wsUrl, canvas)
	}
}

function apiRequest(method, path) {
	if (apiUrl != null) {
		return $.ajax({
			method: method,
			url: apiUrl + path,
		})
	}
}

function saveImage() {

}

async function main() {

	// pwa
	if ('serviceWorker' in navigator) {
		navigator.serviceWorker.register('/sw.js')
	}
}

jQuery(main)
