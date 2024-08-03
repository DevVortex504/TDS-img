import os
from django.shortcuts import render
from django.contrib import messages
from PIL import Image
import io
import base64

key = 2108
# Create your views here.
def rgb_to_tds(r, g, b):
    r = int(r) ^ key
    g = int(g) ^ key
    b = int(b) ^ key
    return f"T{r}D{g}S{b}"

def jpg_to_tds(img):
    rgb_img = img.convert('RGB')
    width, height = rgb_img.size
    tds_data = []
    for y in range(height):
        for x in range(width):
            r, g, b = rgb_img.getpixel((x, y))
            tds_data.append(rgb_to_tds(r, g, b))
    return width, height, tds_data


def display_tds(tds_content):
    lines = tds_content.strip().split('\n')
    width, height = map(int, lines[0].split())
    tds_data = lines[1:]

    img = Image.new('RGB', (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            tds = tds_data[y * width + x]
            r = int(tds[1:tds.index('D')]) ^ key
            g = int(tds[tds.index('D')+1:tds.index('S')]) ^ key
            b = int(tds[tds.index('S')+1:]) ^ key
            pixels[x, y] = (r, g, b)
    return img

def index(request):
    messages.info(request, 'Keep jpg image size below 1MB')
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        file_extension = os.path.splitext(image_file.name)[1].lower()
        if file_extension == ".tds":
            tds_content = image_file.read().decode('utf-8')
            img = display_tds(tds_content)
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            return render(request, 'converter/index.html', {
                "img": f"data:image/png;base64,{img_base64}",
                'jpg_filename': f"{os.path.splitext(image_file.name)[0]}.jpg",
                'jpg_base64': img_base64,
            })
        else:
            try:
                img = Image.open(image_file)
                img = img.convert('RGB')
            except:
                messages.warning(request, 'Invalid image file')
            width, height, tds_data = jpg_to_tds(img)
            tds_content = f"{width} {height}\n" + '\n'.join(tds_data)
            tds_filename = f"{image_file.name.split('.')[0]}.tds"
            tds_base64 = base64.b64encode(tds_content.encode()).decode()
            messages.success(request, 'Image converted successfully')
            return render(request, 'converter/index.html', {
                'tds_filename': tds_filename,
                'tds_base64': tds_base64
            })
    return render(request, 'converter/index.html')
