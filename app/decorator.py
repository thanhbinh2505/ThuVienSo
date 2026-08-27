from functools import wraps

from flask import abort, jsonify, redirect, request, url_for
from flask_login import current_user


def anonymous_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


def _is_api_request():
    return request.path.startswith('/api')


def role_required(allowed_roles):

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if _is_api_request():
                    return jsonify({
                        "success": False,
                        "loai_thong_bao": "auth_required",
                        "message": "Vui lòng đăng nhập!"
                    }), 401
                return redirect(url_for('login_process', next=request.path))

            roles_list = allowed_roles if isinstance(allowed_roles, list) else [allowed_roles]

            if current_user.role not in roles_list:
                if _is_api_request():
                    return jsonify({
                        "success": False,
                        "message": "Bạn không có quyền truy cập!"
                    }), 403
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator
