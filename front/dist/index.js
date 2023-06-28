const backendUrl = 'wss://jan-berndt.de/frogcam/ws/front'
const wsTimeoutS = 10
const imageSensorWidth = 3280
const imageSensorHeight = 2464
const messageType = {
    open: 'auth',
    getImage: 'get_image',
}

let canvas = null
let playButton = null
let lastRefresh = new Date()
let socket = null
let checkTask = null
let currentImage = new Blob()

// get an XOR of all the bytes
async function blobHash() {
    let hash = 0
    let binArray = await currentImage.arrayBuffer()
    let view = new DataView(binArray)
    for (let i = 0; i < view.byteLength; i++) {
        hash ^= view.getUint8(i)
    }
    return hash
}

// use socket to send a message
async function send(msgType) {
    let msg = {
        type: msgType,
    }
    switch(msgType) {
        case (messageType.open):
            msg['session'] = crypto.randomUUID()
            break
        case (messageType.getImage):
            msg['current_hash'] = await blobHash()
            break
        default:
            throw 'wrong message type'
    }
    await socket.send(JSON.stringify(msg))
}

// draw a jpeg blob onto the canvas
async function drawBlob() {
    const bitmap = await createImageBitmap(currentImage)
    const context = canvas.getContext('2d')
    context.drawImage(bitmap, 0, 0, bitmap.width, bitmap.height, 0, 0, canvas.width, canvas.height)
}

// close old websocket and clear image
function cleanUp() {
    if (socket) socket.close()
    if (checkTask) clearInterval(checkTask)
    playButton.hidden = false
    canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height)
}

// create a new websocket
function setupWebsocket() {

    // close old socket
    cleanUp()

    // start websocket ping-pong
    socket = new WebSocket(backendUrl)
    playButton.hidden = true
    socket.addEventListener('open', function () {
        send(messageType.open)
        send(messageType.getImage)
    })
 
    // refresh canvas image with each incoming message
    lastRefresh = new Date()
    socket.addEventListener('message', async function (event) {
        lastRefresh = new Date()
        currentImage = event.data
        await drawBlob()
        send(messageType.getImage)
    })

    // check if connection is still alive
    checkTask = setInterval(() => {
        if (new Date() - lastRefresh >= wsTimeoutS * 1000) cleanUp()
    }, wsTimeoutS * 1000)
}

// transform the canvas so that the backends images of size imageSensorWidth*imageSensorHeight are displayed correctly
function resizeCanvas() {
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

// open dialog to save the current image
function saveImage() {
    // https://stackoverflow.com/a/25911218/10666216
    var blobUrl = URL.createObjectURL(currentImage);
    var link = document.createElement("a")
    link.href = blobUrl
    link.download = `frosch-${new Date().toISOString()}.jpg`
    link.click()
}

function turnServo(toRight) {

}

window.addEventListener('load', () => {
    canvas = document.getElementById('output')
    playButton = document.getElementById('playbutton')
    resizeCanvas()
    setupWebsocket()

    // register service worker for pwa
    // console.log('checking service worker', 'serviceWorker' in navigator)
    // if ('serviceWorker' in navigator) {
    //     navigator.serviceWorker.register('/sw.js')
    //     console.log('service worker registered')
    // }
})
window.addEventListener('resize', resizeCanvas)
