import re
from datetime import date

from marshmallow import (Schema, ValidationError, fields, validate,
                          validates, validates_schema)

SDT_REGEX = r'^(0|\+84)(3|5|7|8|9)[0-9]{8}$'


class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=[
        validate.Length(min=5, max=20, error="Username phải từ 5 đến 20 kí tự!"),
        validate.Regexp(r'^\S+$', error="Username không được chứa khoảng trắng!")
    ], error_messages={"required": "Username không được để trống!"})

    password = fields.Str(required=True, validate=[
        validate.Length(min=8, max=255, error="Mật khẩu phải từ 8 đến 255 kí tự!"),
        validate.Regexp(r'^\S+$', error="Mật khẩu không được chứa khoảng trắng!"),
        validate.Regexp(r'.*[0-9].*', error="Mật khẩu phải chứa ít nhất một số!"),
        validate.Regexp(r'.*[a-z].*', error="Mật khẩu phải chứa ít nhất một chữ thường!"),
        validate.Regexp(r'.*[A-Z].*', error="Mật khẩu phải chứa ít nhất một chữ hoa!"),
        validate.Regexp(r'.*[!@#$%^&*(),.?":{}|<>].*', error="Mật khẩu phải chứa ít nhất một kí tự đặc biệt!")
    ], error_messages={"required": "Mật khẩu không được để trống!"})

    hoten = fields.Str(required=True, validate=[
        validate.Length(max=100, error="Họ tên không được vượt quá 100 ký tự!"),
        validate.Regexp(r'^\s*\S', error="Họ tên không được để trống!")
    ], error_messages={"required": "Họ tên không được để trống!"})


    email = fields.Email(required=False, allow_none=True, validate=[
        validate.Length(max=100, error="Email không được vượt quá 100 ký tự!")
    ], error_messages={"invalid": "Email không hợp lệ!"})

    sdt = fields.Str(required=False, allow_none=True, validate=[
        validate.Regexp(SDT_REGEX, error="Số điện thoại không hợp lệ! (VD: 0912345678)")
    ])

    gioitinh = fields.Str(required=True, validate=validate.OneOf(
        ["male", "female"], error="Giới tính không hợp lệ!"
    ), error_messages={"required": "Giới tính không được để trống!"})

    ngaysinh = fields.Date(required=False, allow_none=True, error_messages={
        "invalid": "Ngày sinh không hợp lệ!"
    })

    @validates('ngaysinh')
    def validate_ngaysinh(self, value, **kwargs):
        if value:
            today = date.today()
            if value >= today:
                raise ValidationError("Ngày sinh không được là hôm nay hoặc tương lai!")
            if value < today.replace(year=today.year - 120):
                raise ValidationError("Ngày sinh quá xa trong quá khứ!")

    @validates_schema
    def validate_lien_he(self, data, **kwargs):
        email = data.get('email')
        sdt = data.get('sdt')
        if not email and not sdt:
            raise ValidationError(
                "Vui lòng cung cấp ít nhất Email hoặc Số điện thoại để đăng ký!",
                field_name="email"
            )


class LoginSchema(Schema):
    dinh_danh = fields.Str(required=True, error_messages={
        "required": "Vui lòng nhập username, email hoặc số điện thoại!"
    })
    password = fields.Str(required=True, error_messages={
        "required": "Vui lòng nhập mật khẩu!"
    })


class TimKiemSachSchema(Schema):
    q = fields.Str(required=False, allow_none=True, load_default="")
    theloai_id = fields.Int(required=False, allow_none=True)
    page = fields.Int(required=False, load_default=1, validate=validate.Range(min=1))
    sort = fields.Str(required=False, load_default="moi_nhat", validate=validate.OneOf(
        ["moi_nhat", "ten_az", "danh_gia"]
    ))
