"""Scanify — local-first smart document scanner built with Streamlit."""
from __future__ import annotations

import hashlib
import io
import base64
import uuid
from pathlib import Path

import numpy as np
import streamlit as st

import config
from components.batch_scanner import move_page
from components.corner_editor import corner_editor
from components.dashboard import metric_card
from components.history import format_timestamp
from components.settings import DEFAULTS, ENHANCEMENT_MODES
from components.sidebar import apply_styles, render_sidebar
from modules.database import delete_scan, initialize_database, list_scans, save_scan, scan_stats, update_ocr
from modules.document_detection import detect_document, visualize_boundary
from modules.image_enhancement import enhance_image
from modules.image_preprocessing import load_image
from modules.image_quality import assess_quality
from modules.ocr_engine import available_languages, extract_text, tesseract_available
from modules.pdf_generator import generate_pdf
from modules.perspective_transform import four_point_transform

st.set_page_config(page_title="Scanify · Smart Document Scanner", page_icon="▤", layout="wide", initial_sidebar_state="expanded")
apply_styles()
initialize_database(config.DATABASE_PATH)

for key, value in DEFAULTS.items():
    st.session_state.setdefault(f"setting_{key}", value)

if "nav_request" in st.session_state:
    st.session_state.navigation = st.session_state.pop("nav_request")
page = render_sidebar()


def page_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(f"<div class='hero'><div class='eyebrow'>{kicker}</div><h1 style='margin:5px 0 4px'>{title}</h1><div style='color:#75819a'>{subtitle}</div></div>", unsafe_allow_html=True)


def stored_image(image: np.ndarray, suffix: str = ".png") -> tuple[str, str]:
    name = f"{uuid.uuid4().hex}{suffix}"
    path = config.PROCESSED_DIR / name
    from PIL import Image
    Image.fromarray(image).save(path, format="PNG", optimize=True)
    return name, str(path)


def render_dashboard() -> None:
    stats = scan_stats(config.DATABASE_PATH)
    page_header("YOUR WORKSPACE", "Good work starts with a clear scan.", "Bring paper documents into your digital workflow in a few simple steps.")
    welcome, action = st.columns([3, 1])
    with welcome:
        st.markdown("### Turn every document into a perfect scan.")
        st.write("Upload a photo, let Scanify find the page, correct its perspective and export a clean, searchable-ready document.")
    with action:
        if st.button("＋  Start a new scan", type="primary", use_container_width=True):
            st.session_state.nav_request = "New Scan"
            st.rerun()
    m1, m2, m3 = st.columns(3)
    with m1: metric_card("Documents processed", stats["scans"])
    with m2: metric_card("Pages scanned", stats["pages"])
    with m3: metric_card("Local & private", "On-device")
    st.markdown("### Recent documents")
    recent = list_scans(config.DATABASE_PATH, limit=5)
    if recent:
        for item in recent:
            cols = st.columns([3, 1, 1, 1])
            cols[0].markdown(f"**{item['original_filename']}**  \n<span style='color:#75819a'>{format_timestamp(item['processed_at'])}</span>", unsafe_allow_html=True)
            cols[1].write(item["processing_mode"])
            cols[2].write(f"{item['page_count']} page(s)")
            if cols[3].button("Open", key=f"dash_open_{item['id']}"):
                st.session_state.nav_request = "Document History"
                st.session_state.history_query = item["original_filename"]
                st.rerun()
    else:
        st.info("Your saved scans will appear here. Start by uploading a document photo.")
    st.markdown("### Built for better documents")
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='soft-card'><b>Automatic page detection</b><p style='color:#75819a'>Find page edges with Canny edges, contours and polygon approximation.</p></div>", unsafe_allow_html=True)
    c2.markdown("<div class='soft-card'><b>Clean, readable output</b><p style='color:#75819a'>Correct perspective and tune grayscale, thresholding, denoising and contrast.</p></div>", unsafe_allow_html=True)
    c3.markdown("<div class='soft-card'><b>Local-first by design</b><p style='color:#75819a'>Images and history stay in local folders; no API key or cloud account required.</p></div>", unsafe_allow_html=True)


def render_new_scan() -> None:
    page_header("SCANNER", "New scan", "Upload a photo or image of a document. Scanify processes it locally on this device.")
    upload = st.file_uploader("Choose a document image", type=["jpg", "jpeg", "png"], help="JPEG or PNG · up to 20 MB", key="single_upload")
    if upload is None:
        st.markdown("<div class='soft-card'><b>For best results</b><p style='color:#75819a'>Place the document on a contrasting, flat surface, keep all four edges visible and avoid strong glare.</p></div>", unsafe_allow_html=True)
        return
    try:
        raw = upload.getvalue()
        fingerprint = hashlib.sha1(raw).hexdigest()[:10]
        image = load_image(raw)
    except (ValueError, OSError) as exc:
        st.error(str(exc))
        return
    found = detect_document(image)
    if found is None:
        st.warning("Automatic edge detection did not find a confident page boundary. You can manually set corners below, or process the full image.")
    else:
        st.success("Document boundary detected. Review the highlighted corners before processing.")
    left, right = st.columns([1.25, 1])
    with left:
        st.image(visualize_boundary(image, found), caption="Original · detected boundary", use_container_width=True)
    corners = found
    manual = st.checkbox("Adjust corners manually", key=f"manual_{fingerprint}")
    if manual:
        h, w = image.shape[:2]
        initial = found if found is not None else np.array([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]], dtype=np.float32)
        reset_key = f"corner_reset_{fingerprint}"
        revision = st.session_state.get(reset_key, 0)
        if st.button("Reset corners", key=f"reset_button_{fingerprint}"):
            st.session_state[reset_key] = revision + 1
            st.rerun()
        image_buffer = io.BytesIO()
        from PIL import Image
        Image.fromarray(image).save(image_buffer, format="PNG")
        default_normalized = (initial / np.array([max(1, w-1), max(1, h-1)])).tolist()
        value = corner_editor(base64.b64encode(image_buffer.getvalue()).decode("ascii"), w, h,
                              default_normalized, key=f"corners_{fingerprint}_{revision}")
        corners = np.asarray(value, dtype=np.float32) * np.array([w-1, h-1]) if value is not None else initial
        # Reject crossed, duplicate, or degenerate corner sets before perspective mapping.
        pts = np.round(corners).astype(np.int32)
        area = abs(float(cv2.contourArea(pts))) if len(np.unique(pts, axis=0)) == 4 else 0
        valid_corners = area > 500 and cv2.isContourConvex(pts.reshape(-1, 1, 2))
        if not valid_corners:
            st.error("These corners do not form a usable quadrilateral. Adjust the points before processing.")
        st.caption("Drag the numbered corner markers on the image to adjust the crop.")
    else:
        valid_corners = corners is not None
    mode_col, rect_col = st.columns([2, 1])
    mode = mode_col.selectbox("Enhancement mode", ENHANCEMENT_MODES, index=ENHANCEMENT_MODES.index(st.session_state.setting_mode))
    rectify = rect_col.checkbox("Correct perspective", value=found is not None or manual, help="Uncheck to keep the full camera frame.")
    controls, quality_col = st.columns([1.3, 1])
    with controls:
        brightness = st.slider("Brightness", -60, 60, 0)
        contrast = st.slider("Contrast", 0.5, 2.0, 1.0, 0.05)
        sharpness = st.slider("Sharpness", 0.0, 2.0, 0.0, 0.1)
        denoise = st.slider("Denoising strength", 0, 10, 0)
        shadow = st.checkbox("Reduce uneven shadows", value=False)
    with quality_col:
        report = assess_quality(image)
        st.markdown("<div class='soft-card'><b>Image quality · heuristic</b>", unsafe_allow_html=True)
        st.write(f"Resolution: {report['width']} × {report['height']}")
        st.write(f"Brightness: {report['brightness']:.0f}/255 · contrast: {report['contrast']:.0f}")
        st.write(f"Blur score: {report['blur_score']:.0f} · noise estimate: {report['noise_estimate']:.1f}")
        for suggestion in report["suggestions"]:
            st.caption("• " + suggestion)
        st.markdown("</div>", unsafe_allow_html=True)
    try:
        source = four_point_transform(image, corners) if rectify and corners is not None and (not manual or valid_corners) else image.copy()
        processed = enhance_image(source, mode, brightness=brightness, contrast=contrast, sharpness=sharpness, denoise=denoise, shadow_removal=shadow)
    except (ValueError, cv2.error, Exception) as exc:
        st.error(f"Could not process this image: {exc}")
        return
    with right:
        st.image(processed, caption="Live processed preview", use_container_width=True)
    st.markdown("### Export scan")
    from PIL import Image
    png_buffer = io.BytesIO()
    Image.fromarray(processed).save(png_buffer, format="PNG")
    pdf_bytes = generate_pdf([processed])
    base_name = Path(upload.name).stem[:80] or "scan"
    d1, d2, d3 = st.columns(3)
    d1.download_button("Download PNG", png_buffer.getvalue(), file_name=f"{base_name}_scan.png", mime="image/png", use_container_width=True)
    d2.download_button("Download PDF", pdf_bytes, file_name=f"{base_name}_scan.pdf", mime="application/pdf", use_container_width=True)
    if d3.button("Save to document history", type="primary", use_container_width=True, key=f"save_scan_{fingerprint}"):
        try:
            original_name = f"{uuid.uuid4().hex}{Path(upload.name).suffix.lower()}"
            original_path = config.ORIGINALS_DIR / original_name
            original_path.write_bytes(raw)
            generated, output_path = stored_image(processed)
            scan_id = save_scan(config.DATABASE_PATH, original_filename=upload.name, generated_filename=generated, processing_mode=mode, output_path=output_path, original_path=str(original_path))
            st.session_state.last_scan_id = scan_id
            st.success("Scan saved to local document history.")
        except OSError as exc:
            st.error(f"Could not save this scan: {exc}")


def render_batch() -> None:
    page_header("MULTI-PAGE WORKFLOW", "Batch scanning", "Process a set of document photos, review each page and export them as one PDF.")
    uploads = st.file_uploader("Choose multiple document images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="batch_upload")
    mode = st.selectbox("Enhancement mode for all pages", ENHANCEMENT_MODES, index=ENHANCEMENT_MODES.index(st.session_state.setting_mode), key="batch_mode")
    rectify = st.checkbox("Automatically correct detected page perspective", value=True, key="batch_rectify")
    if st.button("Process selected images", type="primary", disabled=not uploads, key="process_batch"):
        processed_pages, errors = [], []
        progress = st.progress(0, text="Preparing pages…")
        for index, file in enumerate(uploads):
            try:
                img = load_image(file.getvalue())
                corners = detect_document(img) if rectify else None
                scanned = four_point_transform(img, corners) if rectify and corners is not None else img
                result = enhance_image(scanned, mode)
                processed_pages.append({"name": file.name, "image": result, "mode": mode, "id": uuid.uuid4().hex})
            except Exception as exc:
                errors.append(f"{file.name}: {exc}")
            progress.progress((index + 1) / max(1, len(uploads)), text=f"Processed {index + 1} of {len(uploads)}")
        st.session_state.batch_pages = processed_pages
        st.session_state.batch_errors = errors
        if errors:
            for error in errors: st.warning(error)
        st.success(f"Ready: {len(processed_pages)} page(s) processed; {len(errors)} failed.")
    pages = st.session_state.get("batch_pages", [])
    for error in st.session_state.get("batch_errors", []):
        st.warning(error)
    if not pages:
        return
    st.caption(f"{len(pages)} page(s) · use the arrows to change order")
    for index, item in enumerate(pages):
        cols = st.columns([1.3, 2, .55, .55, .7])
        cols[0].image(item["image"], caption=f"Page {index + 1}", use_container_width=True)
        cols[1].markdown(f"**{item['name']}**  \n{item['mode']}")
        if cols[2].button("↑", key=f"up_{item['id']}", disabled=index == 0, help="Move page earlier"):
            st.session_state.batch_pages = move_page(pages, index, -1); st.rerun()
        if cols[3].button("↓", key=f"down_{item['id']}", disabled=index == len(pages)-1, help="Move page later"):
            st.session_state.batch_pages = move_page(pages, index, 1); st.rerun()
        if cols[4].button("Remove", key=f"remove_{item['id']}"):
            st.session_state.batch_pages = pages[:index] + pages[index+1:]; st.rerun()
        from PIL import Image
        single_buffer = io.BytesIO()
        Image.fromarray(item["image"]).save(single_buffer, format="PNG")
        st.download_button(f"Download page {index + 1}", single_buffer.getvalue(), file_name=f"page_{index+1}.png", mime="image/png", key=f"download_{item['id']}")
    if pages:
        pdf_data = generate_pdf([entry["image"] for entry in pages])
        st.download_button("Download combined PDF", pdf_data, file_name="scanify_batch.pdf", mime="application/pdf", type="primary", use_container_width=True)
        if st.button("Save combined PDF to history", key="save_batch"):
            try:
                filename = f"batch_{uuid.uuid4().hex[:8]}.pdf"
                path = config.EXPORTS_DIR / filename
                path.write_bytes(pdf_data)
                save_scan(config.DATABASE_PATH, original_filename=f"Batch of {len(pages)} pages", generated_filename=filename, processing_mode=mode, output_path=str(path), page_count=len(pages))
                st.success("Batch PDF saved to document history.")
            except OSError as exc:
                st.error(f"Could not save batch PDF: {exc}")


def render_history() -> None:
    page_header("LIBRARY", "Document history", "Find, preview, download or remove scans stored on this device.")
    query = st.text_input("Search filename or extracted OCR text", value=st.session_state.get("history_query", ""), placeholder="Type to search…")
    records = list_scans(config.DATABASE_PATH, query=query)
    if not records:
        st.info("No saved scans match your search.")
        return
    st.caption(f"{len(records)} result(s)")
    for record in records:
        with st.expander(f"{record['original_filename']}  ·  {format_timestamp(record['processed_at'])}  ·  {record['page_count']} page(s)"):
            st.write(f"Processing mode: {record['processing_mode']}")
            path = Path(record["output_path"])
            if path.exists():
                if path.suffix.lower() == ".pdf":
                    st.info("This batch entry is a PDF. Download it below to view the complete set of pages.")
                else:
                    st.image(str(path), caption="Saved scan", use_container_width=True)
                mime = "application/pdf" if path.suffix.lower() == ".pdf" else "image/png"
                st.download_button("Download saved file", path.read_bytes(), file_name=record["generated_filename"], mime=mime, key=f"hist_download_{record['id']}")
            else:
                st.warning("The saved file is missing from local storage; its history entry can still be removed.")
            if record["ocr_text"]:
                st.text_area("OCR text preview", record["ocr_text"], height=120, key=f"hist_ocr_{record['id']}")
            confirm_key = f"confirm_delete_{record['id']}"
            if not st.session_state.get(confirm_key, False):
                if st.button("Delete document", key=f"delete_{record['id']}"):
                    st.session_state[confirm_key] = True; st.rerun()
            else:
                st.warning("Delete this history entry and its locally stored files?")
                yes, no = st.columns(2)
                if yes.button("Confirm delete", key=f"yes_delete_{record['id']}", type="primary"):
                    removed = delete_scan(config.DATABASE_PATH, record["id"])
                    if removed:
                        for target in (removed["output_path"], removed["original_path"]):
                            try:
                                if target and Path(target).exists(): Path(target).unlink()
                            except OSError: pass
                    st.session_state[confirm_key] = False
                    st.success("Document deleted."); st.rerun()
                if no.button("Cancel", key=f"no_delete_{record['id']}"):
                    st.session_state[confirm_key] = False; st.rerun()


def render_ocr() -> None:
    page_header("TEXT EXTRACTION", "OCR workspace", "Extract text locally with Tesseract. Recognition accuracy depends on image quality and language data.")
    languages = available_languages()
    if not languages:
        st.warning("Tesseract OCR is unavailable. Install the Tesseract executable and language data, then restart Scanify. Scanning and export still work without it.")
    records = list_scans(config.DATABASE_PATH)
    options = {f"{r['original_filename']} · {format_timestamp(r['processed_at'])}": r for r in records if Path(r["output_path"]).suffix.lower() != ".pdf" and Path(r["output_path"]).exists()}
    image = None
    selected_record = None
    if options:
        label = st.selectbox("Choose a saved scan", list(options))
        selected_record = options[label]
        try:
            from PIL import Image
            image = np.asarray(Image.open(selected_record["output_path"]).convert("RGB"))
        except (OSError, ValueError):
            st.error("Could not read the selected saved image.")
    else:
        st.info("Save a processed scan to history first, or upload an image below.")
        direct_upload = st.file_uploader("Upload an image for OCR", type=["jpg", "jpeg", "png"], key="ocr_upload")
        if direct_upload:
            try: image = load_image(direct_upload.getvalue())
            except ValueError as exc: st.error(str(exc))
    if not image is None:
        st.image(image, caption="Selected processed image", use_container_width=True)
        language = st.selectbox("OCR language", languages or ["eng"], index=(languages.index("eng") if "eng" in languages else 0), help="Hindi requires the Tesseract hin language pack.")
        if "hin" in languages: st.caption("Hindi OCR is available because the Hindi language pack is installed.")
        if st.button("Extract text", type="primary", disabled=not tesseract_available()):
            try:
                extracted = extract_text(image, language)
                st.session_state.ocr_text = extracted
                st.session_state.ocr_editor = extracted
                st.session_state.ocr_source_id = selected_record["id"] if selected_record else None
            except RuntimeError as exc: st.error(str(exc))
        text = st.text_area("Extracted text · editable", value=st.session_state.get("ocr_text", selected_record["ocr_text"] if selected_record else ""), height=260, key="ocr_editor")
        if text:
            st.caption("Use the copy control on the text block, or select and copy from the editable field.")
            st.code(text, language=None)
        col1, col2 = st.columns(2)
        col1.download_button("Download text (.txt)", text, file_name="scanify_ocr.txt", mime="text/plain", use_container_width=True)
        if selected_record and col2.button("Save edited text to history", use_container_width=True):
            update_ocr(config.DATABASE_PATH, selected_record["id"], text)
            st.success("Edited OCR text saved to this scan's history.")


def render_about() -> None:
    page_header("ABOUT", "Scanify — Smart Document Scanner", "Turn Every Document Into a Perfect Scan.")
    st.markdown("""### Built for a hands-on image-processing project
Scanify is a local-first scanner that transforms ordinary document photographs into clearer, perspective-corrected digital pages. Traditional computer vision is the core of the workflow; OCR is an optional additional tool.

### Processing concepts
- **Representation and color:** uploaded images are orientation-corrected and decoded as RGB arrays; grayscale views support edge and threshold operations.
- **Preprocessing:** Gaussian smoothing reduces sensor noise before Canny edge detection. Median and bilateral filters are also available as reusable functions.
- **Boundary detection:** Canny edges are morphologically closed and dilated, then contours are sorted by area and approximated as polygons. A plausible four-corner candidate is returned only after area and geometry checks.
- **Perspective correction:** the four ordered corners map to a rectangular output using a projective transform.
- **Enhancement:** adaptive thresholding handles locally changing illumination; CLAHE boosts local contrast; denoising and unsharp masking provide additional controls.
- **Storage and export:** SQLite stores metadata while images and PDFs remain in organized local folders. ReportLab creates aspect-ratio-preserving multi-page PDFs.

### Technology
Python · Streamlit · OpenCV · NumPy · Pillow · Pytesseract · Tesseract · ReportLab · SQLite""")


def render_settings() -> None:
    page_header("PREFERENCES", "Settings", "Choose defaults for new scans. These preferences are held in the current local session.")
    st.session_state.setting_mode = st.selectbox("Default enhancement mode", ENHANCEMENT_MODES, index=ENHANCEMENT_MODES.index(st.session_state.setting_mode))
    st.session_state.setting_output = st.selectbox("Default output format", ["PDF", "PNG"], index=["PDF", "PNG"].index(st.session_state.setting_output))
    langs = available_languages()
    language_options = langs or ["eng"]
    default_lang = st.session_state.setting_language if st.session_state.setting_language in language_options else language_options[0]
    st.session_state.setting_language = st.selectbox("Default OCR language", language_options, index=language_options.index(default_lang), disabled=not bool(langs))
    st.session_state.setting_quality = st.slider("JPEG quality preference", 60, 100, int(st.session_state.setting_quality), help="Used as a default preference; lossless PNG and PDF downloads remain available.")
    st.info("Images are processed locally. Streamlit serves the application on your machine; do not expose it to untrusted networks without adding authentication and access controls.")


# cv2 is imported here for runtime exceptions raised by OpenCV operations.
import cv2

if page == "Dashboard": render_dashboard()
elif page == "New Scan": render_new_scan()
elif page == "Batch Scanning": render_batch()
elif page == "Document History": render_history()
elif page == "OCR Text Extraction": render_ocr()
elif page == "About Scanify": render_about()
elif page == "Settings": render_settings()
