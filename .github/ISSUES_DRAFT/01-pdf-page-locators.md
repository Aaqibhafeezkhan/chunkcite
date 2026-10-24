Title: [good first issue] Carry PDF page numbers into chunk locators
Body: chunk_file() sets page for PDF chunks, but the JSON output should
also surface page in the audit report. Add a test with a synthetic PDF.
