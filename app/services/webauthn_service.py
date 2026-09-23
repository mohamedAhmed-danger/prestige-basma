"""
webauthn_service.py — Batch 12

WebAuthn (platform authenticator: Face ID / Touch ID / Windows Hello / Android
biometrics) as a THIRD factor on top of the existing GPS + sign-in-window checks —
additive, does not replace them. Uses the `webauthn` PyPI package (py_webauthn,
duo-labs) rather than hand-rolling any of the crypto/attestation parsing.

Data-flow convention kept from every earlier batch: no REST/JSON endpoint is added
here. The registration/authentication *options* (the server-generated challenge)
are embedded straight into a server-rendered page at GET time (see the
`/employee/webauthn/register` and `/employee/dashboard` routes) — the browser then
calls navigator.credentials.create()/get() itself, and the JSON result of that
browser call is submitted back as the value of a single hidden field in a normal
HTML <form method="POST">, exactly like the lat/lng fields from Batch 7/8. No
fetch() call is introduced anywhere.

The challenge for a given ceremony is round-tripped through the Flask session
(signed cookie) between the GET that generates it and the POST that verifies it —
never trusted from the client, and never stored in the database.
"""
import json
from datetime import datetime, timezone

from flask import current_app

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes,
)
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.extensions import db
from app.models import WebAuthnCredential


from flask import current_app, request
import os


def _rp_config():
    env_rp_id = current_app.config.get('WEBAUTHN_RP_ID') or os.getenv('WEBAUTHN_RP_ID')
    env_origin = current_app.config.get('WEBAUTHN_ORIGIN') or os.getenv('WEBAUTHN_ORIGIN')
    rp_name = current_app.config.get('WEBAUTHN_RP_NAME', 'برستيج بصمة')

    rp_id = env_rp_id
    origin = env_origin

    if request:
        # Read real host and protocol forwarded by Nginx or reverse proxy
        host_header = request.headers.get('X-Forwarded-Host', request.host)
        req_host = host_header.split(':')[0]
        scheme = request.headers.get('X-Forwarded-Proto', request.scheme)

        # Handle local dev vs production domain fallback dynamically
        if not rp_id or rp_id in ('localhost', '127.0.0.1'):
            if req_host not in ('127.0.0.1', 'localhost'):
                rp_id = req_host
            else:
                rp_id = 'localhost'

        if not origin or 'localhost' in origin or '127.0.0.1' in origin:
            if req_host not in ('127.0.0.1', 'localhost'):
                origin = f"{scheme}://{host_header}"
            else:
                origin = origin or f"{scheme}://{host_header}"

    if not rp_id:
        rp_id = 'prestige-basma.revyai.tech'
    if not origin:
        origin = 'https://prestige-basma.revyai.tech'

    return rp_id, rp_name, origin


def build_registration_options(user):
    """Returns (options_json_str, challenge_b64url_str).

    options_json_str is passed straight to the template to embed for
    navigator.credentials.create(); challenge_b64url_str is what the route
    stores in session['webauthn_reg_challenge'] to verify the POST against.

    Excludes the user's already-registered credentials so the same device
    can't be enrolled twice.
    """
    rp_id, rp_name, _origin = _rp_config()

    exclude_credentials = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(cred.credential_id))
        for cred in user.webauthn_credentials
    ]

    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=rp_name,
        user_id=str(user.id).encode('utf-8'),
        user_name=user.name,
        user_display_name=user.name,
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
    )
    return options_to_json(options), bytes_to_base64url(options.challenge)


def verify_and_save_registration(user, credential_json, expected_challenge_b64, nickname=None):
    """Verifies a registration response (the JSON that @simplewebauthn/browser's
    startRegistration() resolves with) and stores the new credential for `user`.

    Raises ValueError with a user-facing (Arabic) message on any failure —
    matches the pattern every other service function in this project uses.
    Returns the saved WebAuthnCredential on success.
    """
    rp_id, _rp_name, origin = _rp_config()

    if not credential_json:
        raise ValueError('مفيش رد من الجهاز، جرب تاني')
    if not expected_challenge_b64:
        raise ValueError('انتهت صلاحية عملية التسجيل، حدّث الصفحة وحاول تاني')

    try:
        verification = verify_registration_response(
            credential=credential_json,
            expected_challenge=base64url_to_bytes(expected_challenge_b64),
            expected_rp_id=rp_id,
            expected_origin=origin,
            require_user_verification=True,
        )
    except Exception as e:
        raise ValueError(f'فشل تسجيل بصمة الجهاز: {e}')

    credential_id_b64 = bytes_to_base64url(verification.credential_id)
    if WebAuthnCredential.query.filter_by(credential_id=credential_id_b64).first():
        raise ValueError('الجهاز ده مسجل بالفعل')

    credential = WebAuthnCredential(
        user_id=user.id,
        credential_id=credential_id_b64,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        device_type=getattr(verification.credential_device_type, 'value', verification.credential_device_type),
        backed_up=verification.credential_backed_up,
        nickname=(nickname or '').strip() or None,
    )
    db.session.add(credential)
    db.session.commit()
    return credential


def build_authentication_options(user):
    """Returns (options_json_str, challenge_b64url_str) for navigator.credentials.get(),
    restricted to this user's own registered credential(s) via allow_credentials.

    Raises ValueError if the user has no registered device yet — the route/template
    is expected to check `user.webauthn_credentials` and offer registration instead
    of calling this.
    """
    rp_id, _rp_name, _origin = _rp_config()

    credentials = user.webauthn_credentials
    if not credentials:
        raise ValueError('لازم تسجل بصمة جهازك الأول')

    allow_credentials = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(cred.credential_id))
        for cred in credentials
    ]

    options = generate_authentication_options(
        rp_id=rp_id,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    return options_to_json(options), bytes_to_base64url(options.challenge)


def verify_authentication(user, credential_json, expected_challenge_b64):
    """The third-factor check inserted into sign-in/sign-out BEFORE the GPS check
    (per the plan). Verifies an authentication (assertion) response against the
    stored public key of the matching credential, and updates that credential's
    sign_count/last_used_at.

    Raises ValueError with a user-facing message on any failure — duplicate
    sign_count (cloned authenticator), wrong RP/origin, bad signature, unknown
    credential id, expired/missing challenge, etc. Returns True on success.
    """
    rp_id, _rp_name, origin = _rp_config()

    if not credential_json:
        raise ValueError('لازم تأكد هويتك ببصمة الجهاز عشان تسجل')
    if not expected_challenge_b64:
        raise ValueError('انتهت صلاحية الجلسة، حدّث الصفحة وحاول تاني')

    try:
        raw = json.loads(credential_json) if isinstance(credential_json, str) else credential_json
        credential_id_b64 = raw.get('id') or raw.get('rawId')
    except (TypeError, ValueError, AttributeError):
        raise ValueError('مقدرناش نقرأ رد الجهاز، جرب تاني')

    if not credential_id_b64:
        raise ValueError('مقدرناش نقرأ رد الجهاز، جرب تاني')

    stored = WebAuthnCredential.query.filter_by(
        user_id=user.id, credential_id=credential_id_b64
    ).first()
    if not stored:
        raise ValueError('الجهاز ده مش مسجل على حسابك')

    try:
        verification = verify_authentication_response(
            credential=raw,
            expected_challenge=base64url_to_bytes(expected_challenge_b64),
            expected_rp_id=rp_id,
            expected_origin=origin,
            credential_public_key=stored.public_key,
            credential_current_sign_count=stored.sign_count,
            require_user_verification=True,
        )
    except Exception as e:
        raise ValueError(f'فشل التحقق ببصمة الجهاز: {e}')

    stored.sign_count = verification.new_sign_count
    stored.last_used_at = datetime.now(timezone.utc)
    db.session.commit()
    return True


def delete_credential(user, credential_id):
    """Removes one registered device (identified by its DB primary key, not the
    WebAuthn credential_id) belonging to `user`. Used by the "manage devices" list
    so a lost/replaced phone can be de-registered and re-enrolled."""
    credential = WebAuthnCredential.query.filter_by(id=credential_id, user_id=user.id).first()
    if not credential:
        raise ValueError('الجهاز ده مش موجود')
    db.session.delete(credential)
    db.session.commit()
