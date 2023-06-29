import asyncio
import websockets
import pathlib

async def maintain_connection(url, images, delay_s):
    print('attempting connection...')
    try:
        async with websockets.connect(url) as socket:
            i = 0
            while True:
                await asyncio.sleep(delay_s)
                print(f'sending image {i}')
                await socket.send(images[i])
                i = (i + 1) % len(images)
    except asyncio.CancelledError:
        print('program cancelled')
        return False
    except:
        print('connection closed')
        return True

async def main(url, imgpath, delay_s):
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
    while True:
        if not await maintain_connection(url, images, delay_s):
            break
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main('wss://jan-berndt.de/frogcam/ws/raspi', pathlib.Path(__file__).parent / 'testimage', 0.1))
