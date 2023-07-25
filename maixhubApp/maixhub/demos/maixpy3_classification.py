from maix import nn, camera, display, image


class Demo:
    def __init__(self, model_path, info):
        self.labels = info["labels"]
        input_name = list(info["inputs"].keys())[0]
        h, w, c = info["inputs"][input_name]
        input_size = (w, h)
        self.input_size = input_size
        self.model_path = model_path

    def init(self):
        # camera.config(size=self.input_size)
        print("-- load model:", self.model_path)
        import os
        pwd = os.getcwd()
        os.chdir(os.path.dirname(self.model_path))
        self.model = nn.load(os.path.basename(self.model_path))
        if not self.model:
            raise Exception("Load model failed")
        os.chdir(pwd)
        print("-- load ok")

    def loop(self, img, dis_img, key):
        out = self.model.forward(img.resize(size=self.input_size))
        out = nn.F.softmax(out)
        msg = "{:.2f}: {}".format(out.max(), self.labels[out.argmax()])
        h = image.get_string_size("A", scale = 2, thickness = 2)[1]
        dis_img.draw_string(2, dis_img.height - h - 10, msg, scale = 2, color = (255, 0, 0), thickness = 2)

    def __del__(self):
        del self.model
