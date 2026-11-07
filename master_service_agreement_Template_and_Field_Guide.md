---
# Suggested PDF export settings (Pandoc-compatible)
papersize: letter
fontsize: 9pt
geometry: margin=0.55in
linestretch: 0.96
colorlinks: false
---

> **PDF length requirement:** The rendered PDF should target 10–15 pages maximum. Use compact paragraph spacing, restrained heading sizes, tight table spacing, and avoid standalone cover pages or unnecessary page breaks. Preserve clause wording, field explanations, and material risk guidance. If the first render exceeds 15 pages, edit for concision and remove repeated explanations or secondary examples before reducing readability. Always render and check the final page count; Markdown alone cannot guarantee pagination across different PDF converters.

# Master Services Agreement (MSA)

## Wheels / Fleet Management Services --- Reusable Template and Clause-by-Clause Field Guide

> **Purpose.** This is a reusable drafting and analysis template for
> master services agreements involving fleet management, vehicle leasing
> and related mobility services. It is designed for use when reviewing
> or preparing agreements in a Wheels, Inc.-type business context.
>
> **Source basis.** The uploaded 14-page *Logistics Services Agreement*
> is the structural reference for this template. It contains provisions
> on parties and recitals; services and covered products; service
> locations; rates, invoices and disputes; service standards; ownership
> and custody; reporting and review meetings; special materials and
> legal compliance; insurance; liability and indemnification;
> confidentiality; term and termination; force majeure; governing law;
> notices; amendments; assignment; and execution. The source is a 2009
> agreement between Limited Logistics Services, Inc. and Express, LLC.
> It is **not** a Wheels agreement.
>
> **Important distinction.** Fleet-management topics in this template
> (vehicle ordering, leasing, maintenance, fuel, driver support,
> accident management, telematics, title, registration, remarketing and
> vehicle disposal) are industry-oriented drafting prompts. They are not
> represented as confirmed Wheels contractual terms, internal policies,
> current product offerings, or approved legal positions. Confirm the
> actual contracting entity, service catalogue, operating model and
> current legal requirements for each transaction.
>
> **Legal review required.** This is a working template and educational
> field guide, not legal advice or a ready-to-sign contract. Governing
> law, tax, leasing/credit, consumer/driver, insurance, privacy,
> telematics, employment, transportation, environmental and
> vehicle-title rules vary by jurisdiction. Have qualified counsel and
> the relevant Wheels commercial, operations, risk, tax, insurance and
> information-security stakeholders approve each document.

------------------------------------------------------------------------

# 1. How to use this template

1.  Replace every `{{PLACEHOLDER}}` with transaction-specific
    information.
2.  Choose only the service modules that are actually in scope. Delete
    unused optional clauses and schedules.
3.  Make the main agreement the stable legal framework. Put variable
    service descriptions, rates, vehicle lists, service levels,
    locations and operating procedures in schedules or statements of
    work (SOWs).
4.  Make sure the order of precedence is explicit where the MSA, SOW,
    vehicle schedule, pricing schedule, supplier terms and policies
    conflict.
5.  Do not leave alternative drafting options, explanatory notes,
    square-bracket comments or unresolved placeholders in the execution
    copy.
6.  Confirm that every commercial promise has an operational owner, a
    measurable definition, a reporting method and a remedy or escalation
    route.
7.  Use the review checklist at the end before sending the agreement for
    signature.

## 1.1 What the example agreement tells us --- and what it does not

The source agreement is a logistics services agreement. It is useful as
a model for contract structure and several general commercial
mechanisms:

-   defined service scope and schedules;
-   treatment of existing and future products;
-   designated service/distribution facilities;
-   monthly invoicing and detailed invoice-dispute mechanics;
-   general service standards and advance notice of material changes;
-   customer ownership of products held by the service provider;
-   reporting, audit access and recurring review meetings;
-   operational policies for shortages, damages, claims and
    investigations;
-   compliance with laws and insurance;
-   reciprocal indemnities, liability limitations and waiver of
    subrogation;
-   confidentiality, term, termination, force majeure and boilerplate
    clauses.

It does **not** establish how Wheels prices or delivers fleet services,
who owns or leases vehicles in a particular Wheels transaction, how
maintenance networks are selected, how fuel cards are administered, how
accident claims are handled, or what liability limits Wheels accepts.
Those matters must be established from the actual deal documents and
approved business positions.

## 1.2 Fleet-management service modules to consider

Select only what applies to the transaction.

  -----------------------------------------------------------------------
  Module                              Typical subject matter to define
  ----------------------------------- -----------------------------------
  Fleet consulting and policy         Fleet strategy, vehicle policy,
                                      driver eligibility,
                                      total-cost-of-ownership analysis

  Vehicle sourcing and ordering       Approved makes/models,
                                      configuration, ordering, delivery,
                                      substitutions, lead times

  Vehicle leasing / funding           Lessee, lessor, term, rentals,
                                      deposits, residual value, early
                                      termination

  Registration and licensing          Title, registration, plates,
                                      permits, taxes and renewals

  Maintenance and repairs             Preventive maintenance, repair
                                      authorisation, network, pricing,
                                      warranty and downtime

  Tyres and roadside assistance       Replacement rules, emergency
                                      response, coverage area, service
                                      hours

  Fuel and charging                   Fuel cards, charging accounts,
                                      transaction controls, fraud,
                                      reconciliation

  Accident and claims management      Reporting, towing, repair, insurer
                                      coordination, liability and claims
                                      support

  Driver services                     Driver communications, eligibility,
                                      onboarding, safety and support

  Telematics and fleet data           Devices, location data,
                                      diagnostics, usage, retention,
                                      access and permitted analytics

  Replacement / rental vehicles       Eligibility, duration, cost
                                      allocation, availability and return

  Vehicle remarketing / disposal      End-of-lease inspection, sale,
                                      proceeds, condition standards,
                                      title transfer

  Reporting and analytics             Fleet dashboards, utilisation,
                                      spend, exceptions, emissions and
                                      savings

  Electric vehicle services           Charging infrastructure, battery
                                      condition, incentives, range,
                                      charging data

  Transition and exit                 Data migration, vehicle handover,
                                      open work orders, supplier transfer
                                      and continuity
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 2. Document control and transaction particulars

  Field                               Insert transaction-specific value
  ----------------------------------- ---------------------------------------
  Agreement title                     `{{MASTER_SERVICES_AGREEMENT_TITLE}}`
  Agreement reference                 `{{CONTRACT_ID}}`
  Version / date                      `{{VERSION_AND_DATE}}`
  Customer legal entity               `{{CUSTOMER_LEGAL_NAME}}`
  Provider legal entity               `{{PROVIDER_LEGAL_NAME}}`
  Effective Date                      `{{EFFECTIVE_DATE}}`
  Initial service commencement date   `{{SERVICE_COMMENCEMENT_DATE}}`
  Initial term end date (if fixed)    `{{INITIAL_TERM_END_DATE}}`
  Primary country / jurisdiction      `{{COUNTRY_AND_JURISDICTION}}`
  Fleet size at commencement          `{{INITIAL_FLEET_COUNT}}`
  Covered vehicle classes             `{{VEHICLE_CLASSES}}`
  Covered operating territories       `{{COUNTRIES_STATES_REGIONS}}`
  Contract owner                      `{{BUSINESS_OWNER}}`
  Legal reviewer                      `{{LEGAL_REVIEWER}}`
  Commercial approver                 `{{COMMERCIAL_APPROVER}}`
  Operations approver                 `{{OPERATIONS_APPROVER}}`

**Why these fields matter:** They provide a reliable contract identity,
distinguish signing from service commencement, and expose the scale and
geographic footprint of the arrangement. Fleet count, vehicle class and
territory can materially affect pricing, service capacity, insurance and
regulatory requirements.

------------------------------------------------------------------------

# 3. Master Services Agreement --- drafting template

## MASTER SERVICES AGREEMENT

This Master Services Agreement (the **"Agreement"**) is entered into on
`{{AGREEMENT_DATE}}` (the **"Effective Date"**) by and between:

1.  **`{{CUSTOMER_LEGAL_NAME}}`**, a `{{ENTITY_TYPE}}` organised under
    the laws of `{{PLACE_OF_FORMATION}}`, with its registered office at
    `{{CUSTOMER_REGISTERED_ADDRESS}}` (**"Customer"**); and
2.  **`{{PROVIDER_LEGAL_NAME}}`**, a `{{ENTITY_TYPE}}` organised under
    the laws of `{{PLACE_OF_FORMATION}}`, with its registered office at
    `{{PROVIDER_REGISTERED_ADDRESS}}` (**"Provider"**).

Customer and Provider are each a **"Party"** and together the
**"Parties"**.

### Field guide --- parties

-   **Full legal entity name:** The contract must bind the correct legal
    entity, not merely a brand, trade name, parent company or business
    division.
-   **Entity type and formation jurisdiction:** Identifies the legal
    form and place of incorporation/organisation.
-   **Registered office:** Supports formal notices and legal
    identification.
-   **Correct Wheels entity:** Do not assume that "Wheels, Inc." is the
    correct provider or lessor for every transaction. Verify the legal
    entity named in the proposal, order documents, invoices, vehicle
    title/lease documents and signature authority. A parent, affiliate,
    special-purpose entity, lessor, servicing entity or subcontractor
    may have a different role.
-   **Customer entity:** Verify which customer affiliate is responsible
    for payment, vehicle use, driver obligations, insurance and
    indemnities. If several affiliates participate, use a clear
    affiliate accession or multi-entity structure.

## RECITALS

A. Provider is engaged in `{{PROVIDER_BUSINESS_DESCRIPTION}}` and has
represented that it has the experience, personnel, systems, supplier
relationships and authorisations required to provide the Services
described in this Agreement.

B. Customer operates or manages a vehicle fleet for
`{{CUSTOMER_BUSINESS_PURPOSE}}` and wishes to obtain certain fleet
management, vehicle-related and/or mobility services from Provider.

C. The Parties wish to establish the terms governing the Services,
including the allocation of responsibilities for vehicles, drivers,
suppliers, data, costs and operational risks.

**NOW, THEREFORE**, in consideration of the mutual promises and
obligations in this Agreement, the Parties agree as follows.

**Why recitals matter:** They record the commercial context and help
explain the transaction. They should not contain the only statement of a
binding service obligation; operative commitments belong in the clauses
and schedules.

------------------------------------------------------------------------

## Section 1. Definitions and interpretation

### 1.1 Definitions

In this Agreement, unless the context requires otherwise:

-   **"Affiliate"** means an entity that controls, is controlled by, or
    is under common control with a Party, where control means
    `{{CONTROL_DEFINITION}}`.
-   **"Business Day"** means a day other than
    `{{WEEKEND_AND_PUBLIC_HOLIDAY_DEFINITION}}` in
    `{{RELEVANT_LOCATION}}`.
-   **"Confidential Information"** has the meaning in Section 11.
-   **"Driver"** means an individual authorised by Customer to operate a
    Covered Vehicle.
-   **"Covered Vehicle"** means a vehicle included in the fleet and
    scope under Schedule 1 or a subsequently approved vehicle order.
-   **"Fleet Data"** means data relating to vehicles, drivers, vehicle
    use, transactions, maintenance, fuel/charging, claims or fleet
    performance, as further described in Schedule 9.
-   **"Fees"** means the fees, rentals, charges and other amounts
    payable under this Agreement and Schedule 5.
-   **"Services"** means the services expressly described in this
    Agreement, each SOW and the Schedules.
-   **"Service Levels"** means the performance standards and measurement
    rules in Schedule 6.
-   **"Supplier"** means a third party engaged by a Party to provide
    goods or services in connection with the Services.
-   **"Statement of Work" or "SOW"** means a document signed by both
    Parties that describes a specific project, service, scope, fee or
    implementation.
-   **"Vehicle Costs"** means vehicle acquisition, lease, financing,
    registration, maintenance, repair, tyres, fuel, charging, insurance,
    taxes, tolls, fines, disposal and other costs allocated under
    Schedule 5.

Add transaction-specific definitions: `{{ADDITIONAL_DEFINITIONS}}`.

### 1.2 Interpretation

References to a statute include amendments and replacements. Headings
are for convenience and do not affect interpretation. "Including" means
"including without limitation". References to a person include an entity
where appropriate.

### Field guide --- definitions

Definitions prevent the same term being interpreted differently across
legal, operations, finance and fleet teams. Define terms that affect
money, responsibility, service measurement, vehicle custody or risk.
Avoid defining ordinary words unnecessarily. In a fleet agreement, the
terms *vehicle owner*, *registered keeper*, *lessee*, *customer*,
*driver*, *fleet administrator* and *service provider* must not be used
interchangeably unless their meanings are genuinely the same.

## Section 2. Services and scope

### 2.1 Appointment

Customer appoints Provider, and Provider agrees, to provide the Services
described in this Agreement and the applicable SOWs and Schedules,
subject to the terms of this Agreement.

The selected Services are:

-   `{{FLEET_CONSULTING_AND_POLICY_SERVICES}}`;
-   `{{VEHICLE_SOURCING_ORDERING_AND_DELIVERY}}`;
-   `{{LEASING_OR_FUNDING_SERVICES}}`;
-   `{{REGISTRATION_AND_LICENSING_SERVICES}}`;
-   `{{MAINTENANCE_REPAIR_AND_TYRE_SERVICES}}`;
-   `{{FUEL_AND_CHARGING_SERVICES}}`;
-   `{{ACCIDENT_AND_CLAIMS_SERVICES}}`;
-   `{{DRIVER_SUPPORT_AND_REPLACEMENT_VEHICLE_SERVICES}}`;
-   `{{TELEMATICS_AND_DATA_SERVICES}}`;
-   `{{REMARKETING_AND_DISPOSAL_SERVICES}}`;
-   `{{REPORTING_AND_ANALYTICS_SERVICES}}`; and
-   `{{OTHER_SERVICES}}`.

The detailed scope, exclusions, deliverables, assumptions and
dependencies are set out in Schedule 1 and the relevant SOW.

### 2.2 Scope boundaries and exclusions

The following are expressly excluded unless added through a signed
change order: `{{EXCLUDED_SERVICES}}`.

Provider is not responsible for an activity merely because it is related
to fleet management; responsibility must be stated in this Agreement, a
Schedule or an SOW.

### 2.3 Fleet population and eligibility

The initial fleet is described in Schedule 2. Customer may request
additions, removals or substitutions in accordance with
`{{VEHICLE_CHANGE_PROCESS}}`. The Parties shall specify eligibility
rules for vehicle types, age, use, territory, annual mileage, driver
category and any restricted use.

### 2.4 Service territory and operating hours

Services will be provided in `{{COUNTRIES_STATES_REGIONS}}`, during
`{{SERVICE_HOURS_AND_TIME_ZONE}}`, subject to the coverage and
emergency-response provisions in Schedule 6.

### 2.5 Additional services and future requirements

Any new service, vehicle category, territory, material volume or
functionality shall be agreed through a written change order identifying
the scope, fees, implementation date, capacity, service levels,
dependencies, risk allocation and any required amendments.

### Field guide --- scope

This is one of the most important sections. It answers: **What exactly
has the provider promised to do, for which vehicles, drivers, locations
and business units?** A broad phrase such as "fleet management services"
is not enough. Separate services that are performed by the provider from
services merely arranged through a third-party network. List exclusions
so that an operational expectation does not accidentally become an
unpriced contractual commitment.

## Section 3. Vehicle ordering, leasing, title and delivery

### 3.1 Vehicle selection and ordering

Customer shall select vehicles from
`{{APPROVED_VEHICLE_POLICY_OR_CATALOGUE}}`. Provider shall process
approved orders in accordance with the ordering workflow in Schedule 3.
Each order shall specify, as applicable, vehicle make/model,
configuration, accessories, delivery location, estimated delivery date,
lease term, mileage allowance, pricing and any special requirements.

### 3.2 Order approval and cancellation

No vehicle order shall bind Customer unless approved by
`{{AUTHORISED_CUSTOMER_ROLE}}` through `{{APPROVED_ORDERING_CHANNEL}}`.
Cancellation, amendment, delay, manufacturer allocation changes and
related charges shall be handled under `{{ORDER_CANCELLATION_RULES}}`.

### 3.3 Lease and funding structure

For each vehicle, the Parties shall identify the legal and commercial
structure:

-   vehicle owner / title holder: `{{ENTITY}}`;
-   lessor / finance provider: `{{ENTITY}}`;
-   lessee: `{{ENTITY}}`;
-   fleet manager / administrator: `{{ENTITY}}`;
-   permitted users / Drivers: `{{DEFINED_GROUP}}`;
-   lease commencement trigger:
    `{{DELIVERY_ACCEPTANCE_OR_OTHER_EVENT}}`;
-   lease term: `{{MONTHS}}`;
-   annual mileage allowance: `{{MILEAGE}}`;
-   base rental and included services: `{{PRICE_AND_INCLUSIONS}}`;
-   residual value risk bearer: `{{PARTY}}`;
-   end-of-term process: `{{PROCESS}}`.

The detailed financial and legal terms for any lease or financing
arrangement shall be set out in
`{{VEHICLE_LEASE_DOCUMENT_OR_SCHEDULE}}`. If a separate lease document
governs title, payment, repossession or vehicle-specific rights, state
its relationship to this MSA in the order-of-precedence clause.

### 3.4 Title, registration and risk of loss

Legal title to each Covered Vehicle shall be held by `{{TITLE_HOLDER}}`.
Registration shall be in the name of `{{REGISTERED_OWNER_OR_KEEPER}}`,
as permitted by applicable law. Risk of loss, damage, theft and physical
custody shall be allocated as follows: `{{RISK_ALLOCATION}}`.

Nothing in this Agreement shall be interpreted as transferring title
unless the relevant vehicle sale or lease document expressly provides
for such transfer.

### 3.5 Delivery and acceptance

Provider shall coordinate delivery to `{{DELIVERY_LOCATIONS}}`. The
Parties shall define inspection, acceptance, defect notification,
missing accessories, delivery evidence and the treatment of delays in
Schedule 3. Acceptance shall not waive latent defects or rights that
cannot lawfully be waived.

### Field guide --- vehicle legal structure

Do not treat the words *fleet manager*, *lessor*, *owner* and *service
provider* as synonyms. In some arrangements a fleet manager administers
vehicles owned or funded by another entity; in others an affiliated
entity or third-party finance company may be the lessor. The actual
documents determine the structure. This distinction drives title,
repossession, insurance, residual value, tax, depreciation, payment and
end-of-term exposure.

## Section 4. Maintenance, repairs, tyres and roadside assistance

### 4.1 Maintenance services

The responsible Party shall arrange preventive maintenance and repairs
in accordance with the manufacturer's requirements, vehicle policy and
Schedule 4. The schedule shall identify covered work, excluded work,
approved repair networks, authorisation thresholds, service hours and
geographic coverage.

### 4.2 Repair authorisation

Repairs up to `{{APPROVAL_LIMIT}}` may be authorised by
`{{AUTHORISED_PARTY_OR_ROLE}}`. Repairs above that amount require
`{{APPROVAL_PROCESS}}`, except for emergency work reasonably required to
protect people or prevent further damage. Emergency exceptions shall be
documented promptly.

### 4.3 Maintenance pricing and parts

The Parties shall specify labour rates, parts pricing, mark-ups,
discounts, network fees, taxes, warranties, diagnostic charges and any
administrative fees in Schedule 5. The agreement shall state whether the
provider acts as principal, agent, purchasing intermediary or
administrator for each relevant transaction.

### 4.4 Downtime and replacement vehicles

The Parties shall define when a vehicle is considered unavailable,
whether a replacement vehicle is provided, eligibility, class, duration,
geographic coverage, cost bearer and any service-level commitment.

### 4.5 Roadside assistance and tyres

Coverage, response times, call-out limits, geographic exclusions, tyre
replacement criteria and emergency escalation shall be described in
Schedule 4.

### Field guide --- maintenance economics

A low monthly administration fee may not represent the total cost to the
customer. Check whether repair network charges, parts mark-ups,
authorisation fees, towing, replacement vehicles, tyres and emergency
services are included, passed through at cost or charged separately.
Confirm who approves work and who bears the cost of unauthorised
repairs, warranty failures and repeat repairs.

## Section 5. Fuel, charging, tolls, fines and other operating costs

### 5.1 Fuel and charging programmes

Where included, Provider shall administer
`{{FUEL_CARD_OR_CHARGING_PROGRAMME}}` in accordance with Schedule 4. The
Parties shall define eligible users, transaction limits, permitted
products, merchant/network coverage, account controls, card issuance,
lost-card reporting, exception handling and reconciliation.

### 5.2 Transaction data and exceptions

Provider shall make available transaction records showing, where
available, vehicle, Driver or card identifier, date, location, quantity,
unit price, total amount and exception indicators. The Parties shall
define how suspected misuse, duplicate transactions, out-of-policy
purchases and disputed charges are investigated.

### 5.3 Tolls, parking, fines and violations

Responsibility for tolls, parking, congestion charges, traffic fines,
penalties and administrative fees shall be allocated in Schedule 5. The
Parties shall specify the process for identifying the Driver, forwarding
notices, contesting charges, paying amounts and recovering
administrative costs.

### 5.4 Electric vehicle charging

If EV services are in scope, Schedule 4 shall address charging
cards/accounts, home charging reimbursement, public charging networks,
charger installation, electricity tariffs, battery data,
charging-session records, tax treatment and responsibility for equipment
maintenance.

### Field guide --- operating spend

Fuel, charging, tolls and fines can create high-volume, low-value
transactions. The agreement should make transaction-level evidence,
reconciliation frequency, exception ownership, dispute windows and fraud
controls explicit. Define whether the customer pays the supplier
directly or pays the provider as part of a consolidated invoice.

## Section 6. Accident, claims and driver support

### 6.1 Accident reporting and coordination

The Parties shall follow the accident reporting process in Schedule 7.
The process shall state the reporting deadline, emergency contacts,
required information, police/authority reporting, towing, repair
coordination, insurer notification and customer escalation.

### 6.2 Claims handling role

Provider's role shall be limited to the following activities:
`{{CLAIMS_ADMINISTRATION_ACTIVITIES}}`. The agreement shall expressly
state whether Provider has authority to admit liability, settle claims,
appoint counsel, instruct repairers or bind an insurer. No such
authority shall be implied.

### 6.3 Driver support

Driver communications and support shall be provided through
`{{CHANNELS}}`, during `{{HOURS}}`, with response and escalation targets
in Schedule 6. Customer remains responsible for
`{{CUSTOMER_DRIVER_RESPONSIBILITIES}}`, including driver eligibility,
licence validity, conduct and policy compliance, except to the extent
expressly assumed by Provider.

### 6.4 Safety and vehicle use

The Parties shall document driver policy, permitted use, prohibited use,
maintenance responsibilities, incident reporting and consequences of
non-compliance in `{{DRIVER_POLICY_REFERENCE}}`.

### Field guide --- claims and drivers

Separate **claims administration** from **insurance coverage** and
**legal responsibility for an accident**. A provider may coordinate a
repair or claim without becoming the insurer or accepting liability for
the accident. Clarify who communicates with the insurer, who controls
settlement, who pays deductibles and who is responsible for Driver
conduct.

## Section 7. Remarketing, return and end-of-term

### 7.1 Vehicle return

At lease expiry or earlier termination, Customer shall make the vehicle
available for return in accordance with `{{RETURN_PROCESS}}`, subject to
normal wear-and-tear standards set out in Schedule 8.

### 7.2 Inspection and condition

The Parties shall agree inspection standards, inspection provider,
notice, evidence, dispute process, repair estimates and appeal rights.
Charges for excess wear, damage, missing equipment, excess mileage or
late return shall be calculated under Schedule 5.

### 7.3 Sale and remarketing

Where Provider arranges vehicle sale or remarketing, the Parties shall
specify the seller, title-transfer process, sale authority, reserve
price (if any), fees, sale proceeds, taxes, buyer warranties,
disclosures and allocation of any shortfall or surplus.

### 7.4 Residual value and sale proceeds

The Party bearing residual-value risk shall be `{{PARTY}}`. The method
for calculating any gain, loss, shortfall, surplus or adjustment shall
be `{{FORMULA_AND_TIMING}}`.

### Field guide --- end-of-term risk

End-of-lease charges and residual-value exposure can be commercially
significant. Define inspection standards before vehicles are returned,
not after. Identify who bears market-value risk, excess mileage, damage,
missing equipment, late return, disposal costs and title-transfer
delays. Do not assume that a fleet administrator necessarily bears
residual-value risk.

## Section 8. Fees, invoicing, taxes and payment

### 8.1 Fees

Customer shall pay the Fees in Schedule 5. The pricing model shall
identify, as applicable, fixed management fees, per-vehicle fees, lease
rentals, usage charges, transaction fees, pass-through costs, supplier
charges, mark-ups, rebates, credits and one-time implementation fees.

### 8.2 Invoice format and frequency

Provider shall invoice `{{FREQUENCY}}` for the period
`{{BILLING_PERIOD}}`. Each invoice shall include sufficient detail to
reconcile charges to vehicles, services, transactions, dates and
applicable rates. Supporting detail shall be made available through
`{{PORTAL / DATA FILE / OTHER METHOD}}`.

### 8.3 Payment

Customer shall pay valid, undisputed invoices within `{{PAYMENT_TERM}}`
days of receipt, in `{{CURRENCY}}`, to the account designated by
Provider. Late payment interest shall be `{{RATE}}`, subject to
applicable law.

### 8.4 Invoice disputes

Customer shall notify Provider of a good-faith invoice dispute within
`{{DISPUTE_NOTICE_PERIOD}}` days, identifying the disputed item, amount
and reason. Customer shall pay all undisputed amounts by the due date.
The Parties shall work to resolve the dispute within
`{{RESOLUTION_PERIOD}}` days. Any amount determined to be payable shall
be paid within `{{POST_RESOLUTION_PERIOD}}` days.

### 8.5 Pass-through costs and supplier charges

The Parties shall specify whether supplier costs are passed through at
cost, include a disclosed administration fee or contain a mark-up.
Provider shall provide `{{REQUIRED_SUPPORTING_DOCUMENTATION}}`. No
undisclosed mark-up shall apply unless expressly agreed.

### 8.6 Taxes

Fees are `{{INCLUSIVE / EXCLUSIVE}}` of applicable taxes. Each Party
shall be responsible for taxes imposed on its income, employees and
property. Transaction taxes, vehicle taxes, registration charges,
withholding and similar amounts shall be allocated as follows:
`{{TAX_ALLOCATION}}`.

### 8.7 Rate changes

Rates may change only under `{{INDEXATION / REVIEW_MECHANISM}}`, with
`{{NOTICE_PERIOD}}` notice and supporting calculation. Any other change
requires written agreement.

### Field guide --- commercial model

Review the entire cost stack, not only the headline management fee. For
a fleet arrangement, the total cost may include rentals or depreciation,
funding, maintenance, tyres, fuel/charging, insurance, taxes, tolls,
accident deductibles, replacement vehicles, remarketing, administration
and termination charges. Require transparent pricing and enough invoice
data to validate each category.

## Section 9. Service levels, reporting and governance

### 9.1 Service standards

Provider shall perform the Services with reasonable skill, care and
diligence, using appropriately qualified personnel and in accordance
with the Service Levels in Schedule 6.

### 9.2 Reporting

Provider shall provide reports at `{{FREQUENCY}}` covering the agreed
metrics, which may include: - fleet count and vehicle status; - order
placement, delivery lead time and order exceptions; - maintenance spend,
repair turnaround and vehicle downtime; - fuel/charging spend and
exception transactions; - accident frequency, claims status and cycle
time; - vehicle utilisation and mileage; - service desk volumes and
response times; - invoice accuracy and unresolved disputes; - vehicle
return, remarketing proceeds and end-of-term charges; - emissions or EV
metrics, where agreed.

### 9.3 Governance meetings

The Parties shall hold operational reviews `{{FREQUENCY}}`, commercial
reviews `{{FREQUENCY}}` and executive reviews `{{FREQUENCY}}`. Each
meeting shall review performance, risks, incidents, savings, forecasts,
disputes, improvement actions and decisions requiring escalation.

### 9.4 Audit and records

Provider shall maintain accurate records relating to the Services for
`{{RETENTION_PERIOD}}`. Customer, its auditors and regulators (where
applicable) may inspect relevant records on `{{NOTICE_AND_SCOPE}}`,
subject to confidentiality, security and legal restrictions.

### 9.5 Service failures and credits

Where a Service Level is missed, Provider shall report the failure,
perform root-cause analysis, provide a corrective action plan and apply
any service credits or other remedies in Schedule 6. Service credits
shall be `{{SOLE_REMEDY / ADDITIONAL_REMEDY}}` for the relevant failure,
subject to the agreed exceptions.

### Field guide --- performance management

A service level must specify: metric, formula, source data, measurement
period, target, exclusions, reporting deadline, evidence, cure period
and remedy. Avoid a target that cannot be measured from available data.
Distinguish service credits from compensation for other losses and
clarify whether credits are capped.

## Section 10. Responsibilities, dependencies and change control

### 10.1 Customer responsibilities

Customer shall: - provide accurate vehicle, Driver, location and policy
information; - appoint authorised approvers and maintain current contact
details; - ensure Drivers follow the agreed vehicle and safety
policies; - provide timely approvals and decisions; - pay undisputed
amounts when due; and - perform the additional responsibilities in
Schedule 10.

### 10.2 Provider responsibilities

Provider shall: - provide the Services and reports described in this
Agreement; - maintain personnel, systems and supplier arrangements
reasonably necessary for the Services; - manage and monitor its
subcontractors as required by this Agreement; - maintain required
records, licences and insurance; - promptly report material incidents
and service failures; and - perform the additional responsibilities in
Schedule 10.

### 10.3 Dependencies and delays

The Parties shall identify dependencies, including vehicle manufacturer
availability, supplier capacity, Customer approvals, Driver cooperation,
insurer decisions, government processing and accurate data. Relief from
a service commitment shall apply only to the extent a failure is caused
by a documented dependency outside the affected Party's reasonable
control and the affected Party has taken reasonable mitigation steps.

### 10.4 Change control

Either Party may request a change. No change to scope, price, service
level, territory, fleet volume, implementation date or risk allocation
is binding unless recorded in a change order signed by authorised
representatives. The change order shall identify impact, assumptions,
dependencies and effective date.

### Field guide --- accountability

Use a responsibility matrix (RACI or equivalent) to prevent gaps between
Customer, Provider, lessor, manufacturer, repair network, insurer and
Driver. A responsibility should have one accountable owner even where
several parties perform supporting tasks.

## Section 11. Confidentiality

Each Party shall protect the other Party's Confidential Information
using at least the same degree of care it uses to protect its own
similar information, and not less than reasonable care. A receiving
Party may use Confidential Information only to perform or receive the
Services and may disclose it only to personnel, Affiliates, professional
advisers and approved subcontractors who need to know it and are bound
by confidentiality obligations.

Confidential Information does not include information that the receiving
Party can demonstrate: (a) is public through no breach; (b) was lawfully
known without restriction; (c) was independently developed; or (d) was
lawfully received from a third party without a duty of confidence.

If disclosure is legally required, the receiving Party shall, where
lawful, give advance notice and disclose only what is required. On
termination or request, Confidential Information shall be returned or
securely destroyed, subject to lawful retention requirements.

Confidentiality obligations shall continue for `{{PERIOD}}` after
termination; trade secrets shall be protected for as long as they remain
trade secrets under applicable law.

### Field guide

Fleet agreements can involve commercial pricing, employee/Driver
details, vehicle locations, accident reports, supplier rates and
business-sensitive operational data. Define permitted use, permitted
recipients, security, legal disclosure and retention. Confidentiality is
not a substitute for a complete data protection and cybersecurity
schedule.

## Section 12. Data protection, telematics and information security

### 12.1 Data roles and permitted use

The Parties shall document their respective roles for personal data and
Fleet Data in Schedule 9. Provider may use data only for
`{{DEFINED_PURPOSES}}` and shall not sell, disclose, monetise or use
identifiable Driver or vehicle-location data for unrelated purposes
unless expressly authorised and lawful.

### 12.2 Security controls

Provider shall maintain administrative, technical and physical
safeguards appropriate to the sensitivity of the data and the Services,
including
`{{ACCESS_CONTROL_ENCRYPTION_LOGGING_VULNERABILITY_BACKUP_CONTROLS}}`.

### 12.3 Security incidents

Provider shall notify Customer of a confirmed or reasonably suspected
security incident affecting Customer data or the Services within
`{{NOTICE_PERIOD}}` after becoming aware, provide available details,
preserve evidence, cooperate with investigation and take reasonable
remediation steps.

### 12.4 Telematics and location information

Where telematics, GPS, diagnostics or Driver behaviour information is
collected, Schedule 9 shall identify: - data fields and collection
frequency; - purpose and legal basis; - who can access the data; -
whether data is identifiable or aggregated; - retention and deletion
periods; - use for safety, maintenance, analytics or productivity; -
Driver notices and consent/consultation requirements, where
applicable; - restrictions on onward disclosure and cross-border
transfers.

### 12.5 Subprocessors and data return

Provider shall disclose material subprocessors and obtain approval where
required by Schedule 9. At termination, data shall be returned or
securely deleted in the agreed format and timeframe, subject to legal
retention duties.

### Field guide

Telematics and fleet data may reveal an individual's location, work
patterns and behaviour. Treat this as a material privacy and employment
issue, not simply an IT integration. Confirm applicable law, notices,
lawful basis, retention, cross-border processing and customer access
rights. The uploaded source agreement does not contain a modern detailed
privacy/telematics framework; this section is an additional drafting
module.

## Section 13. Compliance, licences and regulatory requirements

Each Party shall comply with laws applicable to its obligations,
including relevant vehicle, road safety, licensing, tax, environmental,
employment, anti-bribery, sanctions, competition, privacy and
recordkeeping requirements.

Each Party shall maintain licences, permits and registrations required
for its own activities and promptly notify the other of any material
suspension, investigation or non-compliance that may affect the
Services.

Additional requirements:
`{{INDUSTRY_AND_COUNTRY_SPECIFIC_REQUIREMENTS}}`.

### Field guide

Avoid a generic compliance clause where the business is subject to
specific requirements. Allocate responsibility for vehicle registration,
roadworthiness, driver licensing, safety inspections, tax filings,
environmental reporting and regulatory notifications. The applicable
rules depend on the country and the legal role of each entity.

## Section 14. Insurance

Each Party shall maintain the insurance it is legally required to
maintain and the policies and minimum limits set out below.

  ------------------------------------------------------------------------
  Insurance        Party                    Minimum limit Key terms /
                   responsible                            evidence
  ---------------- ---------------- --------------------- ----------------
  Commercial       `{{PARTY}}`               `{{AMOUNT}}` `{{TERMS}}`
  general                                                 
  liability                                               

  Auto / motor     `{{PARTY}}`               `{{AMOUNT}}` `{{TERMS}}`
  liability                                               

  Physical damage  `{{PARTY}}`               `{{AMOUNT}}` `{{TERMS}}`
  / comprehensive                                         
  vehicle cover                                           

  Professional     `{{PARTY}}`               `{{AMOUNT}}` `{{TERMS}}`
  indemnity /                                             
  errors and                                              
  omissions                                               

  Cyber / privacy  `{{PARTY}}`               `{{AMOUNT}}` `{{TERMS}}`
  liability                                               

  Workers'         `{{PARTY}}`               `{{AMOUNT}}` `{{TERMS}}`
  compensation /                                          
  employer                                                
  liability                                               

  Other            `{{PARTY}}`               `{{AMOUNT}}` `{{TERMS}}`
  ------------------------------------------------------------------------

A Party shall provide reasonable evidence of required coverage on
request and notify the other Party of cancellation or material reduction
to the extent permitted by the policy and applicable law.

### Field guide --- insurance versus liability

Insurance is a funding mechanism; it does not by itself determine who is
legally liable. Identify who insures the vehicle, who is insured, who
pays deductibles, whether coverage applies across all territories and
permitted Drivers, and whether a lessor or finance provider must be
named as loss payee or additional insured. Check that the contractual
liability allocation is consistent with actual policy coverage.

## Section 15. Representations and warranties

Each Party represents that: - it is duly organised and has authority to
enter into and perform this Agreement; - execution and performance do
not knowingly violate its constitutional documents or another binding
obligation; and - it will perform its obligations in compliance with
applicable law.

Provider additionally warrants that it will perform the Services with
reasonable skill and care and that deliverables will materially conform
to their agreed specifications for `{{WARRANTY_PERIOD}}`.

Additional warranties, if agreed: `{{SERVICE_SPECIFIC_WARRANTIES}}`.

Except as expressly stated, all other warranties are excluded to the
maximum extent permitted by law.

### Field guide

Use warranties that can be tested and tied to an appropriate remedy. Do
not promise that a manufacturer, repairer, insurer or other third party
will perform unless the Provider can control or expressly assumes that
obligation. Distinguish Provider's own services from third-party
products and services.

## Section 16. Limitation of liability

### 16.1 General cap

Subject to the exclusions below, each Party's aggregate liability
arising out of or in connection with this Agreement shall not exceed
`{{CAP_FORMULA}}` during `{{CAP_PERIOD}}`.

### 16.2 Separate or super caps

The following liabilities shall be subject to separate caps, if agreed:

  Risk category                             Cap Period / calculation
  --------------------------------- ----------- ----------------------
  Data protection / cybersecurity     `{{CAP}}` `{{PERIOD}}`
  Confidentiality                     `{{CAP}}` `{{PERIOD}}`
  Intellectual property               `{{CAP}}` `{{PERIOD}}`
  Vehicle damage / custody            `{{CAP}}` `{{PERIOD}}`
  Other                               `{{CAP}}` `{{PERIOD}}`

### 16.3 Excluded loss

Neither Party shall be liable for
`{{INDIRECT_OR_CONSEQUENTIAL_LOSS_CATEGORIES}}`, subject to the agreed
carve-outs and applicable law.

### 16.4 Carve-outs

The cap and excluded-loss provisions shall not apply to
`{{FRAUD_DEATH_PERSONAL_INJURY_WILFUL_MISCONDUCT_OTHER_CARVE_OUTS}}`, to
the extent such exclusion is legally permitted and agreed.

### 16.5 Mitigation

Each Party shall take reasonable steps to mitigate loss for which it
seeks recovery.

### Field guide --- key negotiation points

This is a high-risk clause. Do not accept a cap without testing it
against the maximum plausible exposure. Decide whether the cap is per
event, per year or aggregate; whether it is based on fees, rentals,
vehicle value or a fixed sum; and whether separate caps are needed for
data, confidentiality, physical damage, injury or other risks. Consider
whether vehicle value, third-party claims, deductibles, lost use,
replacement costs and residual-value losses are treated consistently.
Some liabilities cannot lawfully be excluded or capped. Obtain
jurisdiction-specific legal advice.

## Section 17. Indemnification

### 17.1 Customer indemnity

Subject to Section 16, Customer shall indemnify Provider and its
`{{DEFINED_INDEMNIFIED_PERSONS}}` against third-party claims and losses
to the extent arising from `{{CUSTOMER_CAUSES}}`, excluding to the
extent caused by Provider's breach, negligence or wilful misconduct.

### 17.2 Provider indemnity

Subject to Section 16, Provider shall indemnify Customer and its
`{{DEFINED_INDEMNIFIED_PERSONS}}` against third-party claims and losses
to the extent arising from `{{PROVIDER_CAUSES}}`, excluding to the
extent caused by Customer's breach, negligence or wilful misconduct.

### 17.3 Vehicle-specific allocation

The Parties shall expressly allocate claims arising from: - Driver
operation and use of a vehicle; - vehicle defect or manufacturer
recall; - negligent maintenance or repair; - theft, loss or physical
damage; - loading, transport or movement of vehicles; - third-party
supplier acts or omissions; - infringement of third-party intellectual
property; - personal data or security incidents.

The allocation shall be set out in `{{SCHEDULE_REFERENCE}}`.

### 17.4 Indemnity procedure

The indemnified Party shall give prompt notice, provide reasonable
cooperation at the indemnifying Party's cost, and permit the
indemnifying Party to control the defence, subject to rights to
participate and approve any settlement that imposes an admission,
payment or non-monetary obligation on the indemnified Party.

### Field guide

Indemnities should identify the claim type, causal trigger, covered
losses, beneficiaries, defence control, settlement approval and
relationship to the liability cap. In fleet arrangements, carefully
distinguish responsibility for Driver conduct, vehicle condition,
maintenance, third-party repairers, insurance and title. Do not use a
broad indemnity as a substitute for clear operational responsibility.

## Section 18. Subcontractors and supplier network

Provider may use subcontractors and suppliers listed in
`{{APPROVED_SUPPLIER_LIST}}` or appointed under `{{APPROVAL_PROCESS}}`.
Provider remains responsible for performance of its obligations to the
extent specified in this Agreement, notwithstanding use of
subcontractors.

Provider shall maintain appropriate due diligence and oversight for
material subcontractors, including `{{DUE_DILIGENCE_CONTROLS}}`.
Provider shall notify Customer of material changes to critical suppliers
where such changes may affect service, security, compliance or
continuity.

### Field guide

Fleet services often rely on manufacturers, dealers, repair networks,
towing providers, fuel/charging networks, insurers, auction houses and
technology vendors. Identify who contracts with each supplier, who pays,
who manages service failure, whether the Provider is liable for supplier
acts, and whether the Customer has approval or audit rights.

## Section 19. Business continuity and disaster recovery

Provider shall maintain and periodically test a business continuity and
disaster recovery plan appropriate to the Services. The plan shall
address `{{CRITICAL_SYSTEMS_AND_PROCESSES}}`, recovery time objective,
recovery point objective, alternate operating arrangements,
communications, data backup and testing.

Provider shall notify Customer of a disruption affecting the Services
within `{{NOTICE_PERIOD}}` and provide updates at
`{{UPDATE_FREQUENCY}}`.

### Field guide

A fleet service disruption can affect vehicle ordering, maintenance
authorisation, fuel access, Driver support, claims and billing. Identify
critical services and realistic recovery targets. A generic promise to
maintain a continuity plan is not enough unless testing, reporting and
recovery expectations are defined.

## Section 20. Term and termination

### 20.1 Initial term

This Agreement begins on the Effective Date and continues for
`{{INITIAL_TERM}}`, unless terminated earlier in accordance with this
Agreement.

### 20.2 Renewal

The Agreement shall `{{AUTO_RENEW / EXPIRE}}` for successive periods of
`{{RENEWAL_TERM}}`, unless either Party gives `{{NON_RENEWAL_NOTICE}}`
prior written notice.

### 20.3 Termination for cause

Either Party may terminate this Agreement by written notice if the other
Party: - commits a material breach and fails to cure it within
`{{CURE_PERIOD}}` after notice; - becomes insolvent or enters an
analogous proceeding, to the extent termination is lawful; - ceases or
threatens to cease a material part of its business; or - experiences
`{{OTHER_TERMINATION_EVENT}}`.

### 20.4 Termination for convenience

Either Party may `{{OR_MAY_NOT}}` terminate for convenience on
`{{NOTICE_PERIOD}}` written notice, subject to
`{{EARLY_TERMINATION_FEES_AND_TRANSITION_OBLIGATIONS}}`.

### 20.5 Vehicle-specific early termination

Early termination of a vehicle lease or funding arrangement may be
governed by separate vehicle documents. The Parties shall identify early
termination charges, outstanding rentals, market value adjustments,
disposal costs, mileage and damage charges, and any funding break costs
in `{{SCHEDULE_OR_LEASE_DOCUMENT}}`.

### 20.6 Suspension

A Party may suspend affected Services only in the circumstances and
subject to the notice, mitigation and continuity requirements in
`{{SUSPENSION_RULES}}`.

### Field guide --- termination economics

The right to terminate the MSA may not automatically end every vehicle
lease, financing commitment or supplier contract. Map the consequences
at both master-agreement and individual-vehicle level. Model early
termination costs, remaining rentals, vehicle sale proceeds,
residual-value adjustments, open repairs, outstanding claims and data
transition.

## Section 21. Exit assistance and transition

On expiry or termination, Provider shall provide the transition
assistance in Schedule 11 for `{{TRANSITION_PERIOD}}`, including: -
transfer of fleet and Driver records in an agreed usable format; -
status of open orders, maintenance work, claims and invoices; - return
or transfer of vehicles, keys, cards, devices and documents; -
coordination with replacement providers and suppliers; - transfer or
termination of data integrations and access; - support for vehicle
title, registration and lease handover; and - continued critical
services during the agreed transition period.

Fees for transition assistance shall be
`{{INCLUDED / PRE-AGREED RATES}}`.

### Field guide

Exit planning should be designed before the contract starts. Without it,
a customer may be unable to access data, transfer vehicles, close
claims, cancel fuel accounts or move maintenance arrangements smoothly.
Define deliverables, timelines, format, cooperation, cost and
responsibility for each workstream.

## Section 22. Force majeure

Neither Party shall be liable for delay or failure caused by an event
beyond its reasonable control, provided that the affected Party promptly
notifies the other, uses reasonable efforts to mitigate the impact and
resumes performance as soon as practicable. If the event continues for
more than `{{LONG_STOP_PERIOD}}`, either Party may
`{{TERMINATION_OR_ALTERNATIVE_RIGHT}}`.

A Party's lack of funds or ordinary supplier underperformance shall
`{{BE / NOT BE}}` treated as force majeure, subject to applicable law
and the specific facts.

### Field guide

Define what qualifies, notice requirements, mitigation, business
continuity, payment obligations and the long-stop termination right. A
supplier problem should not automatically excuse the Provider if
supplier management is part of its contractual responsibility.

## Section 23. Notices

Formal notices shall be in writing and delivered by
`{{PERMITTED_METHODS}}` to:

**If to Customer** - Legal name: `{{CUSTOMER_LEGAL_NAME}}` - Address:
`{{NOTICE_ADDRESS}}` - Attention: `{{ROLE_OR_PERSON}}` - Email (if
permitted): `{{NOTICE_EMAIL}}`

**If to Provider** - Legal name: `{{PROVIDER_LEGAL_NAME}}` - Address:
`{{NOTICE_ADDRESS}}` - Attention: `{{ROLE_OR_PERSON}}` - Email (if
permitted): `{{NOTICE_EMAIL}}`

A notice is effective when `{{RECEIPT_RULE}}`.

### Field guide

Operational contacts and legal notice contacts are different. Keep
formal notice details current and specify when email is legally
effective. Do not rely on an account manager's email as a formal notice
route unless the contract says so.

## Section 24. General provisions

### 24.1 Entire agreement

This Agreement and its Schedules and SOWs constitute the entire
agreement on the subject matter and supersede prior agreements and
understandings, subject to `{{EXPRESS_SURVIVING_DOCUMENTS}}`.

### 24.2 Amendments

Any amendment must be in writing and signed by authorised
representatives of both Parties.

### 24.3 Waiver

A failure or delay in exercising a right is not a waiver of that right.
A waiver must be in writing and applies only to the specific matter
stated.

### 24.4 Assignment and change of control

Neither Party may assign or transfer this Agreement without
`{{CONSENT_RULE}}`, except for
`{{PERMITTED_AFFILIATE_OR_REORGANISATION_EXCEPTIONS}}`. Any
change-of-control notification or termination rights shall be
`{{DETAILS}}`.

### 24.5 Independent contractors

The Parties are independent contractors. Nothing creates a partnership,
joint venture, agency, employment or fiduciary relationship, except for
any agency expressly and narrowly created in writing for a specified
purpose.

### 24.6 Severability

If a provision is invalid or unenforceable, it shall be modified to the
minimum extent necessary or severed, and the remaining provisions shall
continue in effect.

### 24.7 Counterparts and electronic signatures

This Agreement may be executed in counterparts and by electronic
signature to the extent permitted by applicable law.

### 24.8 Third-party rights

`{{SPECIFY WHETHER THIRD_PARTIES_HAVE_ENFORCEMENT_RIGHTS}}`.

### 24.9 Survival

Provisions which by their nature should survive shall survive
termination, including accrued payment obligations, confidentiality,
data return, liability, indemnities, dispute resolution and transition
obligations.

### 24.10 Order of precedence

If documents conflict, the following order shall apply, unless expressly
stated otherwise in the relevant signed document: 1. amendments signed
after the relevant document; 2. this MSA; 3. the applicable SOW; 4. the
Schedules; 5. purchase orders or operational forms, which shall not
amend this MSA unless expressly signed as an amendment.

`{{CUSTOMISE_ORDER_OF_PRECEDENCE}}`

### Field guide

Boilerplate clauses can determine whether an operational form, purchase
order, supplier term or later SOW silently changes the deal. The
order-of-precedence clause is especially important where vehicle lease
documents sit alongside the MSA. State which document governs each
subject rather than relying on a generic hierarchy if different
documents cover different legal relationships.

## Section 25. Governing law and dispute resolution

This Agreement and any non-contractual obligations arising from it shall
be governed by the laws of `{{GOVERNING_LAW}}`, without regard to
conflict-of-law rules, subject to mandatory law.

The Parties shall first attempt to resolve disputes through: 1.
operational representatives within `{{DAYS}}`; 2. senior business
representatives within a further `{{DAYS}}`; and 3. executive escalation
/ mediation / court or arbitration as specified below.

Forum: `{{COURTS_OR_ARBITRATION}}`\
Seat and rules (if arbitration): `{{SEAT_AND_RULES}}`\
Language: `{{LANGUAGE}}`

### Field guide

Choose governing law and forum deliberately. Consider where the
contracting entities, vehicles, Drivers, suppliers, data and assets are
located. Mandatory local law may apply regardless of the chosen
governing law. Obtain counsel's advice on enforceability and dispute
strategy.

------------------------------------------------------------------------

# 4. Signature blocks

IN WITNESS WHEREOF, the Parties have caused this Agreement to be
executed by their duly authorised representatives.

**CUSTOMER: `{{CUSTOMER_LEGAL_NAME}}`**

By: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\
Name: `{{SIGNATORY_NAME}}`\
Title: `{{SIGNATORY_TITLE}}`\
Date: `{{SIGNATURE_DATE}}`

**PROVIDER: `{{PROVIDER_LEGAL_NAME}}`**

By: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\
Name: `{{SIGNATORY_NAME}}`\
Title: `{{SIGNATORY_TITLE}}`\
Date: `{{SIGNATURE_DATE}}`

**Why needed:** The signature block identifies the legal entities and
the individuals signing for them. Confirm authority, correct entity
names, execution formalities, counterpart requirements and
electronic-signature validity.

------------------------------------------------------------------------

# 5. Recommended schedules

Schedules hold the detailed operational and commercial information that
changes more often than the legal framework. They should be expressly
incorporated into the MSA.

## Schedule 1 --- Services, scope and exclusions

  -----------------------------------------------------------------------
  Field                   What to record          Why it matters
  ----------------------- ----------------------- -----------------------
  Service name            `{{SERVICE_NAME}}`      Identifies the
                                                  purchased service

  Description             `{{DETAILED_SCOPE}}`    Makes the promise
                                                  measurable

  Included activities     `{{INCLUSIONS}}`        Prevents scope
                                                  ambiguity

  Excluded activities     `{{EXCLUSIONS}}`        Prevents accidental
                                                  obligations

  Service locations       `{{LOCATIONS}}`         Defines geographic
                                                  coverage

  Operating hours         `{{HOURS}}`             Sets availability
                                                  expectations

  Volumes / assumptions   `{{VOLUMES}}`           Supports capacity and
                                                  pricing

  Dependencies            `{{DEPENDENCIES}}`      Identifies what
                                                  Customer or third
                                                  parties must provide

  Deliverables            `{{DELIVERABLES}}`      Defines completion and
                                                  acceptance

  Service owner           `{{OWNER}}`             Assigns accountability
  -----------------------------------------------------------------------

## Schedule 2 --- Fleet and vehicle population

Include vehicle identifier (where available), make/model, class, model
year, registration/VIN, operating location, assigned business unit,
lease/funding entity, lease start/end, mileage allowance, permitted use,
insurance status and service package. Restrict access to personal data
and sensitive vehicle data.

**Why needed:** Defines which vehicles are covered and enables accurate
billing, service eligibility, risk allocation and fleet reporting.

## Schedule 3 --- Vehicle ordering, delivery and acceptance

Document ordering authority, order channels, approval workflow, approved
vehicle catalogue, configuration, delivery lead times, substitutions,
cancellation charges, delivery evidence, inspection, acceptance and
escalation.

**Why needed:** Prevents unauthorised orders and disputes about
delivery, specification, delays and cancellation costs.

## Schedule 4 --- Maintenance, repair, tyres, fuel, charging and roadside services

Document covered work, excluded work, approved networks, rate cards,
authorisation limits, emergency exceptions, warranties, service hours,
geographic coverage, fuel/charging controls, transaction data and
roadside response.

**Why needed:** These are high-frequency operational services with
significant pass-through spend and potential downtime impact.

## Schedule 5 --- Pricing, fees and financial mechanics

Include: - base management fee and charging unit; - lease/funding
rentals, if applicable; - vehicle acquisition or delivery charges; -
maintenance, repair and tyre rates; - fuel/charging and network
charges; - administrative fees and mark-ups; - pass-through costs and
evidence; - taxes and currency; - indexation and rate review; - invoice
frequency and supporting data; - credits, rebates and discounts; - early
termination, excess mileage and end-of-term charges; - remarketing fees,
proceeds and residual-value adjustments.

**Why needed:** Makes the total cost of the fleet arrangement visible
and auditable. A price schedule should show calculation examples for
material or complicated charges.

## Schedule 6 --- Service levels and service credits

For every metric record:

  Field                  Required detail
  ---------------------- ------------------------
  Metric                 `{{NAME}}`
  Definition / formula   `{{FORMULA}}`
  Data source            `{{SYSTEM_OR_REPORT}}`
  Measurement period     `{{PERIOD}}`
  Target                 `{{TARGET}}`
  Exclusions             `{{EXCLUSIONS}}`
  Reporting date         `{{DEADLINE}}`
  Escalation threshold   `{{THRESHOLD}}`
  Remedy / credit        `{{REMEDY}}`
  Credit cap             `{{CAP}}`

Potential metrics include order cycle time, delivery on-time rate,
repair authorisation time, vehicle downtime, roadside response, driver
support response, invoice accuracy, claim update timeliness and
data/report availability.

**Why needed:** Converts general service promises into measurable
obligations and provides a consistent way to identify and remedy
underperformance.

## Schedule 7 --- Accident, claims, incident and escalation procedures

Include emergency contacts, incident severity, reporting timelines,
required information, insurer notification, towing/repair process,
claims authority, escalation contacts, communications cadence and
root-cause analysis.

**Why needed:** Ensures incidents are handled quickly and makes clear
who can make decisions, communicate with insurers and commit funds.

## Schedule 8 --- Vehicle condition, return and remarketing standards

Include normal wear-and-tear guide, inspection method, evidence
standards, appeal window, excess mileage formula, damage rates, missing
equipment charges, return location, sale process, title transfer and
proceeds allocation.

**Why needed:** Reduces disputes at lease end and clarifies
residual-value and vehicle-condition exposure.

## Schedule 9 --- Data protection, telematics and cybersecurity

Include data inventory, purpose, Party roles, lawful basis, notices,
access controls, encryption, logging, incident response, subprocessors,
cross-border transfer, retention, deletion, audit, data return and
permitted analytics.

**Why needed:** Fleet and telematics data may contain personal, location
and behavioural information. The schedule makes use and protection of
that data explicit.

## Schedule 10 --- Responsibility matrix (RACI)

Use R = Responsible, A = Accountable, C = Consulted, I = Informed.

  ---------------------------------------------------------------------------------
  Activity         Customer     Provider     Lessor /     Supplier     Driver
                                             funder                    
  ---------------- ------------ ------------ ------------ ------------ ------------
  Vehicle policy   `{{RACI}}`   `{{RACI}}`   `{{RACI}}`   `{{RACI}}`   `{{RACI}}`

  Vehicle                                                              
  selection                                                            

  Order approval                                                       

  Registration                                                         

  Maintenance                                                          
  approval                                                             

  Repair                                                               
  performance                                                          

  Fuel / charging                                                      
  control                                                              

  Accident                                                             
  reporting                                                            

  Insurance claim                                                      

  Fine / toll                                                          
  handling                                                             

  Vehicle return                                                       

  Remarketing /                                                        
  sale                                                                 

  Invoice                                                              
  reconciliation                                                       

  Data privacy                                                         
  notices                                                              
  ---------------------------------------------------------------------------------

**Why needed:** Exposes responsibility gaps and prevents multiple
parties from assuming another party owns a task.

## Schedule 11 --- Implementation, transition and exit plan

Include implementation milestones, data migration, system integrations,
fleet onboarding, communications, training, acceptance criteria,
parallel run, cutover, exit support, data return and supplier handover.

**Why needed:** The MSA may be signed before the service is operational.
This schedule turns the intended operating model into a deliverable
plan.

------------------------------------------------------------------------

# 6. Commercial and legal review checklist

Use this checklist before approving or signing an MSA.

## A. Contracting structure

-   [ ] Correct legal entity for Customer and Provider verified.
-   [ ] Any Wheels affiliate, lessor, finance provider or servicing
    entity identified correctly.
-   [ ] Contract signatories have authority.
-   [ ] Customer affiliates and participating entities are covered
    appropriately.
-   [ ] MSA, SOW, vehicle lease and supplier documents have a clear
    hierarchy.

## B. Scope and operations

-   [ ] Services, vehicles, Drivers, territories and business units are
    precisely defined.
-   [ ] Exclusions are explicit.
-   [ ] Vehicle ordering and approval authority is documented.
-   [ ] Maintenance, fuel, charging, claims and roadside roles are
    allocated.
-   [ ] Supplier responsibilities and subcontracting are addressed.
-   [ ] Customer dependencies and Provider dependencies are documented.
-   [ ] Service levels are measurable and supported by available data.

## C. Economics

-   [ ] Total cost of ownership has been reviewed, not just the
    management fee.
-   [ ] Lease rentals, funding costs and residual-value exposure are
    clear.
-   [ ] Pass-through charges and mark-ups are transparent.
-   [ ] Taxes, currency, invoice frequency and payment terms are clear.
-   [ ] Invoice evidence and dispute deadlines are workable.
-   [ ] Early termination and end-of-lease charges have been modelled.
-   [ ] Remarketing proceeds, shortfalls and surpluses are allocated.

## D. Asset, insurance and liability

-   [ ] Vehicle title, registration, lessee and risk of loss are clear.
-   [ ] Insurance responsibility and policy limits align with the
    contract.
-   [ ] Deductibles and uninsured losses are allocated.
-   [ ] Liability caps have been assessed against plausible exposure.
-   [ ] Indemnities identify covered claims and defence procedures.
-   [ ] Vehicle damage, Driver conduct, repair defects and third-party
    claims are addressed.

## E. Data, compliance and resilience

-   [ ] Fleet, Driver and telematics data are identified and classified.
-   [ ] Data use, access, retention and deletion are defined.
-   [ ] Cybersecurity and incident notification obligations are agreed.
-   [ ] Applicable vehicle, road safety, tax, privacy and other laws are
    identified.
-   [ ] Business continuity and recovery commitments are realistic.
-   [ ] Audit and regulatory access rights are sufficient.

## F. Termination and exit

-   [ ] MSA termination and individual vehicle lease termination are
    distinguished.
-   [ ] Early termination costs are understood.
-   [ ] Open orders, repairs, claims and invoices have an exit process.
-   [ ] Vehicle return and title transfer are covered.
-   [ ] Data migration and transition assistance are defined.
-   [ ] Critical services can continue during transition.

------------------------------------------------------------------------

# 7. How to analyse an actual Wheels-related agreement

When reviewing a real agreement, prepare the analysis in this order:

1.  **Identify the parties and legal structure.** Who is the customer,
    who is the contracting provider, who owns the vehicles, who funds
    them, who leases them and who actually performs each service?
2.  **Map the business model.** Is the arrangement fleet administration
    only, full-service leasing, vehicle funding, maintenance management,
    fuel/charging, accident management, remarketing or a combination?
3.  **Map the money.** Identify every revenue and cost stream: fixed
    fees, per-vehicle fees, rentals, pass-through costs, mark-ups,
    rebates, credits, taxes, early termination and residual-value
    adjustments.
4.  **Map operational control.** Who approves vehicle orders, repairs,
    replacement vehicles, claims settlements, Driver changes and
    disposal?
5.  **Map assets and risk.** Who has title, possession, custody,
    insurance, risk of loss and residual-value exposure?
6.  **Map third parties.** Identify manufacturers, dealers, repair
    networks, fuel/charging providers, insurers, auction houses,
    technology vendors and subcontractors.
7.  **Test performance obligations.** Determine whether service levels
    are measurable, how failures are evidenced, what cure rights apply
    and whether credits are meaningful.
8.  **Test legal exposure.** Review indemnities, liability caps,
    exclusions, insurance, confidentiality, privacy, cybersecurity and
    compliance.
9.  **Test exit.** Determine what happens to vehicles, data, open
    claims, suppliers, payments and customer operations if the agreement
    ends.
10. **Record gaps and negotiation points.** Separate material risks from
    drafting clean-up and identify the business owner for each decision.

## 7.1 Recommended output for each contract review

  -----------------------------------------------------------------------
  Review item                         What the reviewer should record
  ----------------------------------- -----------------------------------
  Clause / page                       Exact location in the agreement

  Contract wording                    Relevant text or concise quotation

  Plain-English meaning               What it requires or permits

  Business impact                     Effect on fleet operations,
                                      customer or provider

  Financial impact                    Revenue, cost, cash flow or
                                      exposure

  Risk owner                          Customer, Provider, lessor,
                                      supplier, Driver or shared

  Risk level                          Critical / High / Medium / Low,
                                      with rationale

  Ambiguity / gap                     What is missing or unclear

  Recommended action                  Accept, clarify, amend, escalate or
                                      obtain evidence

  Owner                               Legal, commercial, finance,
                                      operations, risk, IT/security
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 8. Drafting discipline and important cautions

-   Never assume that a public description of a company's business
    proves that a particular service, product, entity or contractual
    practice applies to the transaction being reviewed.
-   Never infer that a parent company guarantees an affiliate's
    obligations unless an express guarantee or other enforceable
    commitment exists.
-   Never infer that a fleet manager owns or leases vehicles. Verify
    title, lease and funding documents.
-   Never assume a service provider is the insurer or bears every risk
    associated with a vehicle.
-   Never assume that a supplier's failure is automatically excused;
    examine the Provider's obligations to select, oversee and manage
    suppliers.
-   Never accept a service credit as the sole remedy without
    understanding its cap and interaction with other remedies.
-   Never accept a liability cap without comparing it with vehicle
    value, third-party claims, personal injury, data exposure and
    realistic loss scenarios.
-   Never treat an operational policy or portal term as contractually
    binding unless properly incorporated.
-   Keep the source agreement's actual wording and commercial intent
    distinct from proposed improvements.
-   Where the source document is silent, record **"not addressed in the
    document"** rather than filling the gap with an assumption.

------------------------------------------------------------------------

# 9. Source-document map

The uploaded 14-page *Logistics Services Agreement* provides the
following reference structure:

  -----------------------------------------------------------------------
  Source pages            Main subject            How this template uses
                                                  it
  ----------------------- ----------------------- -----------------------
  1--2                    Parties, recitals,      Parties, recitals,
                          services, products,     scope, fleet
                          distribution centre,    population, locations
                          rates and payment       and pricing

  3                       Invoice disputes and    Invoice dispute
                          service standards       mechanics and service
                                                  quality

  4--6                    Ownership, reporting,   Vehicle/data ownership
                          review meetings,        prompts, governance,
                          operational policies,   incident and operating
                          special materials and   schedules, compliance
                          legal compliance        

  7--8                    Insurance, liability    Insurance, liability,
                          limitations,            indemnities,
                          indemnification,        confidentiality and
                          subrogation and         risk allocation
                          confidentiality         

  9--11                   Term, termination,      Termination,
                          existing services,      transition, notices and
                          miscellaneous           general provisions
                          provisions and notices  

  12--14                  Governing law,          Governing law,
                          amendment,              boilerplate, order of
                          counterparts,           precedence and
                          assignment,             signature blocks
                          interpretation and      
                          signatures              
  -----------------------------------------------------------------------

**Source limitation:** The source is a logistics services agreement, not
a fleet-management MSA. It does not establish Wheels-specific positions
or the detailed fleet modules added in this guide. The fleet modules are
prompts for transaction-specific drafting and verification.
