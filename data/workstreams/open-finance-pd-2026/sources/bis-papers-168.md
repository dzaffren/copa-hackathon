<figure>

BIS

</figure>

<figure>
</figure>

# BIS Papers No 168

Opening doors to open
finance: evidence from the
international experience

by Hakan Eroglu, Giulio Cornelli, Jon Frost, Friederike
Rühmann and Vatsala Shreeti
Monetary and Economic Department

March 2026

JEL classification: O33, D43, G21.
Keywords: Open finance, financial inclusion,
competition, data sharing

The views expressed in this publication are those of the authors and do not
necessarily reflect the views of the BIS or its member central banks.

This publication is available on the BIS website (www.bis.org).

Bank for International Settlements 2026. All rights reserved. Brief excerpts may be
reproduced or translated provided the source is stated.

# Opening doors to open finance: evidence from the international experience

Hakan Eroglu, Giulio Cornelli, Jon Frost, Friederike Rühmann and Vatsala Shreeti1
March 2026

## Abstract

Open finance is transforming the financial system, with rapid adoption in several
jurisdictions in the years since its introduction. By enabling the sharing and use of
customer-permissioned data, open finance can foster innovation, competition and
financial inclusion. Early evidence highlights a role for open finance in breaking
through data silos, reducing information asymmetries and driving venture capital
investment. Successful implementation depends on standardised data sharing
protocols and interoperability that enable seamless payment system connectivity and
data exchange, all underpinned by robust regulatory frameworks. This paper
examines international experiences with open finance, shedding light on its impact
on competition, market entry and financial access, while discussing the challenges
that remain.

Keywords: open finance, financial inclusion, competition, data sharing.
JEL codes: O33, D43, G21.

1
Hakan Eroglu (hakan.eroglu@bisih.org) is an Adviser at the Bank for International Settlements
Innovation Hub (BISIH) Hong Kong Centre and leads BISIH's Project Aperta for cross-border data
portability. Giulio Cornelli (giulio.cornelli@bis.org) is an Economist in Financial Markets at the Bank
for International Settlements (BIS). Jon Frost (jon.frost@bis.org) is Head of Innovation and the Digital
Economy at the BIS and a research affiliate of the Cambridge Centre for Alternative Finance (CCAF).
Friederike Rühmann (fruehmann@worldbank.org) is a Senior Financial Sector Specialist at the World
Bank and a Secondee to the BIS Financial Stability Institute (FSI). Vatsala Shreeti
(vatsala.shreeti@bis.org) is an Economist in Innovation and the Digital Economy at the BIS. The
authors thank Tom Carpenter (Mastercard), Matheus Rauber Coradin (Central Bank of Brazil), Derya
Demirbüker (Interbank Card Center of Türkiye), Shalini Gupta (Sahamati), Anton Joachim (Open
Banking Limited, UK), Young Jin Kim (Korea Financial Telecommunications and Clearing Institute) and
Nicky Valind (Konsentus) for providing data. The authors would like to thank Iñaki Aldasoro, Elif Cansu
Akoğuz, Yulia Burkova, Maria Teresa Chimienti, Valeria Garcia, Guillermo Galicia Rabadan, Gaston
Gelos, Kiran Gopinath, Linda Jeng, Rudraksh Kansal, Leonardo Luna, Alejo Macaya, Fredesvinda
Montes, Harish Natarajan, Rafaela Nougeira, Bénédicte Nolens, Ariadne Plaitakis, Alex Rizzi and Hyun
Song Shin for valuable comments, and Alison Arnot for editorial support. The views expressed here
are those of the authors and do not necessarily reflect those of the BIS or the World Bank.

## 1. Introduction

Data are the lifeblood of modern economic decision-making, driving innovation and
growth. Yet access to (personal) data remains uneven across different actors in the
economy, and users (data subjects) often have limited control over their data and
how they are used. In response, many jurisdictions are rethinking how data are shared
and governed to empower users and broaden participation in the digital economy.
In the financial sector, many authorities have introduced open banking or open
finance initiatives.

Open finance refers to the sharing and use of customer-permissioned data by
financial institutions with third-party firms, other financial institutions and developers,
to build applications and services.2 Open banking is a narrower concept and refers to
the sharing and use of customer-permissioned data by banks with such third parties.
Both can include both "read access" and "write access" to data. Read access allows
for service provision based on viewing or reading the data. Write access allows for
service provision based on modifying the data. Open finance practices can arise from
customer demands or as a result of policies. Some of the first mandated open banking
and open finance initiatives include the United Kingdom (UK) Open Banking
framework (Fingleton Associates and ODI (2014)); the European Union (EU) Second
Payment Services Directive (PSD2) (EU (2015)) with a stronger focus on payments; and
Australia's Consumer Data Right, which adopts an economy-wide open data
approach (Productivity Commission (2017), Farrell (2023).3 Over time, other
jurisdictions like Brazil, India, South Korea and Türkiye have adopted similar
frameworks. By 2024, 95 jurisdictions had some form of an open banking or finance
policy framework in place with varied objectives, like promoting competition and
innovation and enhancing consumer protection and financial inclusion (CCAF (2024),
CGAP et al (2024).4

2
Throughout this paper, "open finance" refers to both open banking and broader open finance
initiatives. Whereas open banking focuses primarily on bank accounts, open finance extends further
to cover a broader range of financial products, including insurance, securities and mortgages. An
even broader concept, used in some cases, is "open data", which may cover customer-permissioned
data sharing in other industries beyond the financial sector - such as healthcare, utilities,
telecommunications or taxes. See Graph A.1 in the appendix.

3
In other jurisdictions, like the United States, some market-driven bilateral agreements to share
financial data, particularly between banks and financial technology (fintech) companies, emerged
prior to any regulation. Data access and sharing initially developed through market-led
arrangements, eg bilateral agreements and connectivity based on application programming
interfaces (APIs). There were implementations aligned with the Financial Data Exchange (FDX)
standard, as well as legacy non-API techniques such as screen scraping used by some fintech
aggregators. Section 1033 of the Dodd-Frank Wall Street Reform and Consumer Protection Act gives
consumers a right to access information on their financial products and services and to authorise
third parties to access that information on their behalf. The Consumer Financial Protection Bureau
(CFPB) has advanced this through rulemaking.

4
Meanwhile, 52% of Alliance for Financial Inclusion (AFI) members (spanning 88 countries) are still in
the initial exploration phase of open finance, and 4% have fully implemented frameworks (AFI Digital
Financial Services Working Group (2024)). Members' top motivations include improving financial
inclusion and customer choice (each 21%), followed by innovation (20%) and enhanced competition
(16%) (AFI (2025). Regulation has been an enabler of such frameworks and is not just a reaction to
innovation (OECD (2024)).

Open finance policies emerged largely as a response to the growing concerns
about data monopolies and lack of competition in payment markets. Large financial
institutions generate and control vast amounts of data, which can then feed into
improving existing services and providing new ones. New services can generate even
more data, which can be used to further entrench market dominance by large
financial institutions.5 This can create barriers to competition and innovation. Open
finance seeks to break this loop by promoting data portability and interoperability,
allowing consumers to share their financial data securely with third-party providers
(see Vives (2019)). This shift aligns with broader efforts to create a more inclusive,
competitive financial ecosystem while addressing the risks posed by data-driven
monopolies.6

In this paper, we provide evidence on the international experience with open
finance. We draw on new data from jurisdictions with advanced open finance
frameworks, as well as from academic research. We show that in some jurisdictions
where open finance frameworks are operational, they have facilitated the entry of new
types of intermediaries, like third-party financial technology (fintech) firms and large
technology companies (big techs). Open finance has also promoted greater customer
choice through tailored financial products and services and enhanced access for
individuals and firms to financial services, notably new payment methods, and credit.
While there are certainly challenges in implementation, and policy frameworks have
had to adapt to experience, early evidence has been broadly positive.

We contribute to the literature on open banking and open finance (see eg Xie
and Hu (2024) and Jeng (2023) by collecting this international evidence in one place.
This complements studies that focus on one jurisdiction (eg Alok et al (2024), Babina
et al (2025) and World Bank (2024)). We also shed light on whether theoretical
predictions (eg Jones and Tonetti (2020), He et al (2023) and Goldstein et al (2023))
are borne out in practice. We show that, in some cases, there are measurable changes
in jurisdictions with open finance. But additional work will be needed to better
understand that causal impact of policies and further effects as these frameworks are
rolled out and adapted.

The paper is organised as follows. Section 2 outlines the origins of open banking
and open finance initiatives. Section 3 presents international evidence on the
adoption of open finance and describes its impact on competition, entry of new
providers, venture capital (VC) investment and access to credit. Section 4 discusses
challenges and lessons to date. Finally, section 5 concludes.

## 2. Origins and adoption of open finance and open banking

Before full-fledged regulatory frameworks, open banking existed in rudimentary
forms in private sector practices. This included third-party providers using techniques

5
In the context of large technology (big tech) companies' entry into finance, such a dynamic is often
called the data-network-activities (DNA) loop (BIS (2019)).

6
Risks include cyber threats, privacy breaches, data misuse, algorithmic bias, market concentration and
unclear accountability that can undermine consumer protection and ecosystem stability if not
governed effectively (Bonvino and Giorgino (2026).

such as "screen scraping" or "reverse engineering", which allowed their customers to
transfer data into their budgeting, lending and payment apps.7 As concerns around
persistent data monopolies in the financial sector gained traction, calls grew for
consumer-permissioned data sharing via standardised application programming
interfaces (APIs), either through regulatory intervention or through private
initiatives.8

Rather than relying on screen scraping, reverse engineering or bilateral file
transfers, APIs allow systems to communicate automatically. This communication
takes place under clear technical rules that specify how requests are made (eg for
account balances or payment initiation) and how responses are returned. This ensures
that customer-permissioned data are shared in a consistent, secure and auditable
way, while banks retain control over authentication, monitoring and access
management. APIs form the backbone of scalable and interoperable open finance
ecosystems and are the primary mechanism through which third-party providers can
access and exchange data with larger financial institutions. Standardised APIs go one
step further by simplifying integration for all stakeholders, enabling broad
participation, lowering technical barriers for new financial services providers and
minimising duplication of effort.9

Jurisdictions have followed a diverse set of approaches to open banking and
open finance, driven by their unique goals. These approaches can be classified into
three broad categories: (i) regulatory-driven prescriptive approaches, requiring banks
to share customer-permissioned data using eg unified technical API standards and
third parties to register with supervisors; (ii) facilitative approaches, where authorities
publish guidelines and recommended practices;10 and (iii) market-driven approaches,
where no explicit rules require or prohibit data sharing. In the third case, the
ecosystem evolves largely through commercial private sector arrangements (BCBS
(2019)). The choice of regulatory approaches can depend on various factors, including

7
Screen scraping refers to the practice of using customers' online banking credentials, with their
consent, to log into on their behalf and extract data directly from a bank (or financial institution)
website. Reverse engineering involves analysing existing banking interfaces or software to replicate
their functionality or enable data access without relying on official documentation or standardised
APIs. This is often used by third parties prior to the introduction of open banking frameworks.

8
APIs are the "set of routines, protocols and tools for building software applications" that provide
standardised interfaces for secure data exchange between banks and third parties (BCBS (2019)).

9
Open banking and open finance can serve as so-called digital public infrastructure (DPI) by providing
shared, interoperable rails that enable secure data exchange and service connectivity across financial
participants. Built on technical building blocks such as open API standards, digital identity and
consent layers, trust and governance frameworks, and connectivity and aggregation services, these
infrastructures support reliable data portability and service interoperability. By embedding common
protocols for authentication, authorisation and data management, open finance can act as
foundational digital infrastructure. This supports enhancing competition, inclusion and innovation
while maintaining user trust and financial system resilience. For insights on this in the Indian context,
see D'Silva et al (2019).

10
Facilitative approaches vary in how actively regulators get involved, ranging from light-touch
guidance (eg Singapore's non-binding MAS API Playbook or New Zealand's early industry-led
Payments NZ model) to more proactive encouragement (like Hong Kong's phased Open API
Framework that sets expectations without mandating participation). This spectrum shows that
regulators can influence progress while keeping data sharing voluntary, distinguishing facilitative
models from prescriptive ones (Monetary Authority Singapore (2016), Payments New Zealand (2026),
HKMA (2018)). For an overview of approaches by jurisdiction, see Graph A.2 in the appendix.

banking sector concentration, quality of digital infrastructure, cultural norms and laws
around data privacy and the broader political economy of the jurisdiction. Notably,
all of these approaches can be implemented through either centralised or
decentralised technical architectures.11

The EU was among the first to formalise open banking through PSD2, which
created a harmonised regime for third-party access to payment accounts. It required
banks to provide both read and write permissions (account information and payment
initiation services) underpinned by strong customer authentication. PSD2 exemplifies
the regulatory mandate approach. The UK also followed this approach in parallel to
PSD2 by mandating the nine largest banks to fund and implement a common $\mathrm { A P I }$
standard and central directory. This mandated technical interoperability and
governance, driving adoption at scale (The Paypers (2019)).

Other jurisdictions have adopted facilitative frameworks that support open
banking development through voluntary participation and industry coordination,
rather than through regulatory mandates. Authorities typically promote
standardisation and interoperability by issuing guidelines, technical playbooks and
phased roadmaps, while leaving the market to determine adoption speed and scope.
For instance, the Monetary Authority of Singapore (MAS (2016)) encourages open
data exchange through its API Playbook, which provides governance principles,
common data standards and consent frameworks without mandating bank
participation. It also provides complementary initiatives, such as SGFinDex, which
enable individuals to aggregate and share their financial data across institutions.
Similarly, the Hong Kong Monetary Authority (HKMA (2018) launched its Open API
Framework in phases, beginning with open product data and gradually expanding to
include customer and transactional interfaces. These facilitative approaches can foster
innovation and interoperability through shared technical infrastructure, connectivity
and trust frameworks, while allowing flexibility for market-led evolution.

There are also examples of the third approach. In the United States, open banking
has historically evolved through market-led initiatives, with financial institutions and
fintechs forming bilateral data sharing arrangements using private aggregation
services. However, this landscape may shift, as the Consumer Financial Protection
Bureau (CFPB) finalised the Personal Financial Data Rights rule in late 2024 under
Section 1033 of the Dodd-Frank Act, establishing a regulatory framework for
consumer-permissioned data sharing (Arner et al 2025)). The CFPB has since
reopened the rulemaking process to modify and refine this framework, signalling a
transition from a market-based model towards a more regulated one (CFPB (2025).

Concurrently with the adoption of open banking and open finance initiatives,
their use is rising rapidly. While data on adoption are not universally available, and

11
In a centralised architecture, as in India and Türkiye, a single entity or common infrastructure
manages key functions such as directories, trust/identity verification or data switching between
providers (eg financial institutions) and recipients (eg third-party providers), simplifying participation
and interoperability but creating dependency on that central node. By contrast, a decentralised
architecture, as seen in Europe's PSD2 implementation and Brazil's open finance model, relies on
direct bilateral connections via standardised APIs between data holders and users, offering greater
flexibility but potentially raising coordination costs and implementation burdens for each ecosystem
participant (World Bank (2024).

do not always use comparable definitions, data on users and API calls can be
illustrative. 12

Among the G20 jurisdictions for which data are available - Australia, Brazil, India,
Korea, the UK, Türkiye and the US - Korea has the highest open finance adoption
(Graph 1.A), with 36 million subscribers, 194 million registered accounts and an
average of 20 API calls per person per month as of December 2023.13 The swift
advance in Korea may be driven by its mature digital payments ecosystem and the
widespread use of personal finance management apps, which had already integrated
with earlier forms of open banking (CCAF (2025), World Bank (2024). Per capita use

## API-based open finance is taking off in several jurisdictions around the world Graph 1

<figure>

A. Number of open finance users is rising ... 1

B. ... along with more open finance API calls

% of population

No of API calls

No of API calls per capita

50

0.10

60

40

0.08

40

30

0.06

20

0.04

20

10

0.02

0

0

0.00

2021

2022

2023

2024

2025

2022

2023

2024

API users:

BR

GB

IN
KR

API calls per month (Ihs):

$B R$

$G B ^ { 2 }$

IN (rhs)3

TR

US

$\mathrm { K R } ^ { 4 }$

$\mathrm { T R } ^ { 2 }$

</figure>

1
For BR, based on stock of active consents. For GB, based on total number of users. For IN, based on cumulative number of accounts linked.
For KR, based on total number of API subscribers as of December 2023. For US, based on cumulative number of users. 2 Based on successful
API calls. 3 Estimated as incremental consents fulfilled multiplied by 10. This corresponds to the number of data fetches facilitated through
these consents in the lifetime of a consent. 4 Based on average total number of API calls in a day as of December 2023.

Sources: IMF, World Economic Outlook; BKM - the Interbank Card Center of Türkiye; Financial Data Exchange, "FDX hits 94 million accounts,
CFPB publishes FDX's standard-setting application", 2024; Korea Financial Telecommunications & Clearings Institute; openbanking.org.uk;
openfinancebrasil.org.br; Sahamati; authors' calculations.

12
Adoption of open finance can be measured in various ways, from basic indicators such as the number
of registered users and API call volumes to more advanced system performance metrics, including
success rates and response times. An API call refers to any transaction that involves secure, customer-
permissioned data exchange using an API. This can be used as a measure of the intensity of use of
open finance by individuals and businesses. See BIS (2020). Broader assessments may also track
ecosystem coverage (eg participating institutions and data types), user behaviour patterns (such as
consent activity) and market development (including active third-party providers and use-case
uptake). For example, in Brazil authorities track headline indicators, such as participating institutions,
registered customers and active consents, alongside more detailed measures like API call volumes,
success rates and the distribution of calls across data types. They also distinguish between consent
creation and actual data sharing, helping to identify the difference between nominal adoption and
real use (Zetta (2024)).

13
This is nearly 70% of the population. Note that the number of subscribers likely includes some double
counting, as the same individual may subscribe to or hold accounts with multiple financial institutions.
Data source: Korea Financial Telecommunications & Clearings Institute (KFTC).

is highest in Brazil with 55 calls per user per month in March 2025 (Graph 1.B). That
may reflect the relative ease of integration of open finance transactions with other
widespread services, such as fast payments. Other jurisdictions, like the UK and US,
are catching up, as seen in the number of users and API calls. India and Türkiye are
also seeing quick growth in open finance use, but from a much lower base. Australia
recorded around 13 API calls per capita for the banking sector in December 2025.14

Low adoption rates remain a persistent challenge for open finance in many
jurisdictions. "Read-only" open banking may attract a small, financially savvy segment,
while models that include payment initiation, such as in the UK, see faster uptake.
Open finance can scale more effectively when embedded in everyday payments
rather than offered solely as a data sharing tool (Lux and Zhao (2025)). 15

## 3. Impact on market entry, competition and financial inclusion

Despite being in early stages, open finance is facilitating the entry of new providers
of financial services and new business models. In the EU and the UK, for instance, over
4,500 third-party providers of financial services have entered the market for retail
financial services as of December 2024 (Graph 2.A). The vast majority operate across
borders, through the EU's so-called passporting rules.

14
Data are taken from the Australian Consumer Data Right performance dashboard
(https://www.cdr.gov.au/performance), selecting "Banking" as the sector and using the monthly view
of "API Invocations" (API calls). Calculation: 374 million API calls + 28.2 million population = ~ 13 API
calls per capita (December 2025).

15
Reimsbach-Kounatze and Molnar (2024) offer additional evidence explaining why the uptake of data
portability remains limited despite the presence of formal portability rights. Survey findings indicate
that both awareness and actual usage of such rights under general data protection frameworks are
low. Users are frequently discouraged by the complexity of the processes involved, concerns about
potential risks and the effort required to actively manage data transfers. In contrast, open banking
regimes have achieved significantly higher levels of usage by embedding data portability in
standardised, API-based mechanisms that operate seamlessly in the background and are directly
connected to specific services. This distinction between user-driven portability and integrated,
service-oriented data sharing helps clarify why the mere existence of formal rights has not resulted
in widespread adoption.

## Open finance and related policies are promoting greater competition

Graph 2

A. In Europe, more third-party providers (TPPs)1 have
entered the market

<figure>

Number of TPPs

Cumulative number of switches, in millions

4,000

11

3,000

10

2,000

9

1,000

8

0

7

2020

2021

2022

2023

2024

2021

2022

2023

2024

Number of TPPs:

Home-regulated

Passported

Cumulative current account switches

</figure>

B. In the UK, over 11 million people have switched
accounts with a dedicated switching service

1 TPPs active in the European Union (EU) and United Kingdom (UK) operating within the home market or across borders using "passporting".
The drop in December 2020 corresponds to the withdrawal of the eIDAS certificates of UK TPPs as the Brexit transition period ended on
31 December 2020 (for further details see Financial Conduct Authority, "FCA announces changes to open banking identification requirements".
11 March 2020; and Banfico, "Brexit, elDAS revocation and FCA changes to open banking identification requirements", 24 November 2020.

Sources: Konsentus, Third Party Provider Open Banking Tracker; Pay.UK; authors' calculations.

Open finance and related initiatives are helping consumers to switch providers
more easily.16 In the UK, the average length of a customer banking relationship is
14 years. This is a full two years longer than the average (romantic) domestic
relationship, at 12 years (Fenton (2020)). Open finance frameworks can make it easier
for clients to "port" data, including know-your-customer information and other
verified identity and financial account data, from one provider to another. Data
portability allows customers, with their explicit strong customer authentication and
consent, to authorise the secure transfer or reuse of data relating to products and
services that fall within the scope of the open finance ecosystem. The data are then
transferred from one institution or service provider to another through standardised,
encrypted APIs, ensuring privacy and control over personal information. This can
simplify account opening and facilitate the transfer of recurring payments or standing
instructions, reduce frictions in switching between providers and enable more
integrated cross-provider financial services journeys in an open finance environment.
While not formally part of the open finance framework, a related UK initiative - the
Current Account Switch Service - has helped over 11 million individuals to switch
current accounts among over 50 banks and building societies (Graph 2.B). This
underscores the extensive user demand for such services that can be further
promoted by open finance. 17

16
Recent theoretical work also shows that open banking and open finance can enhance competition in
credit markets but increase prices in payments markets. See Akoğuz et al (2025). This points to the
need to account for cross-market spillovers when analysing the global effects of open banking
policies.

17
The service is owned and operated by Pay.UK Ltd, a non-profit limited company that operates UK
interbank payment systems.

In some cases, open finance policies can have a measurable impact on
investment and on firms' access to credit. With a sample of 21 jurisdictions with open
banking policies and using a staggered event study, Babina et al (2025) find that
fintech VC funding increased (in volume and number of projects) significantly in the
year following the introduction of the policies (Graph 3.A). This increase in VC funding
for fintech companies underscores that open banking policies may be able to reduce
barriers to entry and encourage smaller financial services providers to enter the
market. Open finance may also benefit financial inclusion. 18 For the UK specifically,
Babina et al (2025) find that the open banking policy allowed small and medium-sized
enterprises (SMEs) to form new credit relationships with non-bank lenders, although
the gains are the largest for the firms that had access to credit previously (Graph 3.B).
Other recent work shows that open banking enables small businesses to diversify the
types of assets that they use as collateral (eg accounts receivable or inventory) and
enhances credit provision to underserved and younger firms (Yu (2024), Xiong
(2024).19

Open banking and open finance are expanding worldwide, but effects are not
uniform across jurisdictions, sectors and business models. One recent survey (World
Economic Forum and CCAF (2025)) finds a range of views: some fintechs find them
effective (29%), while others report limited usefulness or availability (24% ineffective;
23% unavailable but beneficial). Perceptions also differ by region and sector, with
European, Middle East and North African (MENA) and Asia-Pacific fintechs generally
more positive (42%, 33% and 31% effective, respectively). Overall, fintechs in
advanced economies view frameworks more favourably than emerging market and
developing economies (34% vs 23%). Furthermore, sectors like digital capital raising
show the greatest dissatisfaction (40% ineffective), while high-satisfaction sectors
include lending (39% effective), payments (36%) and wealth tech (37%).

The impact of open finance on financial inclusion goes beyond firms. When
borrowers who are deemed risky gain control over their personal data, they tend to
disclose their payment information more frequently. This increased transparency
leads to higher loan approval rates, lower interest rates and lower ex post defaults
(Nam (2023)). As users assert more control over their data, they become more
confident in sharing data with fintechs. This leads to fintechs offering lower loan rates,
in particular to traditionally underserved groups (Doerr er al (2023)). Further, when
lenders have access to more granular, real-time financial data, credit allocation can
become more efficient, reducing information asymmetries and costs, for both new
entrants such as fintechs and incumbents like banks (Bianchi et al 2024; Alok et al
(2024).20

18
Financial inclusion can be defined as universal access to, and use of, a wide range of reasonably priced
financial services. While this is often equated with access for individuals or households to transaction
accounts, it neglects the much wider issues of access for individuals, households and (small)
businesses to the full range of financial services. See Frost et al (2021).

19
Note that in addition to the credit expansion effect, Xiong (2024) highlights an important trade-off
between screening efficiency and screening cost that arises due to open banking policies.

20
Beyond effects on fintech investment, credit access and financial inclusion, open finance can also
influence bank valuations. Akyildirim et al (2025) examine stock market reactions of more than 3,400
banks in G12 countries following open finance-related announcements and find that bank stocks
typically decline around announcement dates. This may reflect concerns about competition and
compliance costs.

## Competition in lending is driving investment and SME lending

Graph 3

A. Open finance policies have driven fintech investment1

<figure>
<figcaption>B. Open finance led to greater lending to UK SMEs2</figcaption>

USD mn

Number of new lending relationships

2

0.04

0.03

1

0.02

0

0.01

-1

0.00

-2

-0.01

-5 -4 -3 -2 -1 0 1 2
Years after open banking initiative

2015

2016

2017

2018

2019

Year

Ln(fintech VC investment):

Point estimate
95% confidence intervals

New lending relationships:

Point estimate
95% confidence intervals

</figure>

1 Changes in the natural logarithm (ln) of fintech venture capital (VC) investment activity before and after the passage of open finance policies
in 21 jurisdictions. 2 Changes in new lending relationship formation for small and medium-sized enterprises (SMEs) affected by the UK
Commercial Credit Data Sharing (CCDS) policy.

Source: Babina et al (2025).

Within the umbrella of open banking and open finance frameworks, payments
data have played a particularly salient role. By facilitating the sharing of digital
payments data, open finance can provide lenders with high-frequency, verifiable
information on borrowers who may lack formal credit histories. Evidence from India
shows that incorporating digital payments data can improve the prediction of loan
delinquency, strengthening both underwriting and post-disbursal monitoring of
credit (Rishabh (2026). Data from digital payments can also expand access to capital
from fintech lenders at cheaper interest rates (Ghosh et al (2025)). Evidence from
China shows that adoption of digital payments enhances financial inclusion and
access to credit through the portability of payments data (Ouyang (2021)).

### 4. Challenges and lessons to date

The benefits of open finance are tangible, but implementation has not been without
challenges. Experience to date highlights significant differences across regimes which
eventually influence their success. Core challenges are around standardisation in data
sharing, data governance and the transition from open banking to open finance,
alongside the absence of a clear regulatory mandate in some jurisdictions (IIF 2025)).
Other challenges include commercial misalignment, insufficient consumer trust and

legacy technical systems that may make incumbent institutions cautious in sharing
data.21

A key issue is the absence of data sharing standards that are both politically
enforceable and technically harmonised. Differences across jurisdictions in the
structure and implementation of open finance reflect policy choices shaped by
national contexts. In jurisdictions with facilitated or market-led approaches, where
regulation is minimal or absent, there can be slower adoption and higher compliance
costs for firms as they navigate inconsistent standards and limited coordination. By
contrast, those mandating standardised APIs have enabled smoother implementation
of open banking. For example, the UK's approach has improved interoperability and
reduced integration costs for third-party providers, fostering greater innovation
(CMA (2017)). In Türkiye, non-standard market practices prior to regulation posed
significant barriers to interoperability. Localising standards and building centralised
infrastructure enabled a more structured rollout and reduced friction for participants.
Overall, mandating well-defined technical standards is a prerequisite for scalable and
interoperable open finance.

Moreover, ensuring fairness in data sharing between traditional institutions and
new entrants, including fintech and big tech firms, remains a key policy concern.
Banks are mandated under regulations like PSD2 in the EU to share customer financial
data with third-party providers, such as fintechs, when customers consent. This is
intended to foster innovation and competition.22 However, non-banks, fintech
companies or big techs are not subject to equivalent obligations, even though some
of them may hold vast amounts of data that are relevant for the financial sector.
Asymmetric data sharing and access can cause market distortions, hamper regulatory
clarity or reinforce the DNA loop in the case of big techs providing financial services.
Recent theoretical research shows that if open banking policies empower fintechs
disproportionately, borrowers can be worse off (He et al (2023).23 Moreover, consent
alone may be insufficient to protect consumers and may need to be be
complemented by a robust data and consumer protection framework. This includes
effective oversight, privacy-by-design measures and safeguards against risks arising
from eg data analytics and algorithms (Natarajan 2023)).

A distinct challenge is expanding from open banking, focused only on transaction
data, to open finance. Broader frameworks, covering insurance, pensions, investments
and mortgages, face gaps in regulation, complex data protection regimes and higher
infrastructure costs, particularly for smaller institutions. An important effort in this
direction is the design and implementation of data frameworks, which underpin
stability, consumer protection and innovation. Ultimately, advancing open finance
policies requires regulatory clarity, resilient infrastructure and institutional
coordination.

While open finance is primarily implemented at the domestic level, the rising
cross-border mobility of individuals and businesses reveals a key gap. Specifically,

21
Murray and Buckenham (2025) note that some of these challenges have complicated the shift
towards a fully functioning open finance system in the UK, for instance.

22
One approach adopted in certain jurisdictions is to make participation mandatory. While this
approach has generally helped address the historical concentration of data among incumbents, there
is currently no evidence to suggest that it is a necessary condition for achieving a level playing field.

national API infrastructures and data sharing practices may not be sufficient for
individuals and businesses that straddle borders to access financial services in line
with their needs. Supporting cross-border access to financial services requires striking
a balance between data sovereignty imperatives and interoperability between
domestic open finance infrastructures, alignment on technical standards, consent
management systems and governance models to enable secure and user-
permissioned cross-border portability of financial data.24 Bonvino and Giorgino
(2026) argue that the open finance ecosystem can unlock greater innovation,
competition and long-term sustainability when all stakeholders actively collaborate
and co-evolve by harmonising standards, sharing data responsibly and jointly
developing infrastructure and governance frameworks. The challenges of doing this
are, naturally, even greater for stakeholders in different jurisdictions.

Meanwhile, ensuring wide participation in open finance and addressing
structural (behavioural) barriers to adoption remain key. Evidence from Brazil shows
that adoption is lower among less-educated and low-income individuals (CGAP
(2023)). Adoption rates also vary by gender, with men more likely to use open finance
than women.25 In other cases, willingness to share data remains limited even when
benefits are clearly presented. For example, when respondents were shown potential
advantages such as improved loan terms or higher credit limits, only 27% indicated
that they would share data to obtain those benefits (CGAP (2023). $I n \quad I n d i a , a \quad C G A P$
survey shows similar trends. Of approximately 2,000 smartphone users, only 12% were
familiar with account aggregators and 20% were willing to share financial data
(Salman and Fernandez Vidal (2024). Both awareness and willingness were markedly
lower among women, rural residents and individuals with lower levels of education.
Among loan applicants, only 10% reported using the account aggregator mechanism
despite significant efficiency gains reported by financial service providers.

Finally, data access pricing is emerging as an important next stage in the
evolution of open finance policies. Recent policy discussions have focused on how
data should be valued and priced. For example, in 2025 JPMorgan introduced fees
for third-party providers to access its consumer data, prompting renewed attention
to the economic implications of data sharing arrangements (Shevlin (2025). In the
EU, ongoing deliberations on the scope of the Financial Data Access (FiDA) regulation,
including proposals to exclude certain large technology firms, reflect broader
concerns about market structure, eligibility criteria and reciprocity of access (Moens
and Tamma (2025)). The proposed FiDA regulation represents a transformative but
challenging shift towards an EU-wide open data economy. It would significantly
expand PSD2 by mandating real-time access to a broad range of financial data, with
the aim of empowering customers and stimulating innovation (Euro Banking
Association (2025). These developments have revived debates over whether
measures perceived as protecting incumbent institutions could inadvertently limit
competition and innovation. An opposing view is that pricing mechanisms can be
viewed as legitimate compensation for the maintenance of proprietary infrastructure,

24
Project Aperta by the BIS Innovation Hub explores innovative approaches to global interoperability,
offering harmonised features, functionalities, use cases, security protocols, operating procedures and
trust frameworks to support cross-border data portability in open finance.

25
This may reflect differences in risk aversion and preferences towards data sharing. See Armantier et
al (2025).

cyber security investments and the operational costs associated with secure data
sharing systems.

### 5. Conclusion

Overall, jurisdictions' experiences suggest that realising the promise of open finance
hinges on further refining open banking and open finance frameworks over time. The
concept of open finance has been around for some time, but for many jurisdictions,
implementation is still in its early days.26 In this light, authorities can continue to learn
from the experience of peer jurisdictions. Open finance holds strong potential to
enhance consumer empowerment, promote competition, drive innovation and
advance financial inclusion, while requiring careful risk mitigation.

There are a number of open questions where further research will be needed.
While the initial evidence highlights the benefits of open finance in fostering fair
competition, innovation and financial inclusion, more work is needed to understand
the long-term impacts on market structure, financial intermediation and consumer
welfare. Moreover, the role of data protection, privacy frameworks and pricing
mechanisms for data access in shaping the adoption and success of open finance
initiatives remains underexplored. Future research could examine the trade-off
between data sovereignty/privacy and gains from open finance initiatives. Another
interesting avenue to explore could be how variations in open finance frameworks
across jurisdictions affect consumer trust and participation in financial markets.

Advancing open finance will also require deeper investigation of key
performance indicators. This could include providing incentives to market
participants, improving consent management mechanisms and establishing clear
liability frameworks to ensure transparency, security and accountability (OECD 2023).
Open finance has the potential to bridge critical data and market gaps by expanding
beyond sharing of consumer data to include SME transaction-level information,
particularly sex-disaggregated data for women-owned businesses and alternative
data for SME credit scoring. Leveraging these data sources globally could advance
financial inclusion by offering tailored financial products and services and closing
credit gaps for underserved enterprises. It could also inform research on how inclusive
data sharing frameworks can strengthen economic resilience and foster inclusive
growth.

Addressing these research gaps will be critical to designing resilient, inclusive
and trustworthy open finance ecosystems that balance innovation with consumer
protection and market integrity.

26
See Graph A.3 in the appendix for a timeline of implementation in different jurisdictions. In some
jurisdictions, eg India, the ecosystem is beginning to mature and show a wider variety of providers
and use cases (see Graph A.4 in the appendix). As more jurisdictions launch open banking and open
finance frameworks and as these are adopted, the evidence base will grow further.

## References

Akoğuz, E C, T Roukny and T Vadasz (2025): "The Interoperability of Financial data",
available at SSRN: https://ssrn.com/abstract=5169568.

Akyildirim, E, S Corbet, A Mukherjee and M Ryan (2025): "Global perspectives on open
banking: regulatory impacts and market response", Journal of International Financial
Markets, Institutions and Money, vol 101, no 102159, June.

Alliance for Financial Inclusion (AFI) (2025): "Policy development and implementation
guide for inclusive open finance", Guideline Note, no 56, January.

Alok, S, P Ghosh, N Kulkarni and M Puri (2024): "Open banking and digital payments:
implications for credit access", National Bureau of Economic Research (NBER) Working
Paper Series, no 33259, December.

Armantier, O, S Doerr, J Frost, A Fuster and K Shue (2025): "Nothing to hide? Gender
and age differences in willingness to share data", BIS Working Papers, no 1187,
October.

Arner, D, C Wang, R Buckley and D Zetzsche (2025): "Building open finance: from
policy to infrastructure", Centre for Finance, Technology and Entrepreneurship (CFTE)
Academic and Industry Paper Series, January.

Babina, T, S Bahaj, G Buchak, F De Marco, A Foulis, W Gornall, F Mazzola and T Yu
(2025): "Customer data access and fintech entry: early evidence from open banking",
Journal of Financial Economics, vol 169, no 103950, July.

Bank for International Settlements (BIS) (2019): "Big tech in finance: opportunities and
risks", Annual Economic Report 2019, chapter III, June.

\- (2020): Enabling open finance through APIs, report by the BIS Consultative
Group on Innovation and the Digital Economy (CGIDE), December.

Basel Committee on Banking Supervision (BCBS) (2019): Report on open banking and
application programming interfaces (APIs), Bank for International Settlements,
November.

Bianchi, M, S Garz, M Bouvard, H Özyilmaz and A Yamashita (2024): How can
interoperability improve financial inclusion? Research insights from the FIT IN Initiative,
Toulouse School of Economics.

Bonvino, C and M Giorgino (2026): "Strategic data democratization toward open
finance: stakeholders' implications", Financial Innovation, vol 12, no 35,
https://doi.org/10.1186/s40854-025-00878-6.

Cambridge Centre for Alternative Finance (CCAF) (2024): The global state of open
banking and open finance, University of Cambridge Judge Business School.

(2025): The APAC state of open banking and open finance report, University of
Cambridge Judge Business School, June.

CGAP (2023): "Open finance: lessons from Brazil", webinar, November,
https://www.cgap.org/events/open-finance-lessons-brazil.

Competition and Markets Authority (CMA) (2017): The retail banking market
investigation order 2017, gov.uk, February.

Consumer Financial Protection Bureau (CFPB) (2025): "Required rulemaking on
personal financial data rights", August, https://www.consumerfinance.gov/personal-
financial-data-rights.

D'Silva, D, Z Filkova, F Packer and S Tiwari (2019): "The design of digital financial
infrastructure: lessons from India", BIS Papers, no 106, December.

Doerr, S, L Gambacorta, L Guiso and M Sanchez del Villar (2023): "Privacy regulation
and fintech lending", BIS Working Papers, no 1103, June.

Euro Banking Association (2025): "Financial Data Access (FIDA): the catalyst for an
open data economy?", EBA Open Finance Working Group.

European Union (EU) (2015): "Directive (EU) 2015/2366 of the European Parliament
and of the Council of 25 November 2015 on payment services in the internal market,
amending Directives 2002/65/EC, 2009/110/EC and 2013/36/EU and Regulation (EU)
No 1093/2010, and repealing Directive 2007/64/EC (text with EEA relevance)",
25 November.

Farrell, S (2023): Banking on data: evaluating open banking and data rights in banking
law, Kluwer Law International.

Fenton, A (2020): "UK adults more loyal to banks than their partners, study finds",
Yahoo Finance UK, 11 September.

Fingleton Associates and Open Data Institute (ODI) (2014): Data sharing and
open data for banks, a report for HM Treasury and Cabinet Office, September.

Frost, J, L Gambacorta and H S Shin (2021): "From financial innovation to inclusion",
International Monetary Fund Finance & Development, Spring.

Ghosh, P, B Vallee and Y Zeng (2025): "FinTech lending and cashless payments",
Journal of Finance, November.

Goldstein, I, C Huang and L Yang (2023): "Open banking under maturity
transformation", mimeo.

Government of Argentina (2025): "Decreto 353/2025" ("Decree 353/2025"), 22 May,
https://servicios.infoleg.gob.ar/infolegInternet/anexos/410000-
414999/413071/texact.htm.

He, Z, J Huang and J Zhou (2023): "Open banking: credit market competition when
borrowers own the data", Journal of Financial Economics, vol 147, no 2.

Hong Kong Monetary Authority (HKMA) (2018): Open API framework for the banking
sector and the launch of open API on HKMA's website, July,
https://www.hkma.gov.hk/eng/news-and-media/press-releases/2018/07/20180718-
5/f.

Institute of International Finance (IIF) (2025): "Data frameworks - trends and
implementation challenges in open banking, open finance, and open data", IIF Data
Notes, March.

Jeng, L (ed) (2023): Open banking, Oxford University Press.

Jones, C and C Tonetti (2020): "Nonrivalry and the economics of data", American
Economic Review, vol 110, no 9.

Lux, M and O Zhao (2025): "Open banking: lessons, challenges, and opportunities",
Georgetown University's Psaros Center for Financial Markets and Policy, McDonough
School of Business, January.

Moens, B and P Tamma (2025): "EU to block big tech from new financial data sharing
system", Financial Times, 21 September, https://www.ft.com/content/6596876f-c831-
482c-878c-78c1499ef543.

Monetary Authority of Singapore (MAS) (2016): "ABS-MAS Financial World Finance-
as-a-service: API playbook", https://www.mas.gov.sg/-/media/mas/smart-financial-
centre/api/absmasapiplaybook.pdf.

Murray, A and J Buckenham (2025): "Open banking and open finance in the UK",
Financial Conduct Authority Research Note, October.

Nam, R (2023): "Open banking and customer data sharing: implications for fintech
borrowers", Leibniz Institute Sustainable Architecture for Finance in Europe (SAFE)
Working Papers, no 364, October.

Natarajan, H (2023): "Regulatory aspects of open banking: the experience thus far",
European Economy, April.

Organization for Economic Co-operation and Development (OECD) (2024):
"Competition, fintechs and open banking: an overview of recent developments in
Latin America and the Caribbean", OECD Roundtables on Competition Policy Papers,
https://doi.org/10.1787/20758677.

(2023): "Open finance policy considerations", OECD Business and Finance
Policy Papers, https://doi.org/10.1787/19ef3608-en.

Ouyang, S (2021): "Cashless payment and financial inclusion", available at SSRN,
no 3948925.

Payments New Zealand (2026): "World class payments for Aotearoa New Zealand",
https://www.paymentsnz.co.nz/.

Petralia, K, T Philippon and T Rice (2019): "Banking disrupted? Financial intermediation
in an era of transformational technology", Geneva Reports on the World Economy, no
22, September.

Productivity Commission (2017): "Data availability and use: overview and
recommendations", Australian Government Productivity Commission Inquiry Report,
no 82, 31 March.

Reimsbach-Kounatze, C and A Molnar (2024): "The impact of data portability on user
empowerment, innovation, and competition", OECD Going Digital Toolkit Notes,
no 25, https://doi.org/10.1787/319f420f-en.

Rishabh, K (2026): "Beyond the bureau: interoperable payment data for loan screening
and monitoring", Journal of Financial Intermediation, vol 65, no 101196.

Salman, A and M Fernandez Vidal (2024): "Trust and awareness will be key for open
finance adoption in India", CGAP blog, 19 April.

Shevlin, R (2025): "JPMorgan Chase is right to charge fintechs for data access", Forbes,
16 July, https://www.forbes.com/sites/ronshevlin/2025/07/16/jpmorgan-chase-is-
right-to-charge-fintechs-for-data-access/.

The Paypers (2019): The open banking report 2019 - insights into the global open
banking landscape, September.

Vives, X (2019): "Digital disruption in banking", Annual Review of Financial Economics,
vol 11.

World Bank (2024): "Open finance: the Korean experience and opportunities and
challenges for the East Asia and Pacific Region", May.

World Economic Forum and CCAF (2025): The future of global fintech: from rapid
expansion to sustainable growth - second edition, Insight Report, June.

Xie, C and S Hu (2024): "Open banking: an early review", Journal of Internet and Digital
Economics, vol 4, no 2.

Xiong, R (2024): "Open banking and fintech lending: evidence from a crowdfunding
platform", https://ssrn.com/abstract=5046894.

Yu, T (2024): "Data as collateral: open banking for small business lending",
https://papers.ssrn.com/sol3/papers.cfm?abstract id=5147405.

Zetta (2024): "Lessons for the future of open finance: the view from Brazil",
https://somoszetta.org.br/wp-

content/uploads/2024/09/Zetta OpenFinance ENG DIGITAL V1.pdf.

## Appendix

## Further insights on open finance

This appendix gives further information on open finance.27 To start with, Graph A.1
visualises the scope of open banking, which includes deposit accounts and electronic
wallets (e-wallets). Open finance can include a broader set of products, including
loans, insurance and investment products like stocks or exchange-traded funds (ETFs).
An even broader term is open data, which may include data from other sectors
beyond financial services, such as utilities, telecom, transit, etc. Each of these can
include both read access and write access. Read access allows for service provision
based on viewing or reading the data. Write access allows for service provision based
on modifying the data.28

<figure>
<figcaption>Scope of open banking and open finance Graph A.1</figcaption>

Open finance

Open data

Open banking

Product scope

Utilities

Loans

Mortgages

Stocks

Product
scope

Deposit
account

E-wallet

Telecom

Read access: account balance, transaction
history

Insurance

ETFs

Write access: payment initiation on bank
deposit account, or an e-wallet

Read access: open banking scope, plus product pricing and
contract information, etc

Write access: open banking scope, plus open
an account, terminate/apply for a mortgage,
buy/sell stocks, etc

Transit

</figure>

Sources: CCAF (2024); BIS.

27
There are several other definitions of open banking and open finance. The Geneva Report for World
Economy describes "open banking" as a consumer right to access and share banking data (Petralia
et al (2019)). The Basel Committee's 2019 report similarly defined open banking as banks sharing
customer-permissioned data with third parties (BCBS (2019). The World Bank, International Monetary
Fund (IMF), Bank for International Settlements (BIS) and CGAP define open finance as an innovation
that facilitates customer-permissioned access to and use of customer data held by financial
institutions in order to provide new and enhanced services and develop innovative business models
(CGAP et al (2024)).

28
For example, in the EU, PSD2 already provides a form of "write access" by allowing licensed payment
initiation service providers (PISPs) to initiate payments directly from a user's bank account with their

Jurisdictions differ in their approach to open finance. The Cambridge Centre for
Alternative Finance (CCAF) gives an overview (Graph A.2). Some jurisdictions, such as
the European Union, the United Kingdom, Canada, Brazil and India, have regulation-
led approaches, while others, including China, Japan and Mexico, have market-led
approaches. The United States is classified by CCAF as regulation-led, given the work
of the Consumer Financial Protection Bureau (CFPB), but in practice it may be better
classified as market-led. Argentina has transitioned from a market-driven approach
to a regulation-led approach by implementing formal open finance rules through
government decree and central bank regulation (Government of Argentina (2025)).
The CCAF does not classify the framework in Korea, where open finance is widely
adopted.

<figure>
<figcaption>Open finance frameworks: regulation-led vs market-driven Graph A.2</figcaption>

$K$

Market-Driven

$F$

Regulation-Led

</figure>

The use of this map does not constitute, and should not be construed as constituting, an expression of a position by the BIS regarding the legal
status of, or sovereignty of any territory or its authorities, to the delimitation of international frontiers and boundaries and/or to the name and
designation of any territory, city or area.

Note that the overview does not cover all known open finance frameworks, and classifications may change over time.

Source: CCAF (2024).

The stage of development of open banking and open finance also differs.
Graph A.3 gives a timeline with the years in which regulatory changes were enacted
to facilitate the transition towards an open banking or open finance ecosystem,
including live implementation in some jurisdictions. In most cases, jurisdictions begin
by establishing a regulatory framework for open banking before expanding their
financial services to encompass a broader range of products and services under the
open finance model. A few (eg Bahrain, India) moved in parallel. As of the latest
assessment, only a few have progressed to the stage of implementing open finance.

consent, demonstrating how modifying data (eg submitting a payment order) enables automated
services.

As more jurisdictions launch live open banking or open finance systems, there will be
a larger evidence base to assess the impact in practice.

Timeline for year of legislation/regulation/guidance issues vs year of live
implementation of open banking and open finance

Graph A3

<figure>

Open banking

Open finance

Country

2018

2019

2020

2021

2022

2023

2024

Bahrain

India

Australia

Korea

Israel

Brazil

Nigeria

Jordan

UAE

Open banking
legislation
passed

Open
banking
live

Open finance
legislation
passed

Open
finance
live

</figure>

<table>
<tr>
<th>Country</th>
<th colspan="2">2016 2017</th>
<th>2018</th>
<th>2019</th>
<th>2020</th>
<th>2021</th>
<th>2022</th>
<th>2023</th>
<th>2024</th>
</tr>
<tr>
<td>UK</td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Australia</td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Bahrain</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>EU</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Korea</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>India</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Georgia</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Türkiye</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Israel</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Brazil</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Nigeria</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Jordan</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Saudi Arabia</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>UAE</td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
</table>

Source: CCAF (2024).

India, which was a relatively early mover, gives insights into the maturation $o f$
open finance ecosystems. Over time, the financial system has seen broader use cases,
greater provider diversity and more structured governance models. For instance,
third-party providers are enabling an expanding range of financial services, reflecting
a more diverse set of intermediaries entering the open finance ecosystem. While non-
bank financial corporations continue to hold the lion's share, accounting for nearly
two-thirds of third-party providers, stockbrokers have gained some share relative to
investment advisers and private banks (Graph A.4.A). Moreover, while consents for
lending surpassed the 100 million mark in the early months of 2025, their share in the
total number of consents has steadily declined since the end of 2023, suggesting that,
over time, users are increasingly adopting other financial services as well
(Graph A.4.B).

Graph A.4

## In India, the open finance ecosystem is maturing

### A. A growing diversity of different TPPs

<figure>
<figcaption>B. Consents for lending have passed 100 million</figcaption>

100

80

60

40

20

0

Q3 2022 Q1 2023 Q3 2023 Q1 2024 Q3 2024 Q1 2025

</figure>

Percentage of consents by TPP category:

Non-banking financial corporations

P2P lending

Registered investment advisers

Public banks

Private banks

Stockbrokers

Others
1

%

<figure>

Millions

%

100

82.5

80

80.0

60

77.5

40

75.0

20

72.5

0

1

1

70.0

2022

2023

2024

Consents for lending/credit:

Cumulative (Ihs)

% of total consents (rhs)

</figure>

TPP = third-party providers.

1 Includes alternative investment fund, asset management companies, housing finance companies, insurance brokers, insurance companies,
prepaid payment instruments and trade receivables discounting systems, regional rural banks and small finance banks and retirement advisers.

Source: Sahamati.

## Glossary

Application programming interface (API): the set of routines, protocols and tools
for building software applications that provide standardised interfaces for secure data
exchange between banks and third parties. Open API: an interface that provides a
means of accessing data based on a public standard.

Open banking: the sharing and leveraging of customer-permissioned data by banks
with third parties.

Open data: the sharing and leveraging of customer-permissioned data in other
industries beyond the financial sector - such as healthcare, utilities,
telecommunications or taxes.

Open finance: the sharing and leveraging of customer-permissioned data by
financial institutions with third parties. While open banking focuses primarily on bank
accounts, open finance covers a broader range of financial products, including
insurance, securities and mortgages.

Private API: an interface that provides a means of accessing data based on a private
standard.

PSD2: the European Union's Second Payment Services Directive.

Reciprocity: a characteristic of data sharing in an open finance ecosystem in which
eligible entities participate both as data holders and as data users (ie contribute to
and benefit from shared data). In open banking, open finance and open data contexts,
data sharing should only happen with customer consent.

Reverse engineering: analysing existing banking interfaces or software to replicate
their functionality or enable data access, without relying on official documentation or
standardised APIs. This is often used by third parties prior to the introduction of open
banking frameworks.

Screen scraping: the practice of using customers' online banking credentials, with
their consent, to log into on their behalf and extract data directly from a bank (or
financial institution) website.

TPPs: Third-party providers, including fintechs, big techs and other (usually non-
bank) intermediaries.

