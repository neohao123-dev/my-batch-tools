#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成批量重命名工具的图标
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """创建应用图标"""
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 绘制圆角矩形背景
    def rounded_rectangle(draw, xy, radius, fill):
        x1, y1, x2, y2 = xy
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
        draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=fill)
        draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=fill)
        draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=fill)
        draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=fill)

    # 背景 - 深蓝色圆角矩形
    rounded_rectangle(draw, [10, 10, 246, 246], 30, (41, 128, 185))

    # 绘制白色文件夹
    folder_x, folder_y = 45, 55
    folder_w, folder_h = 166, 140

    # 文件夹背面
    draw.rectangle(
        [folder_x, folder_y + 25, folder_x + folder_w, folder_y + folder_h],
        fill=(236, 240, 241)
    )

    # 文件夹顶部标签
    draw.rectangle(
        [folder_x, folder_y, folder_x + 75, folder_y + 35],
        fill=(189, 195, 199)
    )
    draw.rectangle(
        [folder_x + 5, folder_y + 5, folder_x + 70, folder_y + 30],
        fill=(236, 240, 241)
    )

    # 绘制重命名箭头和文字
    draw.rectangle([65, 100, 105, 150], fill=(52, 152, 219))
    draw.rectangle([70, 95, 100, 100], fill=(41, 128, 185))

    draw.line([(120, 125), (155, 125)], fill=(46, 204, 113), width=5)
    draw.polygon([(155, 115), (175, 125), (155, 135)], fill=(46, 204, 113))

    draw.rectangle([160, 100, 200, 150], fill=(231, 76, 60))
    draw.rectangle([165, 95, 195, 100], fill=(192, 57, 43))

    for i in range(3):
        y = 115 + i * 12
        draw.line([(70, y), (100, y)], fill=(255, 255, 255, 200), width=2)
        draw.line([(165, y), (195, y)], fill=(255, 255, 255, 200), width=2)

    draw.rectangle([45, 170, 211, 210], fill=(52, 73, 94))

    try:
        font = ImageFont.truetype("msyh.ttc", 22)
    except:
        try:
            font = ImageFont.truetype("simhei.ttf", 22)
        except:
            font = ImageFont.load_default()

    draw.text((65, 175), "批量重命名", fill=(255, 255, 255), font=font)

    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")

    icons = []
    for s in icon_sizes:
        resized = img.resize(s, Image.Resampling.LANCZOS)
        icons.append(resized)

    icons[0].save(
        icon_path,
        format='ICO',
        sizes=[(s.width, s.height) for s in icons],
        append_images=icons[1:]
    )

    print(f"图标已生成: {icon_path}")
    return icon_path

if __name__ == "__main__":
    create_icon()
