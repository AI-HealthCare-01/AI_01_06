from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ocr_service import NaverOcrService

MOCK_CLOVA_RESPONSE = {
    "version": "V2",
    "requestId": "test-id",
    "timestamp": 1234567890,
    "images": [
        {
            "uid": "test-uid",
            "name": "prescription",
            "inferResult": "SUCCESS",
            "message": "SUCCESS",
            "fields": [
                {"inferText": "요양기관명", "inferConfidence": 0.99},
                {"inferText": "서울대학교병원", "inferConfidence": 0.99},
                {"inferText": "처방의사성명", "inferConfidence": 0.99},
                {"inferText": "김의사", "inferConfidence": 0.99},
                {"inferText": "처방일", "inferConfidence": 0.99},
                {"inferText": "2026-02-25", "inferConfidence": 0.99},
                {"inferText": "상병명", "inferConfidence": 0.99},
                {"inferText": "당뇨병, 고혈압", "inferConfidence": 0.99},
                {"inferText": "처방의약품의명칭", "inferConfidence": 0.99},
                {"inferText": "1회투여량", "inferConfidence": 0.99},
                {"inferText": "1일투여횟수", "inferConfidence": 0.99},
                {"inferText": "총투여일수", "inferConfidence": 0.99},
                {"inferText": "용법", "inferConfidence": 0.99},
                {"inferText": "아스피린", "inferConfidence": 0.99},
                {"inferText": "100mg", "inferConfidence": 0.99},
                {"inferText": "1", "inferConfidence": 0.99},
                {"inferText": "30일", "inferConfidence": 0.99},
                {"inferText": "아침 식후", "inferConfidence": 0.99},
                {"inferText": "메트포르민", "inferConfidence": 0.99},
                {"inferText": "500mg", "inferConfidence": 0.99},
                {"inferText": "2", "inferConfidence": 0.99},
                {"inferText": "30일", "inferConfidence": 0.99},
                {"inferText": "아침 저녁 식후", "inferConfidence": 0.99},
            ],
        }
    ],
}


def test_parse_fields_extracts_hospital_name():
    service = NaverOcrService(secret="s", url="u")
    result = service._parse_fields(["요양기관명", "서울대학교병원"])
    assert result["hospital_name"] == "서울대학교병원"


def test_parse_fields_extracts_doctor_name():
    service = NaverOcrService(secret="s", url="u")
    result = service._parse_fields(["처방의사성명", "김의사"])
    assert result["doctor_name"] == "김의사"


def test_parse_fields_extracts_prescription_date():
    service = NaverOcrService(secret="s", url="u")
    result = service._parse_fields(["처방일", "2026-02-25"])
    assert result["prescription_date"] == "2026-02-25"


def test_parse_fields_extracts_diagnosis():
    service = NaverOcrService(secret="s", url="u")
    result = service._parse_fields(["상병명", "당뇨병, 고혈압"])
    assert result["diagnosis"] == "당뇨병, 고혈압"


def test_parse_fields_returns_empty_medications_by_default():
    service = NaverOcrService(secret="s", url="u")
    result = service._parse_fields(["요양기관명", "서울대학교병원"])
    assert result["medications"] == []


def test_parse_fields_handles_full_prescription_blocks():
    service = NaverOcrService(secret="s", url="u")
    texts = [
        "요양기관명",
        "서울대학교병원",
        "처방의사성명",
        "김의사",
        "처방일",
        "2026-02-25",
        "상병명",
        "당뇨병",
    ]
    result = service._parse_fields(texts)
    assert result["hospital_name"] == "서울대학교병원"
    assert result["doctor_name"] == "김의사"
    assert result["prescription_date"] == "2026-02-25"
    assert result["diagnosis"] == "당뇨병"


def test_parse_fields_extracts_single_medication():
    service = NaverOcrService(secret="s", url="u")
    texts = [
        "처방의약품의명칭",
        "1회투여량",
        "1일투여횟수",
        "총투여일수",
        "용법",
        "아스피린",
        "100mg",
        "1",
        "30일",
        "아침 식후",
    ]
    result = service._parse_fields(texts)
    assert len(result["medications"]) == 1
    assert result["medications"][0]["name"] == "아스피린"
    assert result["medications"][0]["dosage"] == "100mg"
    assert result["medications"][0]["duration"] == "30일"
    assert result["medications"][0]["instructions"] == "아침 식후"


def test_parse_fields_extracts_multiple_medications():
    service = NaverOcrService(secret="s", url="u")
    texts = [
        "처방의약품의명칭",
        "1회투여량",
        "1일투여횟수",
        "총투여일수",
        "용법",
        "아스피린",
        "100mg",
        "1",
        "30일",
        "아침 식후",
        "메트포르민",
        "500mg",
        "2",
        "30일",
        "아침 저녁 식후",
    ]
    result = service._parse_fields(texts)
    assert len(result["medications"]) == 2
    assert result["medications"][1]["name"] == "메트포르민"
    assert result["medications"][1]["dosage"] == "500mg"
    assert result["medications"][1]["instructions"] == "아침 저녁 식후"


async def test_call_clova_api_returns_text_list(tmp_path):
    image_file = tmp_path / "test.png"
    image_file.write_bytes(b"fake-image-data")
    service = NaverOcrService(secret="test-secret", url="http://fake-ocr-url")
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_CLOVA_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    with patch("app.services.ocr_service.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        texts = await service._call_clova_api(str(image_file))
    assert "서울대학교병원" in texts
    assert "아스피린" in texts


async def test_call_clova_api_sends_correct_headers(tmp_path):
    image_file = tmp_path / "test.jpg"
    image_file.write_bytes(b"fake-image-data")
    service = NaverOcrService(secret="my-secret", url="http://fake-ocr-url")
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_CLOVA_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    with patch("app.services.ocr_service.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        await service._call_clova_api(str(image_file))
    _, call_kwargs = mock_client.post.call_args
    assert call_kwargs["headers"]["X-OCR-SECRET"] == "my-secret"


async def test_extract_returns_structured_dict_with_medications(tmp_path):
    image_file = tmp_path / "test.png"
    image_file.write_bytes(b"fake-image-data")
    service = NaverOcrService(secret="test-secret", url="http://fake-ocr-url")
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_CLOVA_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    with patch("app.services.ocr_service.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await service.extract(str(image_file))
    assert result["hospital_name"] == "서울대학교병원"
    assert result["doctor_name"] == "김의사"
    assert result["prescription_date"] == "2026-02-25"
    assert result["diagnosis"] == "당뇨병, 고혈압"
    assert len(result["medications"]) == 2
    assert result["medications"][0]["name"] == "아스피린"
    assert result["medications"][1]["name"] == "메트포르민"
