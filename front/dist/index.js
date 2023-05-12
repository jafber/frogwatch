const dynDns = 'https://gist.githubusercontent.com/CheeseCrustery/a80945ec5a6d0dfa8e067b0f9849d71c/raw/ipv4.txt'
const localDomain = 'localhost:8001'
const wsTimeoutS = 10
const imageSensorWidth = 3280
const imageSensorHeight = 2464

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

async function drawBlob(blob, canvas) {
	const bitmap = await createImageBitmap(blob)
	const context = canvas.getContext('2d')
	context.drawImage(bitmap, 0, 0, bitmap.width, bitmap.height, 0, 0, canvas.width, canvas.height)
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
		await drawBlob(event.data, canvas)
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
	canvas.width = imageSensorWidth/2
	canvas.height = imageSensorHeight/2
	// calculate h and w so canvas covers the container
	const ratio = imageSensorWidth / imageSensorHeight
	let pw = canvas.parentElement.offsetWidth
	let ph = canvas.parentElement.offsetHeight
	if (ph / pw >= ratio) {
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

window.onload = async () => {
	const canvas = document.getElementById('output')
	resizeCanvas(canvas)

	// pwa
	console.log('checking service worker', 'serviceWorker' in navigator)
	if ('serviceWorker' in navigator) {
		navigator.serviceWorker.register('/sw.js')
		console.log('service worker registered')
	}
}

window.onresize = () => { resizeCanvas(document.getElementById('output')) }
