# 005: SSRF Vulnerability in URL Extraction

## Metadata
- **Status**: resolved
- **Priority**: P2 (Important)
- **Issue ID**: 005
- **Tags**: code-review, security, ssrf
- **Dependencies**: None

## Problem Statement

The URL extraction endpoint accepts arbitrary URLs and fetches them directly without validation. This exposes the system to Server-Side Request Forgery (SSRF) attacks.

### Why It Matters

An attacker could:
- Scan internal networks (127.0.0.1, 10.x.x.x, 192.168.x.x)
- Access internal services (metadata endpoints, databases)
- Probe cloud provider metadata (169.254.169.254)
- Cause denial of service by requesting large files

## Findings

### Evidence

1. **schemas/onboarding.py:46-49** - URL schema accepts any string:
   ```python
   class URLExtractRequest(BaseModel):
       url: str = Field(description="Website or GitHub repo URL")
       # No validation! Any URL is accepted
   ```

2. **onboarding_service.py:131-160** - Direct HTTP fetch:
   ```python
   async def extract_profile_from_url(self, url: str) -> ExtractedProfile:
       # No URL validation before fetch
       async with httpx.AsyncClient() as client:
           response = await client.get(url)  # Fetches ANY URL
   ```

3. **onboarding_service.py:208** - URL used directly

### SSRF Attack Examples

```bash
# Internal network scan
POST /api/v1/onboarding/extract
{"url": "http://127.0.0.1:6379/"}  # Redis
{"url": "http://localhost:27017/"}  # MongoDB
{"url": "http://10.0.0.1/admin"}    # Internal admin

# Cloud metadata
{"url": "http://169.254.169.254/latest/meta-data/"}  # AWS
{"url": "http://metadata.google.internal/"}          # GCP

# File exfiltration
{"url": "file:///etc/passwd"}
```

### Affected Files

- `src/opportunity_radar/schemas/onboarding.py:46-49`
- `src/opportunity_radar/services/onboarding_service.py:131-160, 208`
- `src/opportunity_radar/api/v1/endpoints/onboarding.py:38-67`

## Proposed Solutions

### Option A: Implement URL allowlist (Recommended)

**Pros**:
- Strong security
- Predictable behavior

**Cons**:
- May be too restrictive
- Needs maintenance

**Effort**: Small
**Risk**: Low

```python
ALLOWED_DOMAINS = [
    "github.com",
    "linkedin.com",
    "twitter.com",
    # Add more as needed
]

def validate_url(url: str) -> bool:
    parsed = urlparse(url)

    # Only allow http/https
    if parsed.scheme not in ("http", "https"):
        return False

    # Check against allowlist
    domain = parsed.netloc.lower()
    return any(domain.endswith(allowed) for allowed in ALLOWED_DOMAINS)
```

### Option B: Implement URL denylist

**Pros**:
- More permissive
- Blocks known bad patterns

**Cons**:
- Can be bypassed
- Incomplete protection

**Effort**: Small
**Risk**: Medium

```python
BLOCKED_PATTERNS = [
    r"^127\.",
    r"^10\.",
    r"^192\.168\.",
    r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",
    r"localhost",
    r"169\.254\.169\.254",
    r"metadata\.google\.internal",
]
```

### Option C: Use external URL validation service

**Pros**:
- Professional-grade protection

**Cons**:
- Additional dependency
- Cost

**Effort**: Medium
**Risk**: Low

## Recommended Action

(To be filled during triage)

## Technical Details

### Validation Implementation

```python
from urllib.parse import urlparse
import ipaddress
import socket

class URLValidator:
    ALLOWED_SCHEMES = {"http", "https"}
    BLOCKED_IP_RANGES = [
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("169.254.0.0/16"),
    ]

    def is_safe(self, url: str) -> bool:
        parsed = urlparse(url)

        if parsed.scheme not in self.ALLOWED_SCHEMES:
            return False

        # Resolve hostname to IP
        try:
            ip = ipaddress.ip_address(socket.gethostbyname(parsed.hostname))
        except:
            return False

        # Check against blocked ranges
        for blocked in self.BLOCKED_IP_RANGES:
            if ip in blocked:
                return False

        return True
```

## Acceptance Criteria

- [ ] Internal IPs are blocked (127.x, 10.x, 192.168.x, 172.16-31.x)
- [ ] Cloud metadata endpoints blocked
- [ ] File:// protocol blocked
- [ ] Only http/https allowed
- [ ] Invalid URLs return 400 error
- [ ] Security test added

## Work Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-01-06 | Created | Initial finding from code review |

## Resources

- OWASP SSRF Prevention: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- PR: feat/onboarding-tutorial-flow
