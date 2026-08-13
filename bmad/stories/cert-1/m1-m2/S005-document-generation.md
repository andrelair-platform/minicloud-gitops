---
id: S005-document-generation
title: "Policy attestation PDF generation — template + MinIO storage"
status: Ready
type: Story
epic: ktayl-policy-service
milestone: "CERT-1 M1-M2 — ktayl-policy-service (Go)"
estimate: 3
labels: [go, documents, minio, cert-1, backend]
priority: Must
assignee: AndreLiar
---

## Story

As an **assuré**, I want to download a PDF attestation of my active policy so that I can present proof of insurance when required (e.g. car registration, rental contract).

## Background

CdCF §6.1 BF-POL-05 — document generation. The attestation is a legal document required by ACPR Art.L113-5. It must be generated on-demand, stored in MinIO, and accessible via a signed URL. Docuseal handles formal signatures; this story handles the attestation (unsigned proof document).

## Acceptance Criteria

- [ ] AC-1: `POST /v1/policies/:id/documents/attestation` — generates PDF, stores in MinIO, returns `{document_id, url, expires_at}`
- [ ] AC-2: PDF contains: policy number, holder name, product name, LOB, effective/expiry dates, coverage summary, generated_at timestamp
- [ ] AC-3: Signed MinIO URL expires in 1 hour (configurable via `DOCUMENT_URL_TTL`)
- [ ] AC-4: `GET /v1/policies/:id/documents` — lists all documents for a policy (type, created_at, url)
- [ ] AC-5: Only policies in ACTIVE or AMENDED status can generate attestations; DRAFT returns 409
- [ ] AC-6: MinIO bucket `policy-documents` created with lifecycle rule: 7-year retention (ACPR archive requirement)

## Technical Notes

- PDF generation: `github.com/jung-kurt/gofpdf` or `github.com/go-pdf/fpdf` (lightweight, no CGO)
- HTML template alternative: `html/template` → wkhtmltopdf — avoid (CGO, large image)
- MinIO client: `github.com/minio/minio-go/v7`
- MinIO endpoint from env: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` (via ESO/Vault)
- Object key pattern: `policies/{policy_id}/attestation-{yyyyMMddHHmmss}.pdf`
- `policy_documents` table in `V3__documents.sql`: id, policy_id, type, minio_key, created_at

## Definition of Done

- [ ] Code implements all ACs
- [ ] L0: golangci-lint passes
- [ ] L1: unit test — PDF generation with mock data produces non-empty byte slice
- [ ] L1: unit test — MinIO client mocked; correct bucket/key pattern verified
- [ ] PR merged to `staging`

## Tasks

- [ ] TASK-1: Write `migrations/V3__documents.sql`
- [ ] TASK-2: Write `internal/documents/pdf_generator.go` (template + render)
- [ ] TASK-3: Write `internal/documents/minio_store.go` (upload + presigned URL)
- [ ] TASK-4: Write `internal/api/handlers/document_handler.go`
- [ ] TASK-5: Create MinIO bucket + lifecycle rule (via minicloud-gitops manifest or startup code)
- [ ] TASK-6: Write unit tests

## Dependencies

- Depends on: S002 (domain model), S003 (API layer), S004 (status check)
- Blocks: REC-POL-01 (attestation is part of acceptance test)
