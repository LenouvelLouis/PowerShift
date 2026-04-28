# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main branch | Yes |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Contact the maintainer directly via GitHub private message or email
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

- **Acknowledgment**: within 48 hours
- **Initial assessment**: within 1 week
- **Fix or mitigation**: as soon as possible, depending on severity

## Security Measures in Place

- **API authentication**: optional API key (`X-API-Key` header) for production deployments
- **Rate limiting**: 60 requests/min per IP via slowapi
- **CORS**: restricted origins configurable via `CORS_ORIGINS` environment variable
- **Input validation**: Pydantic v2 schemas on all API endpoints
- **SQL injection prevention**: SQLAlchemy parameterized queries (no raw SQL)
- **Docker hardening**: non-root user (`appuser`) + health checks on all containers
- **No secrets in code**: all credentials loaded from environment variables
- **Structured logging**: JSON logs with request-id correlation for audit trails

## Known Considerations

- The simulation engine (PyPSA) is CPU-intensive. Rate limiting prevents abuse but does not eliminate DoS risk for large simulations.
- Weather data is fetched from external APIs (KNMI, Open-Meteo). These are public APIs and do not require authentication.
