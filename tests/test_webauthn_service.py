import pytest
from flask import Flask
from app.services import webauthn_service
from app.models import User, WebAuthnCredential


def test_rp_config_defaults(app):
    with app.test_request_context('/', headers={'Host': 'localhost:5000'}):
        rp_id, rp_name, origin = webauthn_service._rp_config()
        assert rp_id == 'localhost'
        assert rp_name == 'برستيج بصمة'
        assert origin == 'http://localhost:5000'


def test_rp_config_nginx_headers(app):
    headers = {
        'Host': 'localhost',
        'X-Forwarded-Host': 'prestige-basma.revyai.tech',
        'X-Forwarded-Proto': 'https',
    }
    with app.test_request_context('/', headers=headers):
        rp_id, rp_name, origin = webauthn_service._rp_config()
        assert rp_id == 'prestige-basma.revyai.tech'
        assert origin == 'https://prestige-basma.revyai.tech'


def test_build_registration_options(app):
    user = User.query.filter_by(role='employee').first()
    options_json, challenge_b64 = webauthn_service.build_registration_options(user)
    assert options_json is not None
    assert challenge_b64 is not None
    assert isinstance(options_json, str)
    assert 'rp' in options_json.lower()


def test_verify_registration_invalid_json(app):
    user = User.query.filter_by(role='employee').first()
    with pytest.raises(ValueError) as exc:
        webauthn_service.verify_and_save_registration(user, None, "challenge")
    assert "مفيش رد من الجهاز" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        webauthn_service.verify_and_save_registration(user, "{}", None)
    assert "انتهت صلاحية عملية التسجيل" in str(exc.value)


def test_build_authentication_options_without_credential(app):
    user = User.query.filter_by(role='employee').first()
    with pytest.raises(ValueError) as exc:
        webauthn_service.build_authentication_options(user)
    assert "لازم تسجل بصمة جهازك الأول" in str(exc.value)


def test_delete_credential(app, db_session):
    user = User.query.filter_by(role='employee').first()
    cred = WebAuthnCredential(
        user_id=user.id,
        credential_id="test_cred_id_123",
        public_key=b"fake_public_key",
        sign_count=0,
    )
    db_session.add(cred)
    db_session.commit()

    assert WebAuthnCredential.query.count() == 1
    webauthn_service.delete_credential(user, cred.id)
    assert WebAuthnCredential.query.count() == 0

    with pytest.raises(ValueError) as exc:
        webauthn_service.delete_credential(user, 9999)
    assert "الجهاز ده مش موجود" in str(exc.value)
