import pytest
from app.utils.target_normalizer import TargetNormalizer

def test_normalize_ip():
    norm = TargetNormalizer.normalize("192.168.1.1", "ip")
    assert norm.is_ip is True
    assert norm.scan_target == "192.168.1.1"
    assert norm.dns_name is None
    assert norm.get_dmarc_query() is None

def test_normalize_domain():
    norm = TargetNormalizer.normalize("example.com", "domain")
    assert norm.is_ip is False
    assert norm.scan_target == "example.com"
    assert norm.dns_name == "example.com"
    assert norm.get_dmarc_query() == "_dmarc.example.com"

def test_normalize_web_application_url():
    norm = TargetNormalizer.normalize("https://app.example.com/login?redirect=1", "web_application")
    assert norm.is_ip is False
    assert norm.scan_target == "app.example.com"
    assert norm.dns_name == "app.example.com"
    assert norm.scheme == "https"
    assert norm.get_dmarc_query() == "_dmarc.app.example.com"

def test_normalize_web_application_ip():
    norm = TargetNormalizer.normalize("http://192.168.1.50:8080/admin", "web_application")
    assert norm.is_ip is True
    assert norm.scan_target == "192.168.1.50"
    assert norm.dns_name is None
    assert norm.port == 8080
    assert norm.get_dmarc_query() is None
