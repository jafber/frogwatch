const dynDns = 'https://gist.githubusercontent.com/CheeseCrustery/a80945ec5a6d0dfa8e067b0f9849d71c/raw/ipv4.txt'
const localDomain = '192.168.178.102'
const wsTimeoutS = 10
let apiDomain = null
let socket = null
let checkTask = null

async function getApiDomain() {
	try {
		// https://stackoverflow.com/questions/46946380/fetch-api-request-timeout
		let localRes = await fetch('http://' + localDomain, { signal: AbortSignal.timeout(500) })
		if (localRes.ok) {
			console.log('local request worked, using domain ' + localDomain)
			return localDomain
		} else {
			console.log('local request HTTP error', localRes.statusText)
			throw localRes.statusText
		}
	} catch (err) {
		console.log('local request failed, fetching dyndns')
		let dnsRes = await fetch(dynDns)
		if (dnsRes.ok) {
			let text = await dnsRes.text()
			console.log('got dynDns ip ', text.trim())
			return text.trim()
		} else {
			console.log('dynDns request HTTP error', dynDns.statusText)
			throw dynDns.statusText
		}
	}
}

function setupWebsocket(url, canvas, playButton) {

	// close old socket
	const context = canvas.getContext('2d')
	//context.rotate(Math.PI / 2)
	const cleanUp = () => {
		if (socket) socket.close()
		if (checkTask) clearInterval(checkTask)
		playButton.hidden = false
		context.clearRect(0, 0, canvas.width, canvas.height)
	}
	cleanUp()
	
	// start websocket ping-pong
	socket = new WebSocket(url)
	playButton.hidden = true
	socket.addEventListener('open', function () {
		socket.send('');
	})
	
	// refresh canvas image with each incoming message
	let lastRefresh = [new Date()]
	socket.addEventListener('message', async function (event) {
		lastRefresh[0] = new Date()
		const blob = event.data
		const bitmap = await createImageBitmap(blob)
		context.drawImage(bitmap, 0, 0)
		socket.send('')
	})

	// check if connection is still alive
	checkTask = setInterval(() => {
		if (new Date() - lastRefresh[0] >= wsTimeoutS * 1000) cleanUp()
	}, wsTimeoutS * 1000)
}

async function reloadStream() {
	console.log('reloading stream')
	const apiDomain = await getApiDomain()
	if (apiDomain) {
		const wsUrl = 'ws://' + apiDomain + '/ws'
		const canvas = document.getElementById('output')
		const play = document.getElementById('playbutton')
		console.log('starting websocket ' + wsUrl)
		setupWebsocket(wsUrl, canvas, play)
	}
}

function resizeCanvas(canvas) {
	// calculate h and w so canvas covers the container
	const ratio = 16 / 9
	let pw = canvas.parentElement.offsetWidth
	let ph = canvas.parentElement.offsetHeight
	if (ph / pw >= 16 / 9) {
		// container is too high
		var h = ph
		var w = ph / ratio
	} else {
		// container is too wide
		var w = pw
		var h = pw * ratio
	}
	
	// set canvas style
	canvas.style.transform = 'rotate(-90deg)'
	canvas.style.width = h + 'px'
	canvas.style.height = w + 'px'
}

function saveImage() {

}

window.onload = () => {
	resizeCanvas(document.getElementById('output'))

	// pwa
	console.log('checking service worker', 'serviceWorker' in navigator)
	if ('serviceWorker' in navigator) {
		navigator.serviceWorker.register('/sw.js')
		console.log('service worker registered')
	}

}

window.onresize = () => { resizeCanvas(document.getElementById('output')) }
