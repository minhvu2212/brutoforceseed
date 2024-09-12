import tkinter as tk
from PIL import Image, ImageDraw

def create_gradient_image(width, height, color_start, color_end):
    # Tạo một hình ảnh mới với kích thước và màu sắc ban đầu
    img = Image.new('RGB', (width, height), color_start)
    draw = ImageDraw.Draw(img)

    # Vẽ gradient từ màu bắt đầu đến màu kết thúc
    for i in range(height):
        # Tính toán màu cho dòng hiện tại dựa trên gradient
        r = int(color_start[0] + (color_end[0] - color_start[0]) * i / height)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * i / height)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * i / height)
        draw.line((0, i, width, i), fill=(r, g, b))

    return img

# Kích thước của hình ảnh gradient
width = 900
height = 500

# Màu bắt đầu và kết thúc cho gradient
color_start = (17, 45, 96)  # RGB của màu "#112D60"
color_end = (221, 131, 224)  # RGB của màu "#DD83E0"

# Tạo hình ảnh gradient
gradient_img = create_gradient_image(width, height, color_start, color_end)

# Lưu hình ảnh gradient vào một tệp hình ảnh
gradient_img.save("gradient_background.png")

root = tk.Tk()

# Sử dụng hình ảnh gradient như một hình ảnh nền cho root
background_image = tk.PhotoImage(file="gradient_background.png")
label = tk.Label(root, image=background_image)
label.place(x=0, y=0, relwidth=1, relheight=1)

# Cài đặt kích thước cửa sổ
root.geometry("900x500")

root.mainloop()
