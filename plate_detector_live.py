import time
import sys
from pathlib import Path
import cv2
import pytesseract
import onnx
import onnxruntime as onnxr
import numpy as np
import serial
from serial.tools import list_ports

from plate_format.plate_format_ar import is_valid_plate, normalize_plate_format

IMAGE_SIZE = 640
ONNX_PATH = "plate_detection.onnx"
AUTHORIZED_PLATES_PATH = Path(__file__).resolve().with_name("patentes_autorizadas.txt")
CONFIG_TESSERACT = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

INFERENCE_INTERVAL_SECONDS = 0.5
OCR_INTERVAL_SECONDS = 0.75
PLATE_REARM_SECONDS = 10
last_seen_plates = {}

clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8,8))


BAUDIOS = 115200
ESP32_USB_IDS = {
    (0x0403, 0x6001), 
    (0x10C4, 0xEA60),  
    (0x1A86, 0x7523),  
    (0x1A86, 0x55D4),  
    (0x303A, 0x1001),  
}


def find_esp32_port():
    candidates = [
        port for port in list_ports.comports()
        if (port.vid, port.pid) in ESP32_USB_IDS
    ]

    if len(candidates) == 1:
        return candidates[0].device

    if candidates:
        ports = ", ".join(port.device for port in candidates)
        print(f"Se encontraron varios puertos compatibles ({ports}); ESP32 no conectado")
    else:
        print("No se encontró un adaptador USB serie compatible con ESP32")

    return None

PUERTO_ESP32 = find_esp32_port()
esp32 = None

if PUERTO_ESP32 is not None:
    try:
        esp32 = serial.Serial(
            port=PUERTO_ESP32,
            baudrate=BAUDIOS,
            timeout=1
        )

        time.sleep(2)
        print(f"ESP32 conectado en {PUERTO_ESP32}")

    except serial.SerialException as error:
        print(f"No se pudo conectar al ESP32 en {PUERTO_ESP32}: {error}")


def enviar_barrera():
    if esp32 is not None and esp32.is_open:
        mensaje = "barrier up\n"
        esp32.write(mensaje.encode("utf-8"))

        print("Enviado al ESP32: barrier up")

    else:
        print("ESP32 no conectado")


onnx_model = onnx.load(ONNX_PATH)
onnx.checker.check_model(onnx_model)

session = onnxr.InferenceSession(ONNX_PATH)
input_name = session.get_inputs()[0].name
output_names = [out.name for out in session.get_outputs()]


def findIntersectionOverUnion(box1, box2):
    """Computes IoU between two boxes given as (cx, cy, w, h)."""
    box1_w, box1_h = box1[2]/2.0, box1[3]/2.0
    box2_w, box2_h = box2[2]/2.0, box2[3]/2.0

    b1_1, b1_2 = box1[0] - box1_w, box1[1] - box1_h
    b1_3, b1_4 = box1[0] + box1_w, box1[1] + box1_h
    b2_1, b2_2 = box2[0] - box2_w, box2[1] - box2_h
    b2_3, b2_4 = box2[0] + box2_w, box2[1] + box2_h

    x1, y1 = max(b1_1, b2_1), max(b1_2, b2_2)
    x2, y2 = min(b1_3, b2_3), min(b1_4, b2_4)

    intersect = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (b1_3 - b1_1) * (b1_4 - b1_2)
    area2 = (b2_3 - b2_1) * (b2_4 - b2_2)
    union = area1 + area2 - intersect

    return intersect / union if union > 0 else 0


def preprocess_plate(plate_crop):
    """Applies a set of preprocessing steps to enhance plate image for OCR: contrast enhancement, denoising, binarization, and deskewing."""
    gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
    gray = clahe.apply(gray)
    blur = cv2.bilateralFilter(gray, 11, 16, 16)
    thresh = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        13,
        2
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    return morph


def extract_valid_plate(plate_crop):
    """Runs OCR on the plate image and returns a valid Argentine plate string if found."""
    raw_text = pytesseract.image_to_string(
        preprocess_plate(plate_crop),
        config=CONFIG_TESSERACT
    )

    raw_text = raw_text.strip().replace("\n", " ").replace("\f", "")
    raw_text = ''.join(c for c in raw_text if c.isalnum() or c.isspace())

    if is_valid_plate(raw_text):
        return normalize_plate_format(raw_text)

    return None


def load_authorized_plates():
    """Loads valid authorized plates from the local text file."""
    authorized_plates = set()

    try:
        lines = AUTHORIZED_PLATES_PATH.read_text(
            encoding="utf-8"
        ).splitlines()

    except OSError as error:
        sys.stderr.write(
            f"Could not read {AUTHORIZED_PLATES_PATH}: {error}. Access denied.\n"
        )
        return authorized_plates

    for line_number, line in enumerate(lines, start=1):

        plate = line.partition("#")[0].strip()

        if not plate:
            continue

        if not is_valid_plate(plate):
            sys.stderr.write(
                f"Ignoring invalid plate on line {line_number}: {plate}\n"
            )
            continue

        authorized_plates.add(
            normalize_plate_format(plate)
        )

    return authorized_plates


def run_onnx_inference(frame):
    """Preprocesses frame and runs ONNX inference."""
    resized = cv2.resize(
        frame,
        (IMAGE_SIZE, IMAGE_SIZE)
    )

    input_tensor = resized.astype(np.float32) / 255.0
    input_tensor = np.transpose(
        input_tensor,
        (2, 0, 1)
    )

    input_tensor = np.expand_dims(
        input_tensor,
        axis=0
    )

    return session.run(
        output_names,
        {input_name: input_tensor}
    )


def postprocess_detections(outputs, conf_thres=0.25, iou_thres=0.7):
    """Filters detections using confidence and IoU thresholds."""
    detections = []

    for detection in outputs[0]:

        boxes = detection[:4, :]
        scores = detection[4:7, :]

        class_ids = np.argmax(
            scores,
            axis=0
        )

        confs = scores[
            class_ids,
            np.arange(scores.shape[1])
        ]

        valid = confs >= conf_thres
        indices = np.where(valid)[0]

        flags = np.zeros(len(indices))

        for i, idx in enumerate(indices):

            if flags[i]:
                continue

            box = boxes[:, idx]
            class_id = class_ids[idx]
            score = confs[idx]

            for j, idx2 in enumerate(indices):

                if idx2 < idx or class_ids[idx2] != class_id:
                    continue

                if findIntersectionOverUnion(
                    box,
                    boxes[:, idx2]
                ) >= iou_thres:

                    flags[j] = True

            detections.append({
                "bbox": box,
                "confidence": score,
                "class_id": class_id
            })

            flags[i] = True

    return detections


def extract_plate_box(frame, detection, x_scale, y_scale):
    """Extracts plate crop from frame based on detection."""
    x, y, w, h = detection["bbox"]

    x1 = int(
        (x - w / 2) * x_scale
    )

    y1 = int(
        (y - h / 2) * y_scale
    )

    x2 = int(
        (x + w / 2) * x_scale
    )

    y2 = int(
        (y + h / 2) * y_scale
    )

    if x2 - x1 < 60 or y2 - y1 < 20:
        return None, None

    return (
        x1,
        y1,
        x2,
        y2
    ), frame[y1:y2, x1:x2]


def display_camera_with_detection():

    authorized_plates = load_authorized_plates()

    cap = cv2.VideoCapture(0)

    last_inference_time = 0
    last_ocr_time = 0

    conf_thres, iou_thres = 0.25, 0.7

    x_scale = y_scale = None

    while True:

        ret, frame = cap.read()

        if not ret:
            time.sleep(0.1)
            continue

        if x_scale is None or y_scale is None:

            h, w = frame.shape[:2]

            x_scale = w / IMAGE_SIZE
            y_scale = h / IMAGE_SIZE

        now = time.monotonic()

        for plate, last_seen in list(last_seen_plates.items()):
            if now - last_seen >= PLATE_REARM_SECONDS:
                del last_seen_plates[plate]

        if now - last_inference_time >= INFERENCE_INTERVAL_SECONDS:
            last_inference_time = now

            outputs = run_onnx_inference(frame)

            detections = postprocess_detections(
                outputs,
                conf_thres,
                iou_thres
            )

            if now - last_ocr_time >= OCR_INTERVAL_SECONDS:
                for det in detections:

                    _, crop = extract_plate_box(
                        frame,
                        det,
                        x_scale,
                        y_scale
                    )

                    if crop is None or crop.size == 0:
                        continue

                    last_ocr_time = time.monotonic()
                    plate = extract_valid_plate(crop)

                    if plate:
                        now = time.monotonic()

                        if plate in last_seen_plates:
                            last_seen_plates[plate] = now
                            break

                        last_seen_plates[plate] = now
                        sys.stdout.write(
                            f"\n[{time.strftime('%H:%M:%S')}] "
                            f"License Plate: {plate}\n\n"
                        )

                        if plate in authorized_plates:

                            sys.stdout.write(
                                "barrier up\n"
                            )

                            enviar_barrera()

                        else:

                            sys.stdout.write(
                                "Acceso denegado\n"
                            )

                        sys.stdout.flush()

                    break

        cv2.imshow(
            "Camera",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.1)

    cap.release()

    cv2.destroyAllWindows()



    if esp32 is not None and esp32.is_open:
        esp32.close()


if __name__ == "__main__":
    display_camera_with_detection()
