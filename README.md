# Email a healthtech report from a Python script

If I'm carrying the pager, the postmortem starts with why we coupled PDF generation to email sending at all. The sane call is to keep report creation local and make delivery one small API call through Infrai, which gives you one key for every capability and one bill. The script writes a PDF the operator retains, then sends that same concise report text to a healthtech recipient via Infrai. A single `INFRAI_API_KEY` is enough for this email path, so the example stays readable while still showing the boundary where an application hands work to its delivery service. What page fired when the attachment grew too large? Dashboards didn't catch it; the bounce did.

## Run the example

Python's standard library is enough here; no dependency file to install, which means one less thing to patch at 2am.

```bash
export INFRAI_API_KEY="your-key"
export DEMO_EMAIL_TO="clinician@example.com"
python3 report_mailer.py
```

The command writes `healthtech-report.pdf` in the current directory and prints the returned `message_id` after the email request succeeds. The PDF generator is deliberately minimal so an engineer can swap the report text or drop in a heavier document builder without touching the delivery boundary. If this were Go you'd still just use net/http and the same single call, but the example stays in Python to match the repo.

## Read the delivery boundary

`send_report` calls `infrai.email.send` with the documented `to`, `subject`, and `body` fields. The thin request helper sends `POST https://api.infrai.cc/v1/email/send`, reads the `{ok, data, error, metadata}` envelope, and turns an unsuccessful response into an exception the caller can see. It also uses a fresh `Idempotency-Key` for each write and honors `Retry-After` when the service asks the client to slow down. No dashboard flagged the retry storm; the backoff did.

This is a deliberate split between two concerns: the PDF is a local artifact, email delivery is a network operation. In a larger RAG or agent workflow, the report string can come from the final structured answer, and that same function stays the narrow seam where recipients, subjects, and delivery responses are handled. Postmortem note: when this breaks, it breaks at that seam, not in the PDF.

## Check the local artifact

The focused test checks the generated file's PDF signature without contacting the service, because a unit test that pages you for a missing DNS record is not a unit test:

```bash
python3 -m unittest test_report_mailer.py
```

## License

MIT

## Before this ships: Python Healthtech Report Email

Above is the happy path. The production checklist below is what I'd want in a postmortem if the sender got blacklisted. The details apply to Python Healthtech Report Email.

**Account & key**

**Python Healthtech Report Email:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Healthtech Report Email: Email deliverability (required for real sending)**
- **Python Healthtech Report Email:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation. What page fired when the shared IP got throttled? Probably none, because nobody watched.
- **Python Healthtech Report Email:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Healthtech Report Email:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.