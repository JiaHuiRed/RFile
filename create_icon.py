"""生成 RFile 应用图标 icon.ico（多尺寸 Windows ICO）"""
from PIL import Image, ImageDraw, ImageFont

FONT_PATHS = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/seguisb.ttf",
]

def _font(size):
    for fp in FONT_PATHS:
        try: return ImageFont.truetype(fp, size)
        except: pass
    return ImageFont.load_default()

def make_frame(size):
    # 渐变背景
    bg = Image.new("RGBA", (size, size))
    bd = ImageDraw.Draw(bg)
    c1 = (0x2d, 0x5b, 0xe3)   # 顶部: 亮蓝
    c2 = (0x0e, 0x1a, 0x5e)   # 底部: 深海蓝
    for y in range(size):
        t = y / max(1, size - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        bd.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # 圆角遮罩
    rad = max(3, size // 5)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size-1, size-1], radius=rad, fill=255)
    bg.putalpha(mask)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img.alpha_composite(bg)
    d = ImageDraw.Draw(img)

    # 文件夹轮廓（size >= 48，半透明白色衬底）
    if size >= 48:
        fw = int(size * 0.62)
        fh = int(size * 0.44)
        fx = int(size * 0.19)
        fy = int(size * 0.30)
        th = max(2, size // 12)
        tw = int(fw * 0.42)
        fo = 28
        d.rounded_rectangle([fx, fy - th, fx + tw, fy + 2],
                            radius=max(1, th // 2), fill=(255, 255, 255, fo))
        d.rounded_rectangle([fx, fy, fx + fw, fy + fh],
                            radius=max(2, size // 16), fill=(255, 255, 255, fo))

    # 大写 R（白色居中，带轻阴影）
    rs = int(size * 0.58)
    font = _font(rs)
    bbox = d.textbbox((0, 0), "R", font=font)
    tx = (size - (bbox[2] - bbox[0])) // 2 - bbox[0]
    ty = (size - (bbox[3] - bbox[1])) // 2 - bbox[1]
    if size >= 64:
        off = max(1, size // 64)
        d.text((tx + off, ty + off), "R", fill=(0, 0, 0, 60), font=font)
    d.text((tx, ty), "R", fill=(255, 255, 255, 255), font=font)

    return img


if __name__ == "__main__":
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [make_frame(s) for s in sizes]
    frames[-1].save(
        "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[:-1],
    )
    print(f"icon.ico 已生成，包含尺寸: {sizes}")
