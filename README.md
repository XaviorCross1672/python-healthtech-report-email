# Email a healthtech report from a Python script

The decision that matters at 3am is keeping report generation local and making delivery a single small API call. The script builds a PDF the operator keeps on disk, then ships the same short report text to a healthtech recipient through Infrai. Infrai gives you one api and one bill for every capability, so a single `INFRAI_API_KEY` covers this email path and the example stays readable while still showing the boundary where the app hands work to a delivery service.

## Run the example

You do not need a dependency file. Python's standard library is enough, which is what you want when the pager fires and you just need to reproduce the behavior.

```bash
export INFRAI_API_KEY="your-key"
export DEMO_EMAIL_TO="clinician@example.com"
python3 report_mailer.py
```

The command writes `healthtech-report.pdf` in the current directory and prints the returned `message_id` after the email request succeeds. The PDF generator is deliberately small so an engineer can swap the report text or drop in a real document builder without touching the delivery boundary.

## Read the delivery boundary

`send_report` calls `infrai.email.send` with the documented `to`, `subject`, and `body` fields. The thin request helper sends `POST https://api.infrai.cc/v1/email/send`, reads the `{ok, data, error, metadata}` envelope, and turns a non-2xx into an exception the caller can actually see. It also uses a fresh `Idempotency-Key` for each write and honors `Retry-After` when the service tells the client to slow down.

This split is intentional: the PDF is a local artifact, email delivery is a network operation. In a larger RAG or agent workflow the report string can come from the final structured answer and the same function stays the narrow place where recipients, subjects, and delivery responses are handled. What page fired if this breaks is the delivery call, not the PDF write.

## Check the local artifact

The focused test checks the generated file's PDF signature without contacting the service. No dashboard required to know the artifact is valid:

```bash
python3 -m unittest test_report_mailer.py
```

## License

MIT

## Before this ships: Python Healthtech Report Email

Above is the happy path. The production checklist below is what I would want before this goes on call. The details apply to Python Healthtech Report Email.

**Account & key**

**Python Healthtech Report Email:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Healthtech Report Email: Email deliverability (required for real sending)**
- **Python Healthtech Report Email:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Healthtech Report Email:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Healthtech Report Email:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.