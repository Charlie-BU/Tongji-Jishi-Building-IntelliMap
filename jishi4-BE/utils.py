import asyncio
import aiohttp
import cv2
import numpy as np
import base64


async def sendPlantyOfData(ws=None, num=1):
    async with aiohttp.ClientSession() as session:  # 共享 session，减少开销
        tasks = [generate_random_binary_image(session, ws) for _ in range(int(num))]
        await asyncio.gather(*tasks)


def binary_to_base64(binary_data):
    return base64.b64encode(binary_data).decode("utf-8")


def base64_to_data_url(base64_str, mime_type="image/png"):
    return f"data:{mime_type};base64,{base64_str}"


def show_binary_image(binary_data):
    # 将二进制数据转换为 NumPy 数组
    image_array = np.frombuffer(binary_data, dtype=np.uint8)
    # 解码成 OpenCV 格式的图像
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    # 显示图片
    cv2.imshow("Binary Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


async def generate_random_binary_image(session, ws):
    async with session.get("https://picsum.photos/200") as response:
        binary_data = await response.read()
        base64_str = binary_to_base64(binary_data)
        data_url = base64_to_data_url(base64_str)
        await ws.async_send_to(ws.id, data_url)
        # return binary_data
