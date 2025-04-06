const STREAM_URL = 'wss://frogwatch.jan-berndt.de/ws/front'
const WS_TIMEOUT_S = 5
const VIDEO_WIDTH = 1640
const VIDEO_HEIGHT = 1232
const MESSAGE_TYPE = {
    open: 'auth',
    getImage: 'get_image',
}

// get a byte representing the XOR of all the blob's bytes
async function blobHash(imageBlob) {
    let hash = 0
    if (!imageBlob) return hash
    const binArray = await imageBlob.arrayBuffer()
    const view = new DataView(binArray)
    for (let i = 0; i < view.byteLength; i++) {
        hash ^= view.getUint8(i)
    }
    return hash
}

// use websocket to send a message
async function sendMessage(webSocket, msgType, currentImageBlob = null) {
    let msg = {
        type: msgType,
    }
    switch(msgType) {
        case (MESSAGE_TYPE.open):
            msg['session'] = crypto.randomUUID()
            break
        case (MESSAGE_TYPE.getImage):
            msg['current_hash'] = await blobHash(currentImageBlob)
            break
        default:
            throw 'wrong message type'
    }
    await webSocket.send(JSON.stringify(msg))
}

// draw a landscape 1640x1232 jpeg blob onto the canvas
async function drawBlob(image, canvas) {
    const bitmap = await createImageBitmap(image)
    const context = canvas.getContext('2d')
    context.drawImage(bitmap,
                      0, // dx
                      0, // dy
                      bitmap.width, // dWidth
                      bitmap.height // dHeight
                      )
}

// adjust canvas size and overflow direction depending on device aspect ratio
function setCanvasBehavior(canvas) {
    const container = canvas.parentElement
    const videoWidthRatio = VIDEO_WIDTH / VIDEO_HEIGHT
    const containerWidthRatio = container.offsetWidth / container.offsetHeight
    if (containerWidthRatio > videoWidthRatio) {
        // container is wider than video, scroll video top to bottom
        canvas.style.height = 'initial'
        canvas.style.width = '100%'
        container.style.overflowX = 'clip'
        container.style.overflowY = 'scroll'
    } else {
        // container is narrower than video, scroll video left to right
        canvas.style.height = '100%'
        canvas.style.width = 'initial'
        container.style.overflowX = 'scroll'
        container.style.overflowY = 'clip'
    }
}

// open dialog to save the current image
function saveImage(imageBlob) {
    // https://stackoverflow.com/a/25911218/10666216
    if (!imageBlob) return
    const blobUrl = URL.createObjectURL(imageBlob);
    let link = document.createElement("a")
    link.href = blobUrl
    link.download = `frosch-${new Date().toISOString()}.jpg`
    link.click()
}

// init and maintain websocket connection to the backend image stream
function setupWebsocket(onMessage, onClose) {
    console.log('setting up websocket to ' + STREAM_URL)
    // tell backend to start sending
    const webSocket = new WebSocket(STREAM_URL)
    webSocket.addEventListener('open', async function () {
        await sendMessage(webSocket, MESSAGE_TYPE.open)
        await sendMessage(webSocket, MESSAGE_TYPE.getImage)
    })

    // listen for incoming messages
    let lastRefresh = new Date()
    webSocket.addEventListener('message', async function (event) {
        lastRefresh = new Date()
        await onMessage(event.data)
        await sendMessage(webSocket, MESSAGE_TYPE.getImage, event.data)
    })

    // check if stream is still alive
    const timeout = WS_TIMEOUT_S * 1000
    const checkTask = setInterval(() => {
        if (new Date() - lastRefresh >= timeout) {
            webSocket.close()
            clearInterval(checkTask)
        }
    }, timeout)
    webSocket.addEventListener('close', onClose)
}

// when site loads or play button is pressed, attempt to start the video
function startVideo(playButton, canvas) {
    playButton.hidden = true
    const handleClose = () => {
        console.log('websocket closed')
        playButton.hidden = false
        canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height)
    }
    const output = {}
    setupWebsocket(async (imageBlob) => {
        output.currentImage = imageBlob
        await drawBlob(imageBlob, canvas)
    }, handleClose)
    return output
}

// main
window.addEventListener('load', async () => {
    // init canvas
    const canvas = document.getElementById('output')
    setCanvasBehavior(canvas)
    window.addEventListener('resize', () => setCanvasBehavior(canvas))

    // start the websocket stream
    const playButton = document.getElementById('playbutton')
    let video = startVideo(playButton, canvas)
    playButton.addEventListener('click', () => {
        video = startVideo(playButton, canvas)
    })

    // hydrate photo button
    const photoButton = document.getElementById('photobutton')
    photoButton.addEventListener('click', () => saveImage(video.currentImage))
})
