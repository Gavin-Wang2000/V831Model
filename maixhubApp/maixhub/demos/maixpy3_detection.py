from maix import nn, camera, display, image
from maixhub.trans import tr

class YOLOv2:
    def __init__(self, model_path, labels, anchors, net_in_size, net_out_size):
        self.labels = labels
        self.anchors = anchors
        self.net_in_size = net_in_size
        self.net_out_size = net_out_size
        print("-- load yolo model:", model_path)
        import os
        pwd = os.getcwd()
        os.chdir(os.path.dirname(model_path))
        self.model = nn.load(os.path.basename(model_path))
        if not self.model:
            raise Exception("Load model failed")
        os.chdir(pwd)
        print("-- load ok")
        print("-- init yolo2 decoder")
        self._decoder = nn.decoder.Yolo2(len(labels), anchors, net_in_size=net_in_size, net_out_size=net_out_size)
        print("-- init complete")
        self.first = True

    def run(self, img, nms=0.3, threshold=0.5, disp_size = (224, 224)):
        out = self.model.forward(img.resize(size=self.net_in_size), layout="hwc")
        boxes, probs = self._decoder.run(out, nms=nms, threshold=threshold, img_size=disp_size)
        if self.first and len(boxes) > 0:
            self.first = False
        return boxes, probs

    def draw(self, img, boxes, probs):
        if self.first:
            msg = tr("Aim to object to detect")
            w, h = image.get_string_size(msg, scale=1.2, thickness=2)
            img.draw_string((img.width - w) // 2, img.height // 2 - h // 2, msg, scale = 1.2, color = (255, 255, 255), thickness = 2)
            return img
        for i, box in enumerate(boxes):
            class_id = probs[i][0]
            prob = probs[i][1][class_id]
            msg = "{}:{:.2f}%".format(self.labels[class_id], prob*100)
            img.draw_rectangle(box[0], box[1], box[0] + box[2], box[1] + box[3], color=(255, 255, 255), thickness=2)
            img.draw_string(box[0] + 2, box[1] + 2, msg, scale = 1.2, color = (255, 255, 255), thickness = 2)
        return img

    def __del__(self):
        del self.model
        del self._decoder

class Demo:
    def __init__(self, model_path, info):
        self.labels = info["labels"]
        self.anchors = info["anchors"]
        input_name = list(info["inputs"].keys())[0]
        h, w, c = info["inputs"][input_name]
        input_size = (w, h)
        self.input_size = input_size
        self.model_path = model_path

    def init(self):
        # camera.config(size=self.input_size)
        self.yolov2 = YOLOv2(self.model_path, self.labels, self.anchors, self.input_size, (self.input_size[0] // 32, self.input_size[1] // 32))

    def loop(self, img, dis_img, key):
        boxes, probs = self.yolov2.run(img, nms=0.3, threshold=0.5, disp_size = (dis_img.width, dis_img.height))
        self.yolov2.draw(dis_img, boxes, probs)

