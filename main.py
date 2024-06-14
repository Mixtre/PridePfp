from flask import Flask, request, send_file, jsonify, render_template
from PIL import Image, ImageDraw
import numpy as np
import io

app = Flask(__name__)

flags = {
    "lgbtq": ["#E40303", "#FF8C00", "#FFED00", "#008026", "#24408E", "#732982"],
    "transgender": ["#55CDFC", "#F7A8B8", "#FFFFFF", "#F7A8B8", "#55CDFC"],
    "bisexual": ["#D60270", "#9B4F96", "#0038A8"],
    "pansexual": ["#FF1B8D", "#FFD700", "#1BB3FF"],
    "asexual": ["#000000", "#A3A3A3", "#FFFFFF", "#800080"],
    "nonbinary": ["#FFF430", "#FFFFFF", "#9C59D1", "#000000"],
    "genderfluid": ["#FF75A2", "#FFFFFF", "#BE18D6", "#000000", "#333EBD"],
    "genderqueer": ["#B57EDC", "#FFFFFF", "#4A8123"],
    "agender": ["#000000", "#B9B9B9", "#FFFFFF", "#B9B9B9", "#000000"],
    "demisexual": ["#4A4A4A", "#A4A4A4", "#FFFFFF", "#A4A4A4", "#4A4A4A", "#5C2D91"],
    "intersex": ["#FFD800", "#7902AA"],
    "progress": ["#E40303", "#FF8C00", "#FFED00", "#008026", "#24408E", "#732982", "#75D7D3", "#AF42A6", "#FFFFFE", "#000000", "#613915"]
}

def add_flag_border(image_file, border_size=20, mode="static", orientation="horizontal", colors=None):
    color_tuples = [(int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)) for color in colors]

    img = Image.open(image_file).convert("RGBA")
    img_width, img_height = img.size

    temp_border_size = border_size + 3
    new_size = (img_width + 2 * temp_border_size, img_height + 2 * temp_border_size)
    new_img = Image.new("RGBA", new_size, (0, 0, 0, 0))

    if mode == "static":
        draw = ImageDraw.Draw(new_img)
        stripe_size = new_size[0] // len(colors) if orientation == "vertical" else new_size[1] // len(colors)
        for i, color in enumerate(colors):
            if orientation == "horizontal":
                draw.rectangle([0, i * stripe_size, new_size[0], (i + 1) * stripe_size], fill=color)
            else:
                draw.rectangle([i * stripe_size, 0, (i + 1) * stripe_size, new_size[1]], fill=color)
        if orientation == "horizontal":
            draw.rectangle([0, len(colors) * stripe_size, new_size[0], new_size[1]], fill=colors[-1])
        else:
            draw.rectangle([len(colors) * stripe_size, 0, new_size[0], new_size[1]], fill=colors[-1])
    elif mode == "gradient":
        gradient = np.zeros((new_size[1], new_size[0], 3), dtype=np.uint8)
        total_size = new_size[0] if orientation == "vertical" else new_size[1]
        stripe_size = total_size // (len(color_tuples) - 1)
        
        for i in range(len(color_tuples) - 1):
            start_color = np.array(color_tuples[i])
            end_color = np.array(color_tuples[i + 1])
            for j in range(stripe_size):
                ratio = j / stripe_size
                color = tuple(int(start_color[k] * (1 - ratio) + end_color[k] * ratio) for k in range(3))
                if orientation == "horizontal":
                    gradient[i * stripe_size + j, :] = color
                else:
                    gradient[:, i * stripe_size + j] = color

        remaining_size = total_size - (len(color_tuples) - 1) * stripe_size
        if remaining_size > 0:
            start_color = np.array(color_tuples[-2])
            end_color = np.array(color_tuples[-1])
            for j in range(remaining_size):
                ratio = j / remaining_size
                color = tuple(int(start_color[k] * (1 - ratio) + end_color[k] * ratio) for k in range(3))
                if orientation == "horizontal":
                    gradient[(len(color_tuples) - 1) * stripe_size + j, :] = color
                else:
                    gradient[:, (len(color_tuples) - 1) * stripe_size + j] = color

        gradient_img = Image.fromarray(gradient, 'RGB')
        new_img.paste(gradient_img, (0, 0))

    mask = Image.new("L", new_size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((temp_border_size, temp_border_size, new_size[0] - temp_border_size, new_size[1] - temp_border_size), fill=255)
    flag_with_mask = Image.new("RGBA", new_size)
    flag_with_mask.paste(new_img, (0, 0), mask)
    new_img.paste(img, (temp_border_size, temp_border_size), img)
    final_img = Image.alpha_composite(flag_with_mask, new_img)

    cropped_img = final_img.crop((2, 2, new_size[0] - 4, new_size[1] - 4))
    output = io.BytesIO()
    cropped_img.save(output, format='PNG')
    output.seek(0)
    return output

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        image_file = request.files['image']
        flag = request.form['flag']
        border_size = int(request.form['border_size'])
        mode = request.form['mode']
        orientation = request.form['orientation']
        
        if flag in flags:
            colors = flags[flag]
            output = add_flag_border(image_file, border_size, mode, orientation, colors)
            return send_file(output, mimetype='image/png', as_attachment=True, download_name='output.png')
    
    return render_template('index.html', flags=flags)

if __name__ == '__main__':
    app.run(debug=True)
