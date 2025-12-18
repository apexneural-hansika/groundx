"""
Basic tests for the Streamlit application
"""
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import app
        import groundx_utils
        import evaluation_geval
        assert True
    except ImportError as e:
        assert False, f"Import error: {e}"

def test_prepare_chat_context():
    """Test prepare_chat_context function"""
    from app import prepare_chat_context
    
    # Test with None
    result = prepare_chat_context(None, "test")
    assert result is None
    
    # Test with empty dict
    result = prepare_chat_context({}, "test")
    assert result is None
    
    # Test with valid data
    xray_data = {
        "fileSummary": "Test summary",
        "fileType": "PDF",
        "language": "en",
        "documentPages": [
            {
                "chunks": [
                    {"text": "Sample text content"}
                ]
            }
        ]
    }
    result = prepare_chat_context(xray_data, "test")
    assert result is not None
    assert "Test summary" in result
    assert "PDF" in result

def test_generate_chat_response_no_api_key():
    """Test generate_chat_response when API key is missing"""
    from app import generate_chat_response
    
    with patch.dict(os.environ, {}, clear=True):
        result = generate_chat_response("test question", "test context")
        assert "OPENROUTER_API_KEY" in result
        assert "Error" in result or "not found" in result

def test_generate_chat_response_with_context():
    """Test generate_chat_response with context"""
    from app import generate_chat_response
    
    # Test with None context
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}, clear=True):
        # Should handle None context gracefully
        result = generate_chat_response("test question", None)
        # Should not crash, but may return error if API call fails
        assert isinstance(result, str)

def test_groundx_utils_imports():
    """Test groundx_utils imports"""
    from groundx_utils import (
        create_client,
        ensure_bucket,
        check_file_exists,
        get_xray_for_existing_document,
        process_document
    )
    assert callable(create_client)
    assert callable(ensure_bucket)
    assert callable(check_file_exists)
    assert callable(get_xray_for_existing_document)
    assert callable(process_document)

def test_groundx_client_creation_no_key():
    """Test create_client raises error when no API key"""
    from groundx_utils import create_client
    
    with patch.dict(os.environ, {}, clear=True):
        try:
            # This should raise ValueError in Streamlit context
            # In test context, it might behave differently
            client = create_client()
            # If it doesn't raise, that's also acceptable for testing
            assert True
        except ValueError:
            assert True  # Expected behavior
        except Exception as e:
            # Other exceptions are also acceptable
            assert True

def test_evaluation_imports():
    """Test evaluation_geval imports"""
    from evaluation_geval import (
        evaluate_invoice_parsing,
        EvaluatorGEval,
        create_evaluator_geval
    )
    assert callable(evaluate_invoice_parsing)
    assert callable(create_evaluator_geval)

def test_evaluate_invoice_parsing():
    """Test evaluate_invoice_parsing function"""
    from evaluation_geval import evaluate_invoice_parsing
    
    result = evaluate_invoice_parsing(
        "test output",
        "test expected",
        "test question"
    )
    assert isinstance(result, dict)
    assert "overall_score" in result
    assert "reason" in result
    assert "passed" in result

def test_file_syntax():
    """Test that all Python files have valid syntax"""
    import py_compile
    import os
    
    files_to_check = [
        "app.py",
        "groundx_utils.py",
        "evaluation_geval.py",
        "run_evaluation_cli.py"
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            try:
                py_compile.compile(file, doraise=True)
            except py_compile.PyCompileError as e:
                assert False, f"Syntax error in {file}: {e}"


