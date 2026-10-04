# Lab 3 Architecture

Shishir Hegde | PES1UG24CS438 | Section 5H

The selected design is a **layered monolith**. Browsers communicate with one application server, so its deployment is also client-server. The comparison explains why microservices are not needed for this prototype.

- [Component diagram PNG](component-diagram.png) / [PDF](component-diagram.pdf)
- [One-page justification PDF](architecture-justification.pdf) / [Word](architecture-justification.docx)
- [Architecture analysis and interfaces PDF](architecture-analysis.pdf) / [Word](architecture-analysis.docx)

The diagram has seven components: Web UI, Authentication, Event and Budget, Ticket Service, Check-in Service, Dashboard Service and SQLite Repository. It shows five named UI-to-service interfaces and the shared data interface. Circles and semicircles identify provided and required interfaces; small squares identify ports.

These are logical components in one program. The analysis maps each component to its actual code location. The diagram is generated from the editable source in [build_diagrams.py](../tools/build_diagrams.py).

The coffee kiosk in the handout is an example. All submitted architecture files here concern the student club portal.
