import asyncio
import websockets
import pathlib

async def main(imgpath):
    # get all paths to images
    image_paths = []
    for path in imgpath.iterdir():
        if path.is_file():
            image_paths.append(path)
    
    # read images in correct order
    images = []
    for path in sorted(image_paths):
        print(f'reading {path}')
        with open(path, 'rb') as file:
            images.append(file.read())
    
    # connect to server and keep sending image loop
    async with websockets.connect('ws://localhost:8001/raspi') as socket:
        try:
            i = 0
            while True:
                await asyncio.sleep(1.0)
                print(f'sending image {i}')
                await socket.send(images[i])
                i = (i + 1) % len(images)
        finally:
            print('connection closed')
            return

asyncio.run(main(pathlib.Path('three/')))
