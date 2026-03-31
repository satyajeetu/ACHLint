import Papa from "papaparse";

export type Severity = "error" | "warning" | "info";
export type ActivePage = "landing" | "generate" | "validate" | "results" | "help";

export type ValidationIssue = {
  code: string;
  message: string;
  severity: Severity;
  field?: string;
  rowNumber?: number;
  lineNumber?: number;
  originalValue?: string;
  suggestedFix?: string;
};

export type PaymentRowInput = {
  rowNumber: number;
  name: string;
  routingNumber: string;
  accountNumber: string;
  accountType: "checking" | "savings" | string;
  amount: number;
  idNumber: string;
  discretionaryData: string;
  effectiveDate?: string;
};

export type OriginatorConfig = {
  companyName: string;
  companyIdentification: string;
  immediateDestinationRouting: string;
  immediateDestinationName: string;
  immediateOriginRouting: string;
  immediateOriginName: string;
  companyEntryDescription: string;
  effectiveEntryDate: string;
  originatingDfiIdentification: string;
  fileIdModifier: string;
  companyDiscretionaryData: string;
  companyDescriptiveDate: string;
  referenceCode: string;
  traceNumberStart: number;
};

export type BuildSummary = {
  entries: number;
  totalCreditCents: number;
  totalDebitCents: number;
  warnings: number;
  errors: number;
  batchCount: number;
  blockCount: number;
  effectiveDate?: string;
  serviceClass: string;
  secCode: string;
  originatingDfi: string;
  immediateDestination: string;
  generatedAt: string;
};

export type BuildResult = {
  kind: "build";
  status: "success" | "failed";
  summary: BuildSummary;
  issues: ValidationIssue[];
  achText: string;
  exceptionsCsv: string;
};

export type ValidationResult = {
  kind: "validation";
  status: "pass" | "pass_with_warnings" | "fail";
  summary: BuildSummary;
  issues: ValidationIssue[];
  exceptionsCsv: string;
  achText: string;
};

export type AppResult = BuildResult | ValidationResult;

type ParsedCsvRecord = Record<string, string | undefined>;

export const UI_COPY = {
  landingEyebrow: "ACH file generation without the guesswork",
  landingProblem:
    "When a bank rejects your ACH file, payroll and payout operations stall. The pressure is high, the rules are rigid, and most teams are still working from spreadsheets.",
  landingTitle: "Turn your payment spreadsheet into a bank-accepted ACH file in minutes.",
  landingBody:
    "ACHLint gives operators a focused path from CSV to validated ACH output. Upload your payment file, review blocking issues before upload, and leave with an ACH file, a validation report, and an exceptions CSV.",
  landingProof:
    "Built for spreadsheet-driven payroll and payouts. Focused scope. Validation before ACH download.",
  landingNote:
    "Start with guided setup if you are creating a new file. If you already have an ACH file, use Validate to understand what needs attention.",
  resultsPassTitle: "Your file passed validation.",
  resultsPassBody:
    "Your artifacts are ready. You can move into your bank upload workflow with much more confidence.",
  resultsWarningTitle: "Your file passed core validation, with warnings to review.",
  resultsWarningBody:
    "The file is structurally valid, but you should review the advisory notes before upload.",
  resultsFailTitle: "This run has blocking issues.",
  resultsFailBody:
    "Review the grouped issues below, fix the source data or file structure, and run validation again before uploading anything.",
};

const REQUIRED_HEADERS = [
  "name",
  "routing_number",
  "account_number",
  "account_type",
  "amount",
] as const;

const OPTIONAL_HEADERS = [
  "id_number",
  "discretionary_data",
  "effective_date",
] as const;

const ALLOWED_HEADERS = new Set([...REQUIRED_HEADERS, ...OPTIONAL_HEADERS]);
const ALLOWED_ACCOUNT_TYPES = new Set(["checking", "savings"]);

export const TEMPLATE_CSV = `name,routing_number,account_number,account_type,amount,id_number,discretionary_data,effective_date
Jane Doe,021000021,123456789,checking,1250.00,EMP001,,${nextBusinessDay(todayIso())}
John Smith,011000138,987654321,savings,980.55,EMP002,,
`;

export const DEFAULT_CONFIG: OriginatorConfig = {
  companyName: "ACME PAYROLL",
  companyIdentification: "1234567890",
  immediateDestinationRouting: "021000021",
  immediateDestinationName: "JPMORGAN CHASE",
  immediateOriginRouting: "011000015",
  immediateOriginName: "BANK OF AMERICA",
  companyEntryDescription: "PAYROLL",
  effectiveEntryDate: nextBusinessDay(todayIso()),
  originatingDfiIdentification: "01100001",
  fileIdModifier: "A",
  companyDiscretionaryData: "",
  companyDescriptiveDate: "",
  referenceCode: "",
  traceNumberStart: 1,
};

export function parsePaymentCsv(content: string): {
  rows: PaymentRowInput[];
  issues: ValidationIssue[];
} {
  const result = Papa.parse<ParsedCsvRecord>(content, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (header) => header.trim(),
  });

  const issues: ValidationIssue[] = [];
  const headers = result.meta.fields ?? [];
  const missing = REQUIRED_HEADERS.filter((header) => !headers.includes(header));
  const extra = headers.filter((header) => !ALLOWED_HEADERS.has(header as (typeof REQUIRED_HEADERS)[number]));

  if (missing.length) {
    issues.push({
      code: "csv_missing_columns",
      message: `Missing required columns: ${missing.sort().join(", ")}.`,
      severity: "error",
      field: "headers",
    });
  }
  if (extra.length) {
    issues.push({
      code: "csv_unknown_columns",
      message: `Unknown columns in strict mode: ${extra.sort().join(", ")}.`,
      severity: "error",
      field: "headers",
    });
  }
  if (issues.length) {
    return { rows: [], issues };
  }

  const rows: PaymentRowInput[] = [];
  const seen = new Set<string>();

  result.data.forEach((record, index) => {
    const rowNumber = index + 2;
    const name = (record.name ?? "").trim();
    const routingNumber = (record.routing_number ?? "").trim();
    const accountNumber = (record.account_number ?? "").trim();
    const accountType = (record.account_type ?? "").trim().toLowerCase();
    const amountText = (record.amount ?? "").trim();
    const idNumber = (record.id_number ?? "").trim();
    const discretionaryData = (record.discretionary_data ?? "").trim();
    const effectiveDateText = (record.effective_date ?? "").trim();

    if (!name) {
      issues.push(rowIssue(rowNumber, "name", "name_required", "Name is required.", name));
    }
    if (toUpperAscii(name).length > 22) {
      issues.push(
        rowIssue(
          rowNumber,
          "name",
          "name_too_long",
          "Name exceeds 22 characters after normalization.",
          name,
          "Shorten the recipient name."
        )
      );
    }
    if (!accountNumber) {
      issues.push(
        rowIssue(
          rowNumber,
          "account_number",
          "account_required",
          "Account number is required.",
          accountNumber
        )
      );
    }
    if (accountNumber.length > 17) {
      issues.push(
        rowIssue(
          rowNumber,
          "account_number",
          "account_too_long",
          "Account number must be 17 characters or fewer.",
          accountNumber
        )
      );
    }
    if (!isValidRoutingNumber(routingNumber)) {
      issues.push(
        rowIssue(
          rowNumber,
          "routing_number",
          "routing_invalid",
          "Routing number must be 9 digits and pass the ABA check digit test.",
          routingNumber
        )
      );
    }
    if (!ALLOWED_ACCOUNT_TYPES.has(accountType)) {
      issues.push(
        rowIssue(
          rowNumber,
          "account_type",
          "account_type_invalid",
          "Account type must be checking or savings.",
          accountType
        )
      );
    }

    let amount: number | null = null;
    try {
      amount = parseAmount(amountText);
    } catch (error) {
      issues.push(
        rowIssue(
          rowNumber,
          "amount",
          "amount_invalid",
          error instanceof Error ? error.message : "Amount is invalid.",
          amountText
        )
      );
    }

    let effectiveDate: string | undefined;
    if (effectiveDateText) {
      if (/^\d{4}-\d{2}-\d{2}$/.test(effectiveDateText)) {
        effectiveDate = effectiveDateText;
      } else {
        issues.push(
          rowIssue(
            rowNumber,
            "effective_date",
            "effective_date_invalid",
            "Effective date must use YYYY-MM-DD format.",
            effectiveDateText
          )
        );
      }
    }

    const signature = [routingNumber, accountNumber, amountText, name.toUpperCase()].join("|");
    if (seen.has(signature)) {
      issues.push(
        rowIssue(
          rowNumber,
          "row",
          "duplicate_row",
          "Duplicate payment row detected.",
          signature
        )
      );
    } else {
      seen.add(signature);
    }

    if (amount === null) {
      return;
    }

    rows.push({
      rowNumber,
      name,
      routingNumber,
      accountNumber,
      accountType,
      amount,
      idNumber,
      discretionaryData,
      effectiveDate,
    });
  });

  return { rows, issues };
}

export function buildFile(
  config: OriginatorConfig,
  rows: PaymentRowInput[]
): BuildResult {
  const issues = [
    ...validateOriginatorConfig(config),
    ...validateRows(rows, config),
  ];

  const summary: BuildSummary = {
    entries: rows.length,
    totalCreditCents: rows.reduce((sum, row) => sum + amountToCents(row.amount), 0),
    totalDebitCents: 0,
    warnings: issues.filter((issue) => issue.severity === "warning").length,
    errors: issues.filter((issue) => issue.severity === "error").length,
    batchCount: 1,
    blockCount: 0,
    effectiveDate: config.effectiveEntryDate,
    serviceClass: "220",
    secCode: "PPD",
    originatingDfi: config.originatingDfiIdentification,
    immediateDestination: config.immediateDestinationRouting,
    generatedAt: new Date().toISOString(),
  };

  if (summary.errors) {
    return {
      kind: "build",
      status: "failed",
      summary,
      issues,
      achText: "",
      exceptionsCsv: buildExceptionsCsv(issues),
    };
  }

  const now = new Date();
  const fileHeader = buildFileHeader(config, now);
  const batchHeader = buildBatchHeader(config, 1);
  const entries = rows.map((row, index) =>
    buildEntryDetail(row, config, index + config.traceNumberStart)
  );
  const entryHash = computeEntryHash(rows.map((row) => row.routingNumber));
  const batchControl = buildBatchControl({
    entryCount: rows.length,
    entryHash,
    totalCreditCents: summary.totalCreditCents,
    config,
    batchNumber: 1,
  });

  const currentRecords = [fileHeader, batchHeader, ...entries, batchControl];
  const blockCount = Math.floor((currentRecords.length + 1 + 9) / 10);
  const fileControl = buildFileControl({
    batchCount: 1,
    blockCount,
    entryCount: rows.length,
    entryHash,
    totalCreditCents: summary.totalCreditCents,
  });

  const allRecords = [
    fileHeader,
    batchHeader,
    ...entries,
    batchControl,
    fileControl,
    ...buildPaddingLines(currentRecords.length + 1),
  ];

  const achText = allRecords.join("\n");
  return {
    kind: "build",
    status: "success",
    summary: {
      ...summary,
      blockCount: allRecords.length / 10,
      generatedAt: now.toISOString(),
    },
    issues,
    achText,
    exceptionsCsv: buildExceptionsCsv(issues),
  };
}

export function validateAch(content: string): ValidationResult {
  const rawLines = content.split(/\r?\n/);
  const lines = rawLines.filter((line) => line !== "");
  const issues: ValidationIssue[] = [];

  lines.forEach((line, index) => {
    const lineNumber = index + 1;
    if (line.length !== 94) {
      issues.push({
        code: "line_length_invalid",
        message: "Each ACH record must be exactly 94 characters.",
        severity: "error",
        lineNumber,
        originalValue: String(line.length),
      });
    }
    if (!ensureAscii(line)) {
      issues.push({
        code: "line_non_ascii",
        message: "ACH records must contain ASCII characters only.",
        severity: "error",
        lineNumber,
      });
    }
  });

  if (!lines.length) {
    issues.push({
      code: "file_empty",
      message: "ACH file is empty.",
      severity: "error",
    });
    return {
      kind: "validation",
      status: "fail",
      summary: emptySummary(),
      issues,
      exceptionsCsv: buildExceptionsCsv(issues),
      achText: content,
    };
  }

  const recordTypes = lines.map((line) => line.slice(0, 1));
  if (recordTypes[0] !== "1") {
    issues.push({
      code: "record_order_invalid",
      message: "File must start with record type 1.",
      severity: "error",
      lineNumber: 1,
    });
  }

  const batchHeaderIndex = recordTypes.indexOf("5");
  if (batchHeaderIndex === -1) {
    issues.push({
      code: "batch_header_missing",
      message: "Batch header record type 5 is required.",
      severity: "error",
    });
  }

  const entryLines = lines.filter((line) => line.startsWith("6"));
  const batchControlLines = lines.filter((line) => line.startsWith("8"));
  const fileControlLines = lines.filter(
    (line) => line.startsWith("9") && line !== "9".repeat(94)
  );

  if (batchHeaderIndex !== 1) {
    issues.push({
      code: "record_order_invalid",
      message: "Batch header must appear immediately after the file header.",
      severity: "error",
    });
  }
  if (!entryLines.length) {
    issues.push({
      code: "entries_missing",
      message: "At least one entry detail record is required.",
      severity: "error",
    });
  }
  if (batchControlLines.length !== 1) {
    issues.push({
      code: "batch_control_invalid",
      message: "Exactly one batch control record is required.",
      severity: "error",
    });
  }
  if (fileControlLines.length !== 1) {
    issues.push({
      code: "file_control_invalid",
      message: "Exactly one file control record is required.",
      severity: "error",
    });
  }

  if (batchHeaderIndex > -1) {
    const batchHeader = lines[batchHeaderIndex];
    if (batchHeader.slice(1, 4) !== "220") {
      issues.push({
        code: "service_class_invalid",
        message: "Service class must be 220.",
        severity: "error",
        lineNumber: batchHeaderIndex + 1,
      });
    }
    if (batchHeader.slice(50, 53) !== "PPD") {
      issues.push({
        code: "sec_invalid",
        message: "SEC code must be PPD.",
        severity: "error",
        lineNumber: batchHeaderIndex + 1,
      });
    }
  }

  const computedEntryHash = entryLines.reduce(
    (sum, line) => sum + Number.parseInt(line.slice(3, 11), 10),
    0
  ) % 10 ** 10;
  const totalCredits = entryLines.reduce(
    (sum, line) => sum + Number.parseInt(line.slice(29, 39), 10),
    0
  );
  const totalDebits = 0;

  lines.forEach((line, index) => {
    if (line.startsWith("6") && !["22", "32"].includes(line.slice(1, 3))) {
      issues.push({
        code: "transaction_code_invalid",
        message: "Only credit transaction codes 22 and 32 are supported.",
        severity: "error",
        lineNumber: index + 1,
        originalValue: line.slice(1, 3),
      });
    }
  });

  if (batchControlLines.length) {
    const batchControl = batchControlLines[0];
    if (Number.parseInt(batchControl.slice(4, 10), 10) !== entryLines.length) {
      issues.push({
        code: "entry_count_mismatch",
        message: "Batch control entry count does not match entries.",
        severity: "error",
      });
    }
    if (Number.parseInt(batchControl.slice(10, 20), 10) !== computedEntryHash) {
      issues.push({
        code: "entry_hash_mismatch",
        message: "Batch control entry hash does not match entries.",
        severity: "error",
      });
    }
    if (Number.parseInt(batchControl.slice(20, 32), 10) !== totalDebits) {
      issues.push({
        code: "debit_total_mismatch",
        message: "Batch control debit total must be zero.",
        severity: "error",
      });
    }
    if (Number.parseInt(batchControl.slice(32, 44), 10) !== totalCredits) {
      issues.push({
        code: "credit_total_mismatch",
        message: "Batch control credit total does not match entries.",
        severity: "error",
      });
    }
  }

  if (fileControlLines.length) {
    const fileControl = fileControlLines[0];
    const actualBlocks = lines.length % 10 === 0 ? lines.length / 10 : Math.floor(lines.length / 10) + 1;
    if (Number.parseInt(fileControl.slice(1, 7), 10) !== 1) {
      issues.push({
        code: "batch_count_invalid",
        message: "File control batch count must be 1 for MVP.",
        severity: "error",
      });
    }
    if (Number.parseInt(fileControl.slice(7, 13), 10) !== actualBlocks) {
      issues.push({
        code: "block_count_mismatch",
        message: "File control block count does not match line count.",
        severity: "error",
      });
    }
    if (Number.parseInt(fileControl.slice(13, 21), 10) !== entryLines.length) {
      issues.push({
        code: "file_entry_count_mismatch",
        message: "File control entry count does not match entries.",
        severity: "error",
      });
    }
    if (Number.parseInt(fileControl.slice(21, 31), 10) !== computedEntryHash) {
      issues.push({
        code: "file_entry_hash_mismatch",
        message: "File control entry hash does not match entries.",
        severity: "error",
      });
    }
    if (Number.parseInt(fileControl.slice(31, 43), 10) !== totalDebits) {
      issues.push({
        code: "file_debit_total_mismatch",
        message: "File control debit total must be zero.",
        severity: "error",
      });
    }
    if (Number.parseInt(fileControl.slice(43, 55), 10) !== totalCredits) {
      issues.push({
        code: "file_credit_total_mismatch",
        message: "File control credit total does not match entries.",
        severity: "error",
      });
    }
  }

  if (lines.length % 10 !== 0) {
    issues.push({
      code: "padding_invalid",
      message: "ACH file must be padded to a multiple of 10 lines.",
      severity: "error",
    });
  }

  const traceNumbers = entryLines.map((line) => line.slice(79, 94));
  if (traceNumbers.join("|") !== [...traceNumbers].sort().join("|")) {
    issues.push({
      code: "trace_order_invalid",
      message: "Trace numbers must be ascending within the batch.",
      severity: "error",
    });
  }

  const warnings = issues.filter((issue) => issue.severity === "warning").length;
  const errors = issues.filter((issue) => issue.severity === "error").length;
  const status = errors ? "fail" : warnings ? "pass_with_warnings" : "pass";

  return {
    kind: "validation",
    status,
    summary: {
      entries: entryLines.length,
      totalCreditCents: totalCredits,
      totalDebitCents: totalDebits,
      warnings,
      errors,
      batchCount: 1,
      blockCount: lines.length % 10 === 0 ? lines.length / 10 : 0,
      serviceClass: "220",
      secCode: "PPD",
      generatedAt: new Date().toISOString(),
      effectiveDate: undefined,
      originatingDfi: "",
      immediateDestination: "",
    },
    issues,
    exceptionsCsv: buildExceptionsCsv(issues),
    achText: content,
  };
}

export function finalizeBuildResult(result: BuildResult): BuildResult {
  const issues = [...result.issues];
  if (!result.achText) {
    return {
      ...result,
      exceptionsCsv: buildExceptionsCsv(issues),
    };
  }

  const validation = validateAch(result.achText);
  issues.push(...validation.issues);
  const errors = issues.filter((issue) => issue.severity === "error").length;
  const warnings = issues.filter((issue) => issue.severity === "warning").length;
  return {
    ...result,
    status: errors ? "failed" : "success",
    achText: errors ? "" : result.achText,
    issues,
    summary: {
      ...result.summary,
      errors,
      warnings,
    },
    exceptionsCsv: buildExceptionsCsv(issues),
  };
}

export function buildExceptionsCsv(issues: ValidationIssue[]): string {
  const header = [
    "severity",
    "code",
    "field",
    "row_number",
    "line_number",
    "message",
    "original_value",
    "suggested_fix",
  ];
  const rows = issues.map((issue) =>
    [
      issue.severity,
      issue.code,
      issue.field ?? "",
      issue.rowNumber ?? "",
      issue.lineNumber ?? "",
      issue.message,
      issue.originalValue ?? "",
      issue.suggestedFix ?? "",
    ]
      .map(csvEscape)
      .join(",")
  );
  return [header.join(","), ...rows].join("\n");
}

export function issueSummaryCopy(severity: Severity, count: number): string {
  if (severity === "error") {
    return `We found ${count} ${count === 1 ? "blocking issue" : "blocking issues"}. Review them before this run can pass.`;
  }
  if (severity === "warning") {
    return `We found ${count} ${count === 1 ? "warning" : "warnings"}. The file may still be usable, but these items should be reviewed.`;
  }
  return `We found ${count} informational ${count === 1 ? "note" : "notes"}. These are provided for context.`;
}

export function issueNextStepCopy(issue: ValidationIssue): string {
  if (issue.suggestedFix) {
    return issue.suggestedFix;
  }
  if (issue.field) {
    return `Review the ${issue.field} value and update the source data before running again.`;
  }
  return "Review the source data or file structure, then run ACHLint again.";
}

export function issueDisplayMessage(issue: ValidationIssue): string {
  const impact =
    issue.severity === "error"
      ? "This blocks generation or validation pass status."
      : issue.severity === "warning"
        ? "This does not block the run, but it should be reviewed before upload."
        : "This is informational and does not block the run.";
  return `${issue.message} ${impact}`;
}

export function resultBanner(result: AppResult): {
  tone: "success" | "warning" | "fail";
  title: string;
  body: string;
} {
  if (result.status === "success" || result.status === "pass") {
    return {
      tone: "success",
      title: UI_COPY.resultsPassTitle,
      body: UI_COPY.resultsPassBody,
    };
  }
  if (result.status === "pass_with_warnings") {
    return {
      tone: "warning",
      title: UI_COPY.resultsWarningTitle,
      body: UI_COPY.resultsWarningBody,
    };
  }
  return {
    tone: "fail",
    title: UI_COPY.resultsFailTitle,
    body: UI_COPY.resultsFailBody,
  };
}

export function groupedIssues(issues: ValidationIssue[]): Record<Severity, ValidationIssue[]> {
  return {
    error: issues.filter((issue) => issue.severity === "error"),
    warning: issues.filter((issue) => issue.severity === "warning"),
    info: issues.filter((issue) => issue.severity === "info"),
  };
}

export function maskAccountNumber(value: string): string {
  const trimmed = value.trim();
  if (trimmed.length <= 4) {
    return "*".repeat(trimmed.length);
  }
  return `${"*".repeat(trimmed.length - 4)}${trimmed.slice(-4)}`;
}

function validateOriginatorConfig(config: OriginatorConfig): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const requiredFields: [keyof OriginatorConfig, string | number][] = [
    ["companyName", config.companyName],
    ["companyIdentification", config.companyIdentification],
    ["immediateDestinationRouting", config.immediateDestinationRouting],
    ["immediateDestinationName", config.immediateDestinationName],
    ["immediateOriginRouting", config.immediateOriginRouting],
    ["immediateOriginName", config.immediateOriginName],
    ["companyEntryDescription", config.companyEntryDescription],
    ["originatingDfiIdentification", config.originatingDfiIdentification],
    ["fileIdModifier", config.fileIdModifier],
  ];

  requiredFields.forEach(([field, value]) => {
    if (!String(value).trim()) {
      issues.push({
        code: "config_required",
        message: `${field} is required.`,
        severity: "error",
        field,
      });
    }
  });

  if (isWeekend(config.effectiveEntryDate) || isUsFederalHoliday(config.effectiveEntryDate)) {
    issues.push({
      code: "effective_date_invalid",
      message: "Effective entry date must be a U.S. business day and not a federal holiday.",
      severity: "error",
      field: "effectiveEntryDate",
    });
  }

  if (!isValidRoutingNumber(config.immediateDestinationRouting)) {
    issues.push({
      code: "destination_routing_invalid",
      message: "Immediate destination routing must be a valid 9-digit ABA routing number.",
      severity: "error",
      field: "immediateDestinationRouting",
    });
  }
  if (!isValidRoutingNumber(config.immediateOriginRouting)) {
    issues.push({
      code: "origin_routing_invalid",
      message: "Immediate origin routing must be a valid 9-digit ABA routing number.",
      severity: "error",
      field: "immediateOriginRouting",
    });
  }
  if (!/^\d{8}$/.test(config.originatingDfiIdentification)) {
    issues.push({
      code: "originating_dfi_invalid",
      message: "Originating DFI identification must be 8 digits.",
      severity: "error",
      field: "originatingDfiIdentification",
    });
  }
  if (!/^[a-zA-Z0-9]$/.test(config.fileIdModifier)) {
    issues.push({
      code: "file_id_modifier_invalid",
      message: "File ID modifier must be one alphanumeric character.",
      severity: "error",
      field: "fileIdModifier",
    });
  }
  return issues;
}

function validateRows(
  rows: PaymentRowInput[],
  config: OriginatorConfig
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  rows.forEach((row) => {
    const normalizedName = toUpperAscii(row.name);
    if (normalizedName !== row.name.toUpperCase()) {
      issues.push({
        code: "name_normalized",
        message: "Name was normalized to uppercase ASCII for ACH output.",
        severity: "warning",
        field: "name",
        rowNumber: row.rowNumber,
        originalValue: row.name,
        suggestedFix: "Review the generated recipient name preview.",
      });
    }
    if (normalizedName.length > 22) {
      issues.push({
        code: "name_too_long",
        message: "Recipient name exceeds 22 characters after normalization.",
        severity: "error",
        field: "name",
        rowNumber: row.rowNumber,
        originalValue: row.name,
      });
    }
    if (row.effectiveDate && row.effectiveDate !== config.effectiveEntryDate) {
      issues.push({
        code: "row_effective_date_ignored",
        message: "Row-level effective dates are not supported in the output file and were ignored.",
        severity: "warning",
        field: "effective_date",
        rowNumber: row.rowNumber,
        originalValue: row.effectiveDate,
        suggestedFix: "Use the batch-level effective entry date.",
      });
    }
  });
  return issues;
}

function buildFileHeader(config: OriginatorConfig, createdAt: Date): string {
  const record =
    "1" +
    "01" +
    padLeftSpaces(config.immediateDestinationRouting, 10) +
    padLeftSpaces(config.immediateOriginRouting, 10) +
    dateFormat(createdAt, "yymmdd") +
    dateFormat(createdAt, "hhmm") +
    toUpperAscii(config.fileIdModifier.slice(0, 1)) +
    "094" +
    "10" +
    "1" +
    padRightSpaces(toUpperAscii(config.immediateDestinationName), 23) +
    padRightSpaces(toUpperAscii(config.immediateOriginName), 23) +
    padRightSpaces(toUpperAscii(config.referenceCode), 8);
  return assertRecord(record, "File Header");
}

function buildBatchHeader(config: OriginatorConfig, batchNumber: number): string {
  const record =
    "5" +
    "220" +
    padRightSpaces(toUpperAscii(config.companyName), 16) +
    padRightSpaces(toUpperAscii(config.companyDiscretionaryData), 20) +
    padRightSpaces(toUpperAscii(config.companyIdentification), 10) +
    "PPD" +
    padRightSpaces(toUpperAscii(config.companyEntryDescription), 10) +
    padRightSpaces(toUpperAscii(config.companyDescriptiveDate), 6) +
    isoToYYMMDD(config.effectiveEntryDate) +
    "   " +
    "1" +
    padLeftZeros(config.originatingDfiIdentification, 8) +
    padLeftZeros(batchNumber, 7);
  return assertRecord(record, "Batch Header");
}

function buildEntryDetail(
  row: PaymentRowInput,
  config: OriginatorConfig,
  sequence: number
): string {
  const transactionCode = row.accountType === "checking" ? "22" : "32";
  const cents = amountToCents(row.amount);
  const record =
    "6" +
    transactionCode +
    row.routingNumber.slice(0, 8) +
    row.routingNumber.slice(8, 9) +
    padRightSpaces(toUpperAscii(row.accountNumber), 17) +
    padLeftZeros(cents, 10) +
    padRightSpaces(toUpperAscii(row.idNumber), 15) +
    padRightSpaces(toUpperAscii(row.name), 22) +
    padRightSpaces(toUpperAscii(row.discretionaryData), 2) +
    "0" +
    padLeftZeros(config.originatingDfiIdentification, 8) +
    padLeftZeros(sequence, 7);
  return assertRecord(record, "Entry Detail");
}

function buildBatchControl(args: {
  entryCount: number;
  entryHash: number;
  totalCreditCents: number;
  config: OriginatorConfig;
  batchNumber: number;
}): string {
  const { entryCount, entryHash, totalCreditCents, config, batchNumber } = args;
  const record =
    "8" +
    "220" +
    padLeftZeros(entryCount, 6) +
    padLeftZeros(entryHash, 10) +
    padLeftZeros(0, 12) +
    padLeftZeros(totalCreditCents, 12) +
    padRightSpaces(toUpperAscii(config.companyIdentification), 10) +
    padRightSpaces("", 19) +
    padRightSpaces("", 6) +
    padLeftZeros(config.originatingDfiIdentification, 8) +
    padLeftZeros(batchNumber, 7);
  return assertRecord(record, "Batch Control");
}

function buildFileControl(args: {
  batchCount: number;
  blockCount: number;
  entryCount: number;
  entryHash: number;
  totalCreditCents: number;
}): string {
  const record =
    "9" +
    padLeftZeros(args.batchCount, 6) +
    padLeftZeros(args.blockCount, 6) +
    padLeftZeros(args.entryCount, 8) +
    padLeftZeros(args.entryHash, 10) +
    padLeftZeros(0, 12) +
    padLeftZeros(args.totalCreditCents, 12) +
    padRightSpaces("", 39);
  return assertRecord(record, "File Control");
}

function buildPaddingLines(currentLineCount: number): string[] {
  const remainder = currentLineCount % 10;
  if (remainder === 0) {
    return [];
  }
  return Array.from({ length: 10 - remainder }, () => "9".repeat(94));
}

export function computeEntryHash(routingNumbers: string[]): number {
  return routingNumbers.reduce(
    (sum, routingNumber) => sum + Number.parseInt(routingNumber.slice(0, 8), 10),
    0
  ) % 10 ** 10;
}

export function amountToCents(value: string | number): number {
  return Math.round(Number(value) * 100);
}

function parseAmount(value: string): number {
  if (!/^-?\d+(\.\d+)?$/.test(value.trim())) {
    throw new Error("Amount must be a valid decimal value.");
  }
  const parsed = Number(value);
  if (parsed <= 0) {
    throw new Error("Amount must be greater than zero.");
  }
  if (value.includes(".") && value.split(".")[1]?.length > 2) {
    throw new Error("Amount can have at most 2 decimal places.");
  }
  return parsed;
}

function toUpperAscii(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\x20-\x7E]/g, "")
    .toUpperCase();
}

function ensureAscii(value: string): boolean {
  return /^[\x20-\x7E]*$/.test(value);
}

function padLeftZeros(value: string | number, length: number): string {
  return String(value).padStart(length, "0").slice(-length);
}

function padRightSpaces(value: string, length: number): string {
  return value.slice(0, length).padEnd(length, " ");
}

function padLeftSpaces(value: string, length: number): string {
  return value.slice(0, length).padStart(length, " ");
}

function assertRecord(record: string, label: string): string {
  if (record.length !== 94) {
    throw new Error(`${label} must be 94 characters, received ${record.length}.`);
  }
  return record;
}

function rowIssue(
  rowNumber: number,
  field: string,
  code: string,
  message: string,
  originalValue: string,
  suggestedFix?: string
): ValidationIssue {
  return {
    code,
    message,
    severity: "error",
    field,
    rowNumber,
    originalValue,
    suggestedFix,
  };
}

function csvEscape(value: string | number): string {
  const text = String(value);
  if (text.includes(",") || text.includes('"') || text.includes("\n")) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function emptySummary(): BuildSummary {
  return {
    entries: 0,
    totalCreditCents: 0,
    totalDebitCents: 0,
    warnings: 0,
    errors: 1,
    batchCount: 1,
    blockCount: 0,
    serviceClass: "220",
    secCode: "PPD",
    generatedAt: new Date().toISOString(),
    effectiveDate: undefined,
    originatingDfi: "",
    immediateDestination: "",
  };
}

function dateFormat(date: Date, kind: "yymmdd" | "hhmm"): string {
  if (kind === "yymmdd") {
    return `${String(date.getUTCFullYear()).slice(-2)}${String(date.getUTCMonth() + 1).padStart(2, "0")}${String(date.getUTCDate()).padStart(2, "0")}`;
  }
  return `${String(date.getUTCHours()).padStart(2, "0")}${String(date.getUTCMinutes()).padStart(2, "0")}`;
}

function isoToYYMMDD(value: string): string {
  const [year, month, day] = value.split("-");
  return `${year.slice(-2)}${month}${day}`;
}

function computeRoutingCheckDigit(routingNumber: string): number {
  const digits = routingNumber
    .slice(0, 8)
    .split("")
    .map((char) => Number.parseInt(char, 10));
  const weights = [3, 7, 1, 3, 7, 1, 3, 7];
  const total = digits.reduce((sum, digit, index) => sum + digit * weights[index], 0);
  return (10 - (total % 10)) % 10;
}

function isValidRoutingNumber(routingNumber: string): boolean {
  return /^\d{9}$/.test(routingNumber) && computeRoutingCheckDigit(routingNumber) === Number(routingNumber[8]);
}

export function todayIso(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function makeUtcDate(year: number, month: number, day: number): Date {
  return new Date(Date.UTC(year, month - 1, day));
}

function fromIso(value: string): Date {
  const [year, month, day] = value.split("-").map(Number);
  return makeUtcDate(year, month, day);
}

function toIso(date: Date): string {
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}-${String(date.getUTCDate()).padStart(2, "0")}`;
}

function addUtcDays(date: Date, days: number): Date {
  const next = new Date(date);
  next.setUTCDate(next.getUTCDate() + days);
  return next;
}

function isWeekend(value: string): boolean {
  const date = fromIso(value);
  const weekday = date.getUTCDay();
  return weekday === 0 || weekday === 6;
}

function nthWeekday(year: number, month: number, weekday: number, occurrence: number): Date {
  let current = makeUtcDate(year, month, 1);
  while (current.getUTCDay() !== weekday) {
    current = addUtcDays(current, 1);
  }
  return addUtcDays(current, (occurrence - 1) * 7);
}

function lastWeekday(year: number, month: number, weekday: number): Date {
  let current = month === 12 ? makeUtcDate(year + 1, 1, 1) : makeUtcDate(year, month + 1, 1);
  current = addUtcDays(current, -1);
  while (current.getUTCDay() !== weekday) {
    current = addUtcDays(current, -1);
  }
  return current;
}

function observed(day: Date): Date {
  const weekday = day.getUTCDay();
  if (weekday === 6) {
    return addUtcDays(day, -1);
  }
  if (weekday === 0) {
    return addUtcDays(day, 1);
  }
  return day;
}

function usFederalHolidays(year: number): Set<string> {
  return new Set([
    toIso(observed(makeUtcDate(year, 1, 1))),
    toIso(nthWeekday(year, 1, 1, 3)),
    toIso(nthWeekday(year, 2, 1, 3)),
    toIso(lastWeekday(year, 5, 1)),
    toIso(observed(makeUtcDate(year, 6, 19))),
    toIso(observed(makeUtcDate(year, 7, 4))),
    toIso(nthWeekday(year, 9, 1, 1)),
    toIso(nthWeekday(year, 10, 1, 2)),
    toIso(observed(makeUtcDate(year, 11, 11))),
    toIso(nthWeekday(year, 11, 4, 4)),
    toIso(observed(makeUtcDate(year, 12, 25))),
  ]);
}

function isUsFederalHoliday(value: string): boolean {
  return usFederalHolidays(fromIso(value).getUTCFullYear()).has(value);
}

export function nextBusinessDay(value: string): string {
  let current = fromIso(value);
  while ([0, 6].includes(current.getUTCDay()) || isUsFederalHoliday(toIso(current))) {
    current = addUtcDays(current, 1);
  }
  return toIso(current);
}
