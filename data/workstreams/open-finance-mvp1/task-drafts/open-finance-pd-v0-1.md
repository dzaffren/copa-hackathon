# Open Finance

## Policy Document (Working Draft — v0.1)

## PART A OVERVIEW

## 1 Introduction

1.1 The financial sector's move toward customer-centric services depends on
the ability of financial institutions to share customer financial information
across providers in a manner that is safe, informed, and reversible. Open
finance provides the regulated framework through which such sharing takes
place, subject to prudential and conduct safeguards commensurate with the
risks involved.

1.2 To realise the benefits of open finance while preserving the confidence of
customers and the stability of the financial system, financial institutions
must—

1.2(a) obtain and act only on the customer's informed and revocable permission
to share financial information with a third party;

1.2(b) apply security controls proportionate to the sensitivity of the data
being shared and the criticality of the sharing channel;

1.2(c) preserve accountability for customer outcomes across the chain of
regulated and unregulated participants; and

1.2(d) maintain the integrity, availability, and confidentiality of shared
information at all stages of its lifecycle.

## 2 Applicability

2.1 This policy applies to all licensed financial institutions in Malaysia
that hold customer financial information, and to their participation as data
holders or data recipients in open-finance arrangements.

## PART B PERMISSION FRAMEWORK

## 3 Customer permission

3.1 A financial institution shall not disclose or receive customer financial
information under an open-finance arrangement unless the customer has granted
express permission that is—

3.1(a) informed by a plain-language disclosure of the scope, purpose,
recipient, and duration of the sharing;

3.1(b) affirmative, requiring a deliberate act by the customer and not implied
from acceptance of general terms and conditions;

3.1(c) granular at the level of the specific data categories to be shared;
and

3.1(d) revocable by the customer at any time, with effect no later than one
business day from the date of revocation.

3.2 A financial institution shall retain records of every permission granted,
modified, or revoked for a period of not less than seven years from the date
of the last action taken on that permission.

## PART C API STANDARDS AND SECURITY

## 4 Application programming interfaces

4.1 A financial institution acting as a data holder shall expose customer
financial information through application programming interfaces (APIs) that
conform to industry-recognised specifications adopted by the Bank.

4.2 A financial institution shall ensure that its open-finance APIs implement,
at minimum—

4.2(a) mutual authentication of the data holder and the data recipient using
certificates issued by a directory of participants recognised by the Bank;

4.2(b) authorisation flows compliant with the Financial-grade API (FAPI)
profile of the OAuth 2.0 framework, or an equivalent standard approved by the
Bank;

4.2(c) end-to-end encryption of data in transit; and

4.2(d) mechanisms to detect and respond to abnormal request patterns,
including credential stuffing and enumeration attacks.

## PART D GOVERNANCE AND ACCOUNTABILITY

## 5 Board and senior management responsibilities

5.1 The board of a financial institution shall approve the institution's
open-finance strategy and shall satisfy itself that appropriate controls are
in place before the institution participates in any open-finance
arrangement.

5.2 Senior management shall establish clear internal lines of accountability
for open-finance operations, including—

5.2(a) a designated senior officer accountable for open-finance risk
management;

5.2(b) escalation pathways for incidents arising from open-finance
arrangements; and

5.2(c) periodic reporting to the board on the performance and risk profile
of the institution's open-finance participation.

## PART E LIABILITY AND SUPERVISORY REPORTING

## 6 Allocation of liability

6.1 A financial institution shall ensure that its open-finance arrangements
allocate liability between the data holder and the data recipient in a manner
that—

6.1(a) does not diminish the customer's rights to redress under existing
consumer-protection frameworks; and

6.1(b) is disclosed to the customer in a plain-language form as part of the
permission process required under paragraph 3.1(a).

## 7 Incident reporting

7.1 A financial institution shall report to the Bank any open-finance
incident that materially affects the confidentiality, integrity, or
availability of customer financial information, no later than twenty-four
hours from the point at which the institution is first aware of the
incident.

7.2 The report required under paragraph 7.1 shall include, at minimum, the
nature of the incident, the number of customers affected, the immediate
containment measures taken, and an initial assessment of root cause.
