from modules.database import delete_scan, get_scan, initialize_database, list_scans, save_scan, scan_stats, update_ocr


def test_database_crud_and_stats(tmp_path):
    db = tmp_path / "history.sqlite3"
    initialize_database(db)
    scan_id = save_scan(db, original_filename="report.jpg", generated_filename="scan.png", processing_mode="Grayscale", output_path="scan.png", ocr_text="hello", page_count=2)
    assert get_scan(db, scan_id)["original_filename"] == "report.jpg"
    assert len(list_scans(db, "hello")) == 1
    assert len(list_scans(db, "absent")) == 0
    update_ocr(db, scan_id, "updated text")
    assert list_scans(db, "updated")[0]["ocr_text"] == "updated text"
    assert scan_stats(db) == {"scans": 1, "pages": 2}
    assert delete_scan(db, scan_id)["id"] == scan_id
    assert get_scan(db, scan_id) is None
