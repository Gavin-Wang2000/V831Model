from maix import nn
from PIL import Image, ImageDraw, ImageFont
from maix import  display, camera
import time
from maix.nn import decoder
def draw_rectangle_with_title(draw, box, disp_str, bg_color=(255, 0, 0, 255), font_color=(255, 255, 255, 255)):
    # draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    font_w, font_h = font.getsize(disp_str)
    draw.rectangle((box[0], box[1], box[0] + box[2], box[1] + box[3]), fill=None, outline=bg_color, width=2)
    draw.rectangle((box[0], box[1] - font_h, box[0] + font_w, box[1]), fill=bg_color)
    draw.text((box[0], box[1] - font_h), disp_str, fill=font_color, font=font)
camera.config(size=(224, 224))
labels = ["1", "2", "3", "4", "5", "6", "7", "8"]
anchors = [2.44, 2.25, 5.03, 4.91, 3.5 , 3.53, 4.16, 3.94, 2.97, 2.84]
model = {
    "param": "/root/number_awnn.param",
    "bin": "/root/number_awnn.bin"
}
options = {
    "model_type":  "awnn",
    "inputs": {
        "input0": (224, 224, 3)
    },
    "outputs": {
        "output0": (7, 7, (1+4+len(labels))*5)
    },
    "mean": [127.5, 127.5, 127.5],
    "norm": [0.0078125, 0.0078125, 0.0078125],
}
print("-- load model:", model)
m = nn.load(model, opt=options)
print("-- load ok")
w = options["inputs"]["input0"][1]
h = options["inputs"]["input0"][0]
yolo2_decoder = decoder.Yolo2(len(labels), anchors, net_in_size=(w, h), net_out_size=(7, 7))
while 1:
    t = time.time()
    img = camera.capture()
    if not img:
        time.sleep(0.01)
        continue
    print("-- capture: ", time.time() - t )
    t = time.time()
    out = m.forward(img, quantize=True, layout="hwc")
    print("-- forward: ", time.time() - t )
    t = time.time()
    boxes, probs = yolo2_decoder.run(out, nms=0.3, threshold=0.5, img_size=(240, 240))
    print("-- decode: ", time.time() - t )
    t = time.time()
    for i, box in enumerate(boxes):
        class_id = probs[i][0]
        prob = probs[i][1][class_id]
        disp_str = "{}:{:.2f}%".format(labels[class_id], prob*100)
        draw_rectangle_with_title(display.get_draw(), box, disp_str)
    print("-- draw: ", time.time() - t )
    t = time.time()
    display.show()
    print("-- show: ", time.time() - t )


