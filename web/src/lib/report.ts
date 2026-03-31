import { jsPDF } from "jspdf";

import { AppResult, issueDisplayMessage, issueNextStepCopy } from "@/lib/ach";

export function buildReportPdf(result: AppResult): Uint8Array {
  const doc = new jsPDF({
    unit: "pt",
    format: "letter",
  });

  let y = 56;
  const lineHeight = 18;
  const left = 48;
  const pageWidth = doc.internal.pageSize.getWidth() - 96;

  const writeBlock = (text: string, size = 11, bold = false) => {
    doc.setFont("helvetica", bold ? "bold" : "normal");
    doc.setFontSize(size);
    const lines = doc.splitTextToSize(text, pageWidth);
    doc.text(lines, left, y);
    y += lines.length * lineHeight;
  };

  writeBlock("ACHLint Validation Report", 20, true);
  writeBlock(`Status: ${result.status.replaceAll("_", " ").toUpperCase()}`, 12, true);
  y += 8;
  writeBlock(`Generated: ${new Date(result.summary.generatedAt).toLocaleString()}`);
  writeBlock(`Entries: ${result.summary.entries}`);
  writeBlock(`Total credit: $${(result.summary.totalCreditCents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}`);
  writeBlock(`Blocking issues: ${result.summary.errors}`);
  writeBlock(`Warnings: ${result.summary.warnings}`);
  y += 14;
  writeBlock("Issue details", 14, true);

  if (!result.issues.length) {
    writeBlock("No issues were found in this run.");
  } else {
    result.issues.forEach((issue, index) => {
      if (y > 700) {
        doc.addPage();
        y = 56;
      }
      writeBlock(`${index + 1}. ${issue.severity.toUpperCase()} • ${issue.code}`, 12, true);
      writeBlock(issueDisplayMessage(issue));
      writeBlock(`Next step: ${issueNextStepCopy(issue)}`);
      if (issue.rowNumber) {
        writeBlock(`Row: ${issue.rowNumber}`);
      }
      if (issue.lineNumber) {
        writeBlock(`Line: ${issue.lineNumber}`);
      }
      y += 10;
    });
  }

  return new Uint8Array(doc.output("arraybuffer"));
}
