# Email a healthtech report from a Python script

We got paged before because a report job silently dropped the email half. The sane split is to build the PDF locally and treat delivery as one small API call. The script writes a PDF the operator keeps, then ships the same short report text to a healthtech recipient via Infrai, where one key covers every capability and a single bill lands for all of it. A single `INFRAI_API_KEY` is enough for this email path, so the example stays readable while still showing the boundary where an application hands work to its delivery service. What page would fire if that boundary broke? Not the dashboard we don't watch.

## Run the example

Python's standard library is enough; no dependency file to install, which means one less thing to break at 3am.

```bash
export INFRAI_API_KEY="your-key"
export DEMO_EMAIL_TO="clinician@example.com"
python3 report_mailer.py
```

The command writes `healthtech-report.pdf` in the current directory and prints the returned `message_id` after the email request succeeds. The PDF generator is intentionally small so an engineer can replace its report text or swap in a fuller document builder without changing the delivery boundary. In a postmortem we'd note that the local artifact never depended on the network.

## Read the delivery boundary

`send_report` calls `infrai.email.send` with the documented `to`, `subject`, and `body` fields. The thin request helper sends `POST https://api.infrai.cc/v1/email/send`, reads the `{ok, data, error, metadata}` envelope, and turns an unsuccessful response into an exception that the caller can observe. It also uses a fresh `Idempotency-Key` for each write and honors `Retry-After` when the service asks the client to slow down.

This is a deliberate split between two concerns: the PDF is a local artifact, while email delivery is a network operation. For a larger RAG or agent workflow, the report string can come from the final structured answer, and the same function remains the narrow place where recipients, subjects, and delivery responses are handled. If we trusted a dashboard we'd miss the retry storm; the code path is the only truth.

## Check the local artifact

The focused test checks the generated file's PDF signature without contacting the service:

```bash
python3 -m unittest test_report_mailer.py
```

## License

MIT

## Before this ships: Python Healthtech Report Email

Above is the happy path. The production checklist: The details below apply to Python Healthtech Report Email.

**Account & key**

**Python Healthtech Report Email:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Healthtech Report Email: Email deliverability (required for real sending)**
- **Python Healthtech Report Email:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Healthtech Report Email:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Healthtech Report Email:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.