import asyncio
import websockets
import pathlib
import sys

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
    except Exception as e:
        print('connection closed')
        print(f'An error occurred: {str(e)}')
        return True

async def main(url, imgpath, delay_s):
    # get all paths to images
    image_paths = []
    for path in imgpath.iterdir():
        if path.is_file() and path.suffix.lower() == '.jpg':
            image_paths.append(path)
    
    # read images in correct order
    image_paths.sort(key=lambda path: int(path.stem))
    images = []
    print('reading images...')
    for path in image_paths:
        # print(f'reading {path}')
        with open(path, 'rb') as file:
            images.append(file.read())
    
    # connect to server and keep sending image loop
    while True:
        if not await maintain_connection(url, images, delay_s):
            break
        await asyncio.sleep(5)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = 'ws://localhost:3000/'
    print(f'using url {url}')
    asyncio.run(main(
        url=url,
        imgpath=pathlib.Path(__file__).parent / 'frog', 
        delay_s=0.1))
