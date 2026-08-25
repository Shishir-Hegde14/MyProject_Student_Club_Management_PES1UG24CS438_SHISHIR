# Software Engineering Lab 1
## Requirements Engineering & UML Use-Case Modelling

**Name:** Shishir Hegde  
**SRN:** PES1UG24CS438  

**Problem Statement #10:** Student Club Event Ticketing & Budget Portal  
**Domain:** Campus & Academic Operations  

---

## 1. Problem Overview

Student clubs require an integrated portal to submit event proposals, request university budget allocations through a multi-stage approval process, and generate secure QR-code tickets for attendees.

The system should simplify event planning, budget approval, and attendee ticket validation while ensuring that university approval procedures are followed correctly.

---

## 2. Requirements Table

| Req ID | Type | Description | Priority | Acceptance Criteria | Rationale | Comments |
|---|---|---|---|---|---|---|
| FR-001 | Functional | The system shall route event budget proposals sequentially through the Faculty Coordinator, Finance Office, and Dean for approval. | High | **Pass:** The proposal reaches each approval stage only after the previous stage has digitally approved it. **Fail:** The proposal reaches a later stage without approval from the previous stage. | Ensures that university budget requests follow the required approval hierarchy. | |
| FR-002 | Functional | The system shall allow a Club Lead to submit an event proposal containing event details and the requested budget. | High | **Pass:** A proposal containing all mandatory information is successfully submitted and assigned a unique proposal ID. **Fail:** A proposal with missing mandatory information is accepted by the system. | Enables student clubs to formally initiate the event approval process. | |
| FR-003 | Functional | The system shall allow authorized approvers to approve or reject an event proposal and record their decision. | High | **Pass:** An authorized approver can approve or reject a proposal, and the decision is stored with the updated status. **Fail:** The proposal status remains unchanged after a valid approval or rejection action. | Provides a clear and traceable mechanism for processing event and budget requests. | |
| FR-004 | Functional | The system shall generate a unique QR-code ticket for each registered attendee of an approved event. | High | **Pass:** Each registered attendee receives a QR-code ticket with a unique ticket identifier. **Fail:** Two attendees are issued tickets with the same ticket identifier. | Provides secure and convenient digital tickets for event attendees. | |
| FR-005 | Functional | The system shall validate an attendee's QR-code ticket at the event check-in point and determine whether the ticket is authentic. | High | **Pass:** A valid QR-code ticket is accepted and an invalid ticket is rejected. **Fail:** An invalid or unrecognized QR-code ticket is accepted as valid. | Prevents unauthorized entry and supports efficient attendee verification. | |
| NFR-001 | Non-Functional – Performance & Security | The QR-code ticket scanner API shall validate entry authenticity in under 100 milliseconds at venue check-in points. | High | **Pass:** Performance testing under simulated peak load shows that QR-code authentication completes in less than 100 ms. **Fail:** Validation takes 100 ms or more under the defined test conditions. | Ensures fast and secure attendee check-in, especially during periods of high traffic. | |
| NFR-002 | Non-Functional – Security | The system shall restrict event proposal, budget approval, and ticket-management operations according to authorized user roles. | High | **Pass:** Users can access only the operations permitted for their assigned role during authorization testing. **Fail:** A user can perform an operation that is not permitted for their assigned role. | Protects sensitive event and financial operations from unauthorized access. | |

---

## 3. Requirement Summary

The proposed system has five primary functional requirements:

1. Multi-stage budget approval workflow.
2. Event proposal submission.
3. Approval or rejection of proposals.
4. QR-code ticket generation.
5. QR-code ticket validation.

The two major non-functional requirements focus on:

1. QR-code validation performance and security.
2. Role-based access security.

---

## 4. Peer Review Comments

The Comments column is intentionally left blank and can be completed during the peer-review stage of the lab.

Each requirement should be reviewed for:

- Clarity
- Testability
- Relevance to the problem statement
- Unambiguous wording
- Measurable acceptance criteria
