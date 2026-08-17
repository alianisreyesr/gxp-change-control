# Glossary — Change Control and Data Integrity

These definitions describe how terms are used in this educational repository. They are not substitutes for an organization's approved procedures, regulatory interpretation, or legal advice.

## Activity record

An application-generated entry describing a workflow event, actor, detail, and server timestamp. In this prototype, records are append-oriented through the supported API. They are not an independently secured or validated audit trail.

## Approval

A recorded decision by an attributable actor acting in a stated role. The prototype supports approval, rejection, and request for more information. It does not implement electronic signatures, re-authentication, delegated authority, or multi-approver policy.

## Attributable

The data-integrity expectation that an action can be associated with the individual who performed it. The prototype rejects generic actor names such as `admin` and records a supplied individual-style identifier. It does not authenticate that identity.

## Change control

A governed process for proposing, assessing, approving, implementing, verifying, and closing a change while preserving traceability and managing risk.

## Change request

The initial record describing what is proposed, why it is needed, which system is affected, its priority, the requester, and an optional target implementation date.

## Controlled transition

A permitted movement from one workflow status to another. The API enforces defined transitions and rejects unsupported movements rather than silently changing state.

## Data integrity

The degree to which data remains complete, consistent, accurate, attributable, legible, contemporaneous, original, and available throughout its lifecycle. The repository models selected technical concepts but does not provide a complete data-integrity control framework.

## Electronic signature

An electronic representation of a person's intent to sign a record. This prototype does not implement electronic signatures, signature meaning, identity verification, or signature-to-record linking.

## GxP

A collective term for regulated good-practice requirements such as good manufacturing, laboratory, clinical, distribution, and pharmacovigilance practices. The repository uses GxP vocabulary for learning and portfolio demonstration.

## Impact assessment

A structured evaluation of what a proposed change could affect. This prototype records potential effects on validated state, Part 11 controls, data integrity, training, and SOPs, plus residual risk and rationale.

## Implementation

The stage in which approved work is carried out. The v1.0.0 prototype records the status transition but does not yet model individual implementation tasks, evidence, owners, or due dates.

## Like-for-like change

A change intended to replace or update an item without altering its approved function, configuration intent, or risk profile. Whether a change is truly like-for-like requires documented assessment; the label alone does not remove the need for change control.

## Part 11 controls

Technical and procedural controls associated with electronic records and electronic signatures under 21 CFR Part 11. The impact flag in this repository is an educational prompt, not evidence that Part 11 applies or that the system complies.

## Residual risk

The risk remaining after planned controls or mitigations are considered. The prototype records low, medium, or high residual risk and applies consistency rules to the supporting rationale.

## Request for information

A decision returning a pending approval to impact assessment so that the requester or assessor can add or revise evidence before another decision.

## Segregation of duties

The separation of responsibilities so that incompatible activities are not controlled by one person without appropriate oversight. The prototype records roles but does not enforce role assignments or separation.

## SOP

A standard operating procedure: an approved instruction describing how an activity must be performed and controlled. SOP impact is represented as an assessment flag only.

## Synthetic data

Fictional information created solely for demonstration or testing and not derived from identifiable people, companies, products, batches, incidents, investigations, or regulated records.

## Validated state

The condition in which a system continues to operate according to approved requirements and its validated or assured baseline. A change may affect that state and trigger additional assessment or testing. This portfolio application is itself not validated.

## Verification

Confirmation that implementation produced the intended result and did not introduce unacceptable effects. The prototype includes a verification status but does not yet capture protocol steps, expected results, actual results, attachments, or independent sign-off.
