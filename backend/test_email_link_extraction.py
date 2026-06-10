"""Link extraction from HTML email CTAs (VML/Outlook buttons, conditional
comments) and static unwrapping of click-tracking wrappers. Mirrors the
Android HtmlLinkExtractor coverage so both pipelines agree on the real target."""

import os
import sys

from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import main as app_main
from services.redirect_resolver import unwrap_tracking_redirect


def _targets(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    found = app_main._collect_click_targets_from_html(soup)
    return {item["original_url"]: item for item in found}


def test_vml_roundrect_button_href_is_extracted():
    html = (
        '<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" '
        'href="https://evil-courier.example/plata-taxa" style="height:40px;">'
        "<center>Plătește taxa de livrare</center></v:roundrect>"
    )
    targets = _targets(html)
    assert "https://evil-courier.example/plata-taxa" in targets
    assert "Plătește taxa" in targets["https://evil-courier.example/plata-taxa"]["button_text"]


def test_vml_button_inside_mso_conditional_comment_is_extracted():
    html = (
        "<div><!--[if mso]>"
        '<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" '
        'href="https://evil2.example/confirmare" arcsize="10%">'
        "<center>Confirmă comanda</center></v:roundrect>"
        "<![endif]--></div>"
    )
    targets = _targets(html)
    assert "https://evil2.example/confirmare" in targets
    assert targets["https://evil2.example/confirmare"]["source_tag"].startswith("mso-comment:")


def test_anchor_inside_mso_conditional_comment_is_extracted():
    html = (
        "<!--[if mso]>"
        '<a href="https://hidden-outlook.example/login">Acceseaza contul</a>'
        "<![endif]-->"
    )
    targets = _targets(html)
    assert "https://hidden-outlook.example/login" in targets


def test_regular_anchor_button_still_extracted():
    html = '<a href="https://example.com/cta" style="display:block">Vezi factura</a>'
    targets = _targets(html)
    assert "https://example.com/cta" in targets


def test_unwrap_outlook_safelinks():
    wrapped = (
        "https://eur02.safelinks.protection.outlook.com/?url="
        "https%3A%2F%2Fevil-bank.example%2Flogin%3Fsession%3D9&data=05|01|"
    )
    assert unwrap_tracking_redirect(wrapped) == "https://evil-bank.example/login?session=9"


def test_unwrap_google_redirect():
    wrapped = "https://www.google.com/url?q=https%3A%2F%2Fphish.example%2Fro&sa=D"
    assert unwrap_tracking_redirect(wrapped) == "https://phish.example/ro"


def test_unwrap_facebook_lphp():
    wrapped = "https://l.facebook.com/l.php?u=https%3A%2F%2Fscam.example%2Foferta&h=AT0x"
    assert unwrap_tracking_redirect(wrapped) == "https://scam.example/oferta"


def test_unwrap_proofpoint_urldefense_v3():
    wrapped = "https://urldefense.com/v3/__https://evil.example/path__;!!AbC!xyz$"
    assert unwrap_tracking_redirect(wrapped) == "https://evil.example/path"


def test_unwrap_yahoo_redirect():
    wrapped = (
        "https://r.search.yahoo.com/_ylt=abc/RU=https%3A%2F%2Ftarget.example%2Fp/RK=2/RS=xyz"
    )
    assert unwrap_tracking_redirect(wrapped) == "https://target.example/p"


def test_unwrap_branch_style_fallback():
    wrapped = "https://yoxo.sng.link/Abcde/xyz?_fallback_redirect=https%3A%2F%2Fwww.yoxo.ro%2Foferta"
    assert unwrap_tracking_redirect(wrapped) == "https://www.yoxo.ro/oferta"


def test_unwrap_generic_redirector_requires_absolute_url():
    assert (
        unwrap_tracking_redirect("https://tracker.example/click?url=https%3A%2F%2Freal.example%2Fx")
        == "https://real.example/x"
    )
    # Relative ?next= values on legitimate sites must never unwrap.
    assert unwrap_tracking_redirect("https://bank.example/login?next=/cont") is None
    assert unwrap_tracking_redirect("https://shop.example/?to=settings") is None


def test_unwrap_protocol_relative_target_normalizes_to_https():
    assert (
        unwrap_tracking_redirect("https://tracker.example/c?url=%2F%2Fdest.example%2Fpath")
        == "https://dest.example/path"
    )


def test_unwrap_ignores_plain_urls():
    assert unwrap_tracking_redirect("https://www.emag.ro/telefoane") is None
    assert unwrap_tracking_redirect("") is None
