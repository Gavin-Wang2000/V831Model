#检测示例代码

from maix import nn, camera, image, display
from maix.nn import decoder
import time
import serial
import struct

ser = serial.Serial("/dev/ttyS1",115200)    # 连接串口1
ser.write(b"Hello Wrold !!!\n")
def sendData(class_id,x,y):
    # ser.write((f"0x5b,0x3c{class_id}\r\n").encode("gbk"))
    load_data = struct.pack(">BBBBB", 0x5b, 0x3c, class_id, x, y)
    ser.write(load_data)

model = {
    "param": "/root/model_awnn.param",
    "bin": "/root/model_awnn.bin"
}
options = {
    "model_type":  "awnn",
    "inputs": {
        "input0": (224, 224, 3)
    },
    "outputs": {
        "output0": (7, 7, (1+4+2)*5)    #输出参数修改,修改格式 (7 ,7 , (1 + 4 + "类别数量" ) * 5)
    },
    "mean": [127.5, 127.5, 127.5],
    "norm": [0.0078125, 0.0078125, 0.0078125],
}

labels = ["usb","aigo"]            #分类标签
anchors = [1.19, 1.98, 2.79, 4.59, 4.53, 8.92, 8.06, 5.29, 10.32, 10.65]

m = nn.load(model, opt=options)
yolo2_decoder = decoder.Yolo2(len(labels), anchors, net_in_size=(options["inputs"]["input0"][0], options["inputs"]["input0"][1]), net_out_size=(7, 7))

while True:
    img = camera.capture()
    AI_img = img.copy().resize(224, 224)
    out = m.forward(AI_img.tobytes(), quantize=True, layout="hwc")
    boxes, probs = yolo2_decoder.run(out, nms=0.3, threshold=0.3, img_size=(options["inputs"]["input0"][0], options["inputs"]["input0"][1]))

    if len(boxes):
        for i, box in enumerate(boxes):
            class_id = probs[i][0]
            prob = probs[i][1][class_id]
            disp_str = "{}:{:.2f}%".format(labels[class_id], prob*100)
            img.draw_rectangle(box[0], box[1], box[0] + box[2], box[1] + box[3], color = (255, 255, 255))
            sendData(class_id, box[0], box[1])
            x = box[0]
            y = box[1] - 20
            if y < 0:
                y = 0
            img.draw_string(x, y, disp_str, color = (255, 255, 255))

    display.show(img)


