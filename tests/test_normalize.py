import pytest
from app.services.normalize import normalize_any, normalize_syslog


def test_normalize_syslog_firewall():
    line = (
        "<134>Aug 20 12:44:56 fw01 vendor=demo product=ngfw action=deny "
        "src=10.0.1.10 dst=8.8.8.8 spt=5353 dpt=53 proto=udp msg=DNS_blocked policy=Block-DNS"
    )
    ev = normalize_syslog(line, "demoA")
    assert ev["source"] == "firewall"
    assert ev["action"] == "deny"
    assert ev["src_ip"] == "10.0.1.10"
    assert ev["dst_ip"] == "8.8.8.8"
    assert ev["dst_port"] == 53
    assert ev["tenant"] == "demoA"


def test_normalize_api_login_failed():
    payload = {
        "tenant": "demoA",
        "source": "api",
        "event_type": "app_login_failed",
        "user": "alice",
        "ip": "203.0.113.7",
        "@timestamp": "2025-08-20T07:20:00Z",
    }
    ev = normalize_any(payload)
    assert ev["src_ip"] == "203.0.113.7"
    assert ev["user"] == "alice"
    assert ev["action"] == "login"
    assert ev["timestamp"].year == 2025


def test_normalize_aws_cloud():
    payload = {
        "tenant": "demoB",
        "source": "aws",
        "cloud": {"service": "iam", "account_id": "123456789012", "region": "ap-southeast-1"},
        "event_type": "CreateUser",
        "user": "admin",
        "@timestamp": "2025-08-20T09:10:00Z",
    }
    ev = normalize_any(payload)
    assert ev["cloud_service"] == "iam"
    assert ev["cloud_account_id"] == "123456789012"
    assert ev["cloud_region"] == "ap-southeast-1"
