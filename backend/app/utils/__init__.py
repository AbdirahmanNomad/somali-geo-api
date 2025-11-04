# Utils package
# This makes app.utils a package so we can import from app.utils.olc_helper

# Import functions from parent utils.py for backward compatibility
import sys
from pathlib import Path

# Import from parent utils.py module
parent_utils = Path(__file__).parent.parent / "utils.py"
if parent_utils.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("app.utils_module", parent_utils)
    utils_module = importlib.util.module_from_spec(spec)
    sys.modules["app.utils_module"] = utils_module
    spec.loader.exec_module(utils_module)
    
    # Export functions that login.py needs
    __all__ = [
        'generate_password_reset_token',
        'generate_reset_password_email', 
        'send_email',
        'verify_password_reset_token',
    ]
    
    # Re-export functions
    generate_password_reset_token = getattr(utils_module, 'generate_password_reset_token', None)
    generate_reset_password_email = getattr(utils_module, 'generate_reset_password_email', None)
    send_email = getattr(utils_module, 'send_email', None)
    verify_password_reset_token = getattr(utils_module, 'verify_password_reset_token', None)

