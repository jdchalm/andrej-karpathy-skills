# Sensitivity review (LLM second pass)

Run only on pages the scan marked `flagged`. Run it locally or with a model you trust with the content; the point of the deterministic scan is to keep hard hits away from any model at all.

## Prompt

```
You are reviewing a note that a pattern scan flagged as possibly sensitive.
Read VAULT-SPEC.md "Sensitivity" for the definition. Decide one of:

  clean    - nothing in the note identifies a person or client together
             with money, health, legal, or employment details, and there
             are no credentials or account identifiers.
  private  - it does.
  unsure   - you cannot tell without context the note does not contain.

Output exactly:

  verdict: <clean|private|unsure>
  reason: <one sentence quoting the specific phrase that decided it>

Do not edit the note. Do not summarise it. If the scan hit is a false
positive (an order number that looks like a card number, a public price
list), say so in the reason.
```

## After the pass

Append each verdict to `scan-report.md` next to the page. A human reads the report and promotes. `unsure` is treated as `private` until someone says otherwise.
