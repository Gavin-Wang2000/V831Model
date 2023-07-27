import os, json
from . import maixpy3_classification, maixpy3_detection

codes = {
    "classification": maixpy3_classification,
    "detection": maixpy3_detection,
}

def load_model_info(model_dir, init_model = True):
    '''
        @model_dir model files dir, should include report.json
        @return model_dir, report_info:dict, code_object
    '''
    model_path = None
    files = os.listdir(model_dir)
    for name in files:
        if name.endswith(".mud"):
            model_path = os.path.join(model_dir, name)
    if not model_path:
        return None, "No mud file found", None
    report = os.path.join(model_dir, "report.json")
    with open(report, "r") as f:
        report = json.load(f)
    if not report["label_type"] in codes:
        print(f'{report["label_type"]} not supported')
        return None, "", None
    try:
        obj = codes[report["label_type"]].Demo(model_path, report)
        if init_model:
            obj.init()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, "Load error", None
    return [model_path, report, obj]

