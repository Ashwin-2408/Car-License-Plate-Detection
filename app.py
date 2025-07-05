import streamlit as st
import cv2
import numpy as np
import os
import re
from ultralytics import YOLO
from PIL import Image
import easyocr
import shutil


model_dir = os.path.join(os.path.expanduser('~'), '.EasyOCR')


broken_zip = os.path.join(model_dir, 'craft_mlt_25k.zip')
if os.path.exists(broken_zip):
    os.remove(broken_zip)

if os.path.exists(model_dir):
    try:
        shutil.rmtree(model_dir)
    except Exception as e:
        print(f"Error removing EasyOCR model directory: {e}")


reader = easyocr.Reader(['en'], gpu=False)


model = YOLO("best.pt") 


st.title("🚘 License Plate Detector + OCR Reader (EasyOCR)")
st.write("Upload an image containing a license plate. The app will detect and extract the number.")


uploaded_file = st.file_uploader("📤 Upload Image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)

    
    os.makedirs("uploads", exist_ok=True)
    input_path = os.path.join("uploads", uploaded_file.name)
    cv2.imwrite(input_path, cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))

   
    results = model.predict(input_path, save=False, imgsz=640, conf=0.4)

    found_plate = False

    for r in results:
        boxes = r.boxes
        if len(boxes) == 0:
            st.warning("❌ No license plate detected.")
            break

        for box in boxes:
            found_plate = True

          
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = xyxy
            cropped = img_array[y1:y2, x1:x2]

            st.image(cropped, caption="🔍 Cropped License Plate", use_column_width=False)

        
            gray = cv2.cvtColor(cropped, cv2.COLOR_RGB2GRAY)

          
            h, w = gray.shape[:2]
            gray_center = gray[:, int(w * 0.1):int(w * 1.0)]

           
            ocr_results = reader.readtext(gray_center)

            ocr_text = ''
            if ocr_results:
                best_result = max(ocr_results, key=lambda x: x[2])  # highest confidence
                raw_text = best_result[1]
                ocr_text = re.sub(r'[^A-Z0-9]', '', raw_text.upper())

            annotated = img_array.copy()
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(annotated, ocr_text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

         
            st.image(annotated, caption=f"✅ Detected Plate Text: `{ocr_text}`", use_column_width=True)
            st.success(f"🔤 OCR Result: `{ocr_text}`")

    if not found_plate:
        st.info("Try a clearer image or different angle.")
