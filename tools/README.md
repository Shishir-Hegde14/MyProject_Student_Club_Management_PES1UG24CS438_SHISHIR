# Document and diagram sources

Shishir Hegde | PES1UG24CS438 | Section 5H

`build_documents.py` contains the editable text and tables used to build the seven new Word documents. It needs `python-docx` and reads the recorded performance JSON for the test report. It does not alter the original Lab 1 files.

`build_diagrams.py` produces the two black-and-white diagram PDFs and PNGs using `reportlab` and `pypdfium2`. These are diagrams, not application screenshots.

PDF document copies were exported from Word files through LibreOffice and checked as rendered pages. Screenshots were captured separately from the running browser. The document-building packages are not application runtime dependencies.
