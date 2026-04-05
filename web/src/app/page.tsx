"use client";

import { ChangeEvent, startTransition, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  FileCheck2,
  Sparkles,
  Upload,
} from "lucide-react";

import {
  ActivePage,
  AppResult,
  DEFAULT_CONFIG,
  OriginatorConfig,
  PaymentRowInput,
  TEMPLATE_CSV,
  UI_COPY,
  ValidationIssue,
  buildFile,
  finalizeBuildResult,
  groupedIssues,
  issueDisplayMessage,
  issueNextStepCopy,
  issueSummaryCopy,
  maskAccountNumber,
  nextBusinessDay,
  parsePaymentCsv,
  resultBanner,
  todayIso,
  validateAch,
} from "@/lib/ach";
import { buildReportPdf } from "@/lib/report";

const NAV_ITEMS: { id: ActivePage; label: string }[] = [
  { id: "landing", label: "Landing" },
  { id: "generate", label: "Generate" },
  { id: "validate", label: "Validate" },
  { id: "results", label: "Results" },
  { id: "help", label: "Help" },
];

export default function Home() {
  const [activePage, setActivePage] = useState<ActivePage>("landing");
  const [generateStep, setGenerateStep] = useState(1);
  const [config, setConfig] = useState<OriginatorConfig>(() => {
    if (typeof window === "undefined") {
      return DEFAULT_CONFIG;
    }
    const stored = window.localStorage.getItem("achlint-config");
    if (!stored) {
      return DEFAULT_CONFIG;
    }
    try {
      return { ...DEFAULT_CONFIG, ...(JSON.parse(stored) as Partial<OriginatorConfig>) };
    } catch {
      window.localStorage.removeItem("achlint-config");
      return DEFAULT_CONFIG;
    }
  });
  const [csvFileName, setCsvFileName] = useState("");
  const [csvRows, setCsvRows] = useState<PaymentRowInput[]>([]);
  const [csvIssues, setCsvIssues] = useState<ValidationIssue[]>([]);
  const [achInputName, setAchInputName] = useState("");
  const [achInputText, setAchInputText] = useState("");
  const [latestResult, setLatestResult] = useState<AppResult | null>(null);
  const [busyLabel, setBusyLabel] = useState("");

  useEffect(() => {
    window.localStorage.setItem("achlint-config", JSON.stringify(config));
  }, [config]);

  const handleCsvUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setBusyLabel("Parsing CSV and checking for blocking issues...");
    const text = await file.text();
    startTransition(() => {
      const parsed = parsePaymentCsv(text);
      setCsvFileName(file.name);
      setCsvRows(parsed.rows);
      setCsvIssues(parsed.issues);
      setGenerateStep(1);
      setBusyLabel("");
    });
  };

  const handleAchUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setAchInputName(file.name);
    setAchInputText(await file.text());
  };

  const runValidation = () => {
    const result = validateAch(achInputText);
    setLatestResult(result);
    setActivePage("results");
  };

  const runGeneration = () => {
    setBusyLabel("Generating ACH artifacts and validating the output...");
    startTransition(() => {
      const finalized = finalizeBuildResult(buildFile(config, csvRows));
      setLatestResult(finalized);
      setBusyLabel("");
      setActivePage("results");
    });
  };

  const downloadTemplate = () => {
    downloadText("achlint_template.csv", TEMPLATE_CSV, "text/csv");
  };

  const downloadExceptions = () => {
    if (!latestResult) {
      return;
    }
    downloadText("exceptions.csv", latestResult.exceptionsCsv, "text/csv");
  };

  const downloadAch = () => {
    if (!latestResult || latestResult.kind !== "build" || !latestResult.achText) {
      return;
    }
    downloadText("payments.ach", latestResult.achText, "text/plain");
  };

  const downloadReport = () => {
    if (!latestResult) {
      return;
    }
    const bytes = buildReportPdf(latestResult);
    downloadBytes("validation_report.pdf", bytes, "application/pdf");
  };

  const previewTotal = csvRows.reduce((sum, row) => sum + row.amount, 0);
  const blockingIssues = csvIssues.filter((issue) => issue.severity === "error").length;
  const warnings = csvIssues.filter((issue) => issue.severity === "warning").length;

  return (
    <main className="min-h-screen bg-white px-4 py-6 text-[#1F1F1C] sm:px-6 lg:px-10">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-6">
        <header className="grid gap-4 lg:grid-cols-[1.4fr_0.8fr]">
          <GlassCard>
            <div className="text-[32px] font-bold tracking-[-0.02em] text-[#1F1F1C]">ACHLint</div>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[#4F4E48]">
              A focused ACH file workspace for spreadsheet-driven payroll and payout operations.
            </p>
          </GlassCard>
          <GlassCard className="text-sm leading-6 text-[#4F4E48]">
            <strong className="text-[#1F1F1C]">Focused scope.</strong> PPD credits only.
            One batch per file. Validation happens before ACH download so operators can catch
            issues earlier.
          </GlassCard>
        </header>

        <nav className="grid gap-2 border-b border-[#E7E3DB] pb-3 sm:grid-cols-5" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setActivePage(item.id)}
              className={`rounded-lg border px-4 py-3 text-sm font-medium transition ${
                activePage === item.id
                  ? "border-[#F36B21] bg-[#FDE7DB] text-[#1F1F1C]"
                  : "border-[#D7D2C7] bg-white text-[#4F4E48] hover:border-[#A8A293] hover:bg-[#FCFBF9]"
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {busyLabel ? <BusyBar label={busyLabel} /> : null}

        {activePage === "landing" ? (
          <div className="space-y-4">
            <section>
              <GlassCard className="relative overflow-hidden">
                <div className="inline-flex items-center gap-2 rounded-md border border-[#F8B089] bg-[#FDE7DB] px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-[#D95A16]">
                  <Sparkles className="h-3.5 w-3.5" />
                  {UI_COPY.landingEyebrow}
                </div>
                <p className="mt-6 max-w-2xl text-lg leading-8 text-[#4F4E48]">
                  {UI_COPY.landingProblem}
                </p>
                <h1 className="mt-4 max-w-4xl text-4xl font-bold tracking-[-0.02em] text-[#1F1F1C] sm:text-5xl">
                  {UI_COPY.landingTitle}
                </h1>
                <p className="mt-4 max-w-3xl text-base leading-8 text-[#4F4E48]">
                  {UI_COPY.landingBody}
                </p>
                <div className="mt-5 text-sm leading-6 text-[#76746B]">{UI_COPY.landingProof}</div>
                <div className="mt-2 text-sm leading-6 text-[#4F4E48]">{UI_COPY.landingNote}</div>
                <div className="mt-8 grid gap-3 md:grid-cols-[1.15fr_1fr_1fr]">
                  <PrimaryButton
                    onClick={() => {
                      setActivePage("generate");
                    }}
                  >
                    Start guided setup
                  </PrimaryButton>
                  <SecondaryButton onClick={downloadTemplate}>Download CSV template</SecondaryButton>
                  <SecondaryButton onClick={() => setActivePage("validate")}>
                    Validate an existing ACH
                  </SecondaryButton>
                </div>
              </GlassCard>
            </section>

            <section className="grid gap-4 md:grid-cols-3">
              <FunnelCard
                step="Step 1"
                title="Bring your spreadsheet"
                body="Use the template or your existing payout CSV with the supported columns."
              />
              <FunnelCard
                step="Step 2"
                title="Fix issues before upload"
                body="ACHLint flags blocking errors and explains them in operator-friendly language."
              />
              <FunnelCard
                step="Step 3"
                title="Download ready-to-use artifacts"
                body="Leave with the ACH file, validation report, and exceptions CSV for follow-up."
              />
            </section>
          </div>
        ) : null}

        {activePage === "generate" ? (
          <div className="space-y-4">
            <SectionIntro
              eyebrow="Generate mode"
              title="Create a validated ACH file"
              body="This workspace follows the natural operator flow: bring in the spreadsheet, confirm company and bank settings, review what blocks the file, then generate artifacts when everything is clean."
            />

            <div className="grid gap-3 md:grid-cols-3">
              <WizardStep
                active={generateStep === 1}
                done={!!csvFileName}
                index={1}
                title="Upload CSV"
                body="Bring in your payout spreadsheet and confirm the file shape."
              />
              <WizardStep
                active={generateStep === 2}
                done={generateStep > 2}
                index={2}
                title="Confirm settings"
                body="Review the originator and bank fields used in the ACH headers."
              />
              <WizardStep
                active={generateStep === 3}
                done={csvFileName.length > 0 && blockingIssues === 0}
                index={3}
                title="Review and generate"
                body="Check readiness, then generate only when blocking issues are cleared."
              />
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              <SecondaryButton onClick={() => setGenerateStep(1)}>Step 1: Upload</SecondaryButton>
              <SecondaryButton onClick={() => setGenerateStep(csvFileName ? 2 : 1)}>
                Step 2: Settings
              </SecondaryButton>
              <SecondaryButton onClick={() => setGenerateStep(csvFileName ? 3 : 1)}>
                Step 3: Review &amp; Generate
              </SecondaryButton>
            </div>

            {generateStep === 1 ? (
              <div className="grid gap-4 lg:grid-cols-2">
                <GlassCard className="space-y-4">
                  <StepBadge>Step 1</StepBadge>
                  <div>
                    <h3 className="text-xl font-semibold text-[#1F1F1C]">Upload your payment CSV</h3>
                    <p className="mt-2 text-sm leading-6 text-[#4F4E48]">
                      Start with the ACHLint template if you want the clearest path on your first run.
                    </p>
                  </div>
                  <div className="rounded-xl border border-dashed border-[#D7D2C7] bg-[#FCFBF9] p-5">
                    <label className="flex cursor-pointer flex-col items-center gap-3 text-center">
                      <span className="rounded-md bg-[#FDE7DB] p-3 text-[#D95A16]">
                        <Upload className="h-5 w-5" />
                      </span>
                      <span className="text-sm font-semibold">Upload payments CSV</span>
                      <span className="text-sm text-[#76746B]">
                        {csvFileName || "CSV with payment rows, routing numbers, and amounts"}
                      </span>
                      <input className="hidden" type="file" accept=".csv,text/csv" onChange={handleCsvUpload} />
                    </label>
                  </div>
                  <SecondaryButton onClick={downloadTemplate}>Download template</SecondaryButton>
                  {csvFileName ? (
                    <div className="rounded-lg border border-[#8FB5AC] bg-[#E6F0ED] p-4 text-sm text-[#183B35]">
                      Your CSV is in place. Review the preview on the right, then continue to settings.
                    </div>
                  ) : (
                    <EmptyState
                      title="Upload required"
                      body="Use the uploader above to bring in your payment CSV. Once the file is in place, you can continue to settings."
                    />
                  )}
                  {csvFileName ? (
                    <PrimaryButton onClick={() => setGenerateStep(2)}>
                      Continue to settings
                    </PrimaryButton>
                  ) : null}
                </GlassCard>

                <GlassCard className="space-y-4">
                  <div>
                    <h3 className="text-xl font-semibold text-[#1F1F1C]">CSV preview</h3>
                    <p className="mt-2 text-sm leading-6 text-[#4F4E48]">
                      ACHLint shows the row count, total credit, and grouped issues before you spend
                      time in the settings form.
                    </p>
                  </div>
                  {csvFileName ? (
                    <>
                      <MetricGrid
                        items={[
                          { label: "Rows parsed", value: String(csvRows.length) },
                          { label: "Total credit", value: currency(previewTotal) },
                          { label: "Blocking issues", value: String(blockingIssues) },
                          { label: "Warnings", value: String(warnings) },
                        ]}
                      />
                      <DataTable
                        headers={["Row", "Recipient", "Routing", "Account", "Type", "Amount"]}
                        rows={csvRows.slice(0, 12).map((row) => [
                          String(row.rowNumber),
                          row.name,
                          row.routingNumber,
                          maskAccountNumber(row.accountNumber),
                          row.accountType,
                          currency(row.amount),
                        ])}
                      />
                      <IssueGroups issues={csvIssues} emptyMessage="Your CSV preview looks clean so far. You can continue to settings." />
                    </>
                  ) : (
                    <EmptyState
                      title="No preview yet"
                      body="Once you upload a CSV, ACHLint will show row counts, totals, and any blocking issues here."
                    />
                  )}
                </GlassCard>
              </div>
            ) : null}

            {generateStep === 2 ? (
              <div className="grid gap-4 lg:grid-cols-[1.08fr_0.92fr]">
                <GlassCard className="space-y-5">
                  <StepBadge>Step 2</StepBadge>
                  <div>
                    <h3 className="text-xl font-semibold text-[#1F1F1C]">Originator settings</h3>
                    <p className="mt-2 text-sm leading-6 text-[#4F4E48]">
                      These values are used in the ACH file header and batch header. Save them for
                      this session, then move to review.
                    </p>
                  </div>
                  <SettingsForm config={config} onChange={setConfig} />
                  <div className="grid gap-3 md:grid-cols-2">
                    <SecondaryButton onClick={() => setGenerateStep(1)}>Back to upload</SecondaryButton>
                    <PrimaryButton onClick={() => setGenerateStep(3)}>Continue to review</PrimaryButton>
                  </div>
                </GlassCard>

                <GlassCard className="space-y-4">
                  <div>
                    <h3 className="text-xl font-semibold text-[#1F1F1C]">Current session settings</h3>
                    <p className="mt-2 text-sm leading-6 text-[#4F4E48]">
                      This supporting pane keeps the current ACH header inputs visible while you work,
                      so you do not need to mentally carry the configuration between steps.
                    </p>
                  </div>
                  <FactGrid
                    items={[
                      ["Company", config.companyName],
                      ["Entry description", config.companyEntryDescription],
                      ["Effective date", config.effectiveEntryDate],
                      ["Destination routing", config.immediateDestinationRouting],
                      ["Origin routing", config.immediateOriginRouting],
                      ["Trace start", String(config.traceNumberStart)],
                    ]}
                  />
                </GlassCard>
              </div>
            ) : null}

            {generateStep === 3 ? (
              <div className="grid gap-4 lg:grid-cols-2">
                <GlassCard className="space-y-4">
                  <StepBadge>Step 3</StepBadge>
                  <div>
                    <h3 className="text-xl font-semibold text-[#1F1F1C]">Readiness review</h3>
                    <p className="mt-2 text-sm leading-6 text-[#4F4E48]">
                      This is the final check before generation. If blocking issues remain, fix them
                      before you generate.
                    </p>
                  </div>
                  <MetricGrid
                    items={[
                      { label: "Rows parsed", value: String(csvRows.length) },
                      { label: "Total credit", value: currency(previewTotal) },
                      { label: "Blocking issues", value: String(blockingIssues) },
                      { label: "Warnings", value: String(warnings) },
                    ]}
                  />
                  <IssueGroups
                    issues={csvIssues}
                    emptyMessage="Your CSV is ready for generation. You can generate artifacts when you are ready."
                  />
                </GlassCard>

                <GlassCard className="space-y-4">
                  <div>
                    <h3 className="text-xl font-semibold text-[#1F1F1C]">Generation summary</h3>
                    <p className="mt-2 text-sm leading-6 text-[#4F4E48]">
                      Use this panel as the final preflight check. It surfaces the exact identifiers
                      and totals that will shape the file you generate.
                    </p>
                  </div>
                  <FactGrid
                    items={[
                      ["Company", config.companyName],
                      ["Effective date", config.effectiveEntryDate],
                      ["Originating DFI", config.originatingDfiIdentification],
                      ["Destination routing", config.immediateDestinationRouting],
                      ["Entries", String(csvRows.length)],
                      ["Projected total", currency(previewTotal)],
                    ]}
                  />
                  <div className="grid gap-3 md:grid-cols-2">
                    <SecondaryButton onClick={() => setGenerateStep(2)}>Back to settings</SecondaryButton>
                    <PrimaryButton onClick={runGeneration}>Generate ACH artifacts</PrimaryButton>
                  </div>
                </GlassCard>
              </div>
            ) : null}
          </div>
        ) : null}

        {activePage === "validate" ? (
          <div className="space-y-4">
            <SectionIntro
              eyebrow="Validate mode"
              title="Inspect an existing ACH file before upload"
              body="Use this mode when you already have a generated ACH file and want a fast confidence check on record order, totals, padding, and MVP support constraints."
            />

            <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
              <GlassCard>
                <h3 className="text-xl font-semibold text-[#1F1F1C]">What ACHLint checks</h3>
                <ul className="mt-4 space-y-3 text-sm leading-6 text-[#4F4E48]">
                  <li>94-character fixed-width records</li>
                  <li>File and batch record order</li>
                  <li>Entry counts, entry hash, and totals</li>
                  <li>PPD credits-only constraints for this MVP</li>
                  <li>Padding and block count rules</li>
                </ul>
              </GlassCard>

              <GlassCard className="space-y-4">
                <div>
                  <h3 className="text-xl font-semibold text-[#1F1F1C]">Upload an ACH file</h3>
                  <p className="mt-2 text-sm leading-6 text-[#4F4E48]">
                    Use this mode to understand what happened in an existing ACH file before you
                    upload it or send it back for correction.
                  </p>
                </div>
                <div className="rounded-xl border border-dashed border-[#D7D2C7] bg-[#FCFBF9] p-5">
                  <label className="flex cursor-pointer flex-col items-center gap-3 text-center">
                    <span className="rounded-md bg-[#FDE7DB] p-3 text-[#D95A16]">
                      <FileCheck2 className="h-5 w-5" />
                    </span>
                    <span className="text-sm font-semibold">Upload ACH file</span>
                    <span className="text-sm text-[#76746B]">
                      {achInputName || ".ach or .txt file"}
                    </span>
                    <input className="hidden" type="file" accept=".ach,.txt,text/plain" onChange={handleAchUpload} />
                  </label>
                </div>
                {achInputText ? (
                  <PrimaryButton onClick={runValidation}>Run validation</PrimaryButton>
                ) : (
                  <EmptyState
                    title="No file uploaded yet"
                    body="Upload an existing ACH/NACHA file to inspect structure, totals, record order, and padding before the next bank upload attempt."
                  />
                )}
              </GlassCard>
            </div>
          </div>
        ) : null}

        {activePage === "results" ? (
          <div className="space-y-4">
            <SectionIntro
              eyebrow="Results"
              title="Your validation outcome"
              body="Review grouped issues, verify the totals, and download the artifacts you need for bank upload or remediation."
            />

            {!latestResult ? (
              <GlassCard>
                <EmptyState
                  title="No results yet"
                  body="Run Generate or Validate to see your validation outcome and download artifacts here."
                />
              </GlassCard>
            ) : (
              <>
                <ResultHero result={latestResult} />

                <div className="grid gap-3 md:grid-cols-2">
                  <SecondaryButton
                    onClick={() => {
                      setActivePage("generate");
                      setGenerateStep(1);
                    }}
                  >
                    Start a new generation run
                  </SecondaryButton>
                  <SecondaryButton onClick={() => setActivePage("validate")}>
                    Validate another file
                  </SecondaryButton>
                </div>

                <MetricGrid
                  items={[
                    { label: "Entries", value: String(latestResult.summary.entries) },
                    {
                      label: "Total credit",
                      value: currency(latestResult.summary.totalCreditCents / 100),
                    },
                    { label: "Blocking issues", value: String(latestResult.summary.errors) },
                    { label: "Warnings", value: String(latestResult.summary.warnings) },
                  ]}
                />

                <IssueGroups issues={latestResult.issues} emptyMessage="No issues were found in this run." />

                <div className="grid gap-4 lg:grid-cols-3">
                  <ArtifactCard
                    title="ACH file"
                    body="This file is available only when the run passes without blocking issues and is ready for bank upload."
                    action={
                      latestResult.kind === "build" && latestResult.achText ? (
                        <PrimaryButton onClick={downloadAch}>Download payments.ach</PrimaryButton>
                      ) : (
                        <DisabledButton>ACH file not available</DisabledButton>
                      )
                    }
                  />
                  <ArtifactCard
                    title="Validation report"
                    body="Human-readable PDF with summary totals, issue details, and next-step guidance."
                    action={<SecondaryButton onClick={downloadReport}>Download validation_report.pdf</SecondaryButton>}
                  />
                  <ArtifactCard
                    title="Exceptions CSV"
                    body="Machine-friendly issue export for remediation and internal review."
                    action={<SecondaryButton onClick={downloadExceptions}>Download exceptions.csv</SecondaryButton>}
                  />
                </div>
              </>
            )}
          </div>
        ) : null}

        {activePage === "help" ? (
          <div className="space-y-4">
            <SectionIntro
              eyebrow="Help"
              title="Product scope and operator guidance"
              body="ACHLint is intentionally narrow so operators can trust what it does today instead of navigating a broad, ambiguous ACH platform."
            />

            <div className="grid gap-4 md:grid-cols-2">
              <GlassCard>
                <h3 className="text-xl font-semibold text-[#1F1F1C]">Supported in v1</h3>
                <ul className="mt-4 space-y-3 text-sm leading-6 text-[#4F4E48]">
                  <li>PPD credits only</li>
                  <li>One batch per file</li>
                  <li>No addenda records</li>
                  <li>CSV-in to ACH-out workflow</li>
                  <li>Existing ACH validator mode</li>
                </ul>
              </GlassCard>
              <GlassCard>
                <h3 className="text-xl font-semibold text-[#1F1F1C]">Not supported in v1</h3>
                <ul className="mt-4 space-y-3 text-sm leading-6 text-[#4F4E48]">
                  <li>Debits</li>
                  <li>CCD, CTX, WEB, TEL, IAT</li>
                  <li>Bank integrations or SFTP push</li>
                  <li>Saved recipients or approval workflows</li>
                  <li>Multi-batch authoring</li>
                </ul>
              </GlassCard>
            </div>

            <GlassCard className="space-y-4">
              <div className="rounded-xl border border-[#D7D2C7] bg-[#FBF1DD] p-4 text-sm leading-6 text-[#4F4E48]">
                ACHLint checks structural and formatting issues for the supported ACH file type.
                Bank-specific policies, cutoffs, and authorization requirements still apply.
              </div>
              <div>
                <h3 className="text-xl font-semibold text-[#1F1F1C]">Recommended workflow</h3>
                <ol className="mt-4 space-y-3 text-sm leading-6 text-[#4F4E48]">
                  <li>1. Download the CSV template and prepare your payout rows.</li>
                  <li>2. Review all blocking errors before generating the ACH file.</li>
                  <li>3. Keep the validation report alongside the uploaded bank file for operational traceability.</li>
                </ol>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row">
                <PrimaryButton
                  onClick={() => {
                    setActivePage("generate");
                  }}
                >
                  Start guided setup
                </PrimaryButton>
                <SecondaryButton onClick={downloadTemplate}>Download CSV template</SecondaryButton>
              </div>
            </GlassCard>
          </div>
        ) : null}
      </div>
    </main>
  );
}

function SettingsForm({
  config,
  onChange,
}: {
  config: OriginatorConfig;
  onChange: (config: OriginatorConfig) => void;
}) {
  const setField = <K extends keyof OriginatorConfig>(field: K, value: OriginatorConfig[K]) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Field label="Company name">
        <input value={config.companyName} onChange={(event) => setField("companyName", event.target.value)} />
      </Field>
      <Field label="Company identification">
        <input
          value={config.companyIdentification}
          onChange={(event) => setField("companyIdentification", event.target.value)}
        />
      </Field>
      <Field label="Immediate destination routing">
        <input
          value={config.immediateDestinationRouting}
          onChange={(event) => setField("immediateDestinationRouting", event.target.value)}
        />
      </Field>
      <Field label="Immediate destination name">
        <input
          value={config.immediateDestinationName}
          onChange={(event) => setField("immediateDestinationName", event.target.value)}
        />
      </Field>
      <Field label="Immediate origin routing">
        <input
          value={config.immediateOriginRouting}
          onChange={(event) => setField("immediateOriginRouting", event.target.value)}
        />
      </Field>
      <Field label="Immediate origin name">
        <input
          value={config.immediateOriginName}
          onChange={(event) => setField("immediateOriginName", event.target.value)}
        />
      </Field>
      <Field label="Company entry description">
        <input
          value={config.companyEntryDescription}
          onChange={(event) => setField("companyEntryDescription", event.target.value)}
        />
      </Field>
      <Field label="Effective entry date">
        <input
          type="date"
          value={config.effectiveEntryDate}
          min={nextBusinessDay(todayIso())}
          onChange={(event) => setField("effectiveEntryDate", event.target.value)}
        />
      </Field>
      <Field label="Originating DFI identification">
        <input
          value={config.originatingDfiIdentification}
          onChange={(event) => setField("originatingDfiIdentification", event.target.value)}
        />
      </Field>
      <Field label="File ID modifier">
        <input
          maxLength={1}
          value={config.fileIdModifier}
          onChange={(event) => setField("fileIdModifier", event.target.value)}
        />
      </Field>
      <Field label="Company discretionary data">
        <input
          value={config.companyDiscretionaryData}
          onChange={(event) => setField("companyDiscretionaryData", event.target.value)}
        />
      </Field>
      <Field label="Company descriptive date">
        <input
          value={config.companyDescriptiveDate}
          onChange={(event) => setField("companyDescriptiveDate", event.target.value)}
        />
      </Field>
      <Field label="Reference code">
        <input
          value={config.referenceCode}
          onChange={(event) => setField("referenceCode", event.target.value)}
        />
      </Field>
      <Field label="Trace number start">
        <input
          type="number"
          min={1}
          value={config.traceNumberStart}
          onChange={(event) => setField("traceNumberStart", Number(event.target.value))}
        />
      </Field>
    </div>
  );
}

function ResultHero({ result }: { result: AppResult }) {
  const banner = resultBanner(result);

  return (
    <GlassCard className="overflow-hidden border-t-2 border-t-[#F36B21]">
      <div
        className={`inline-flex rounded-md border px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${
          banner.tone === "success"
            ? "border-[#8FB5AC] bg-[#E6F0ED] text-[#183B35]"
            : banner.tone === "warning"
              ? "border-[#D9A441] bg-[#FBF1DD] text-[#A7771D]"
              : "border-[#D65A4A] bg-[#FBE7E4] text-[#B63E2E]"
        }`}
      >
        {result.status.replaceAll("_", " ")}
      </div>
      <h2 className="mt-4 text-3xl font-bold tracking-[-0.015em] text-[#1F1F1C]">{banner.title}</h2>
      <p className="mt-3 max-w-3xl text-base leading-8 text-[#4F4E48]">{banner.body}</p>
    </GlassCard>
  );
}

function IssueGroups({
  issues,
  emptyMessage,
}: {
  issues: ValidationIssue[];
  emptyMessage: string;
}) {
  if (!issues.length) {
    return <EmptyState title="Ready for the next step" body={emptyMessage} />;
  }

  const groups = groupedIssues(issues);

  return (
    <div className="space-y-4">
      {(["error", "warning", "info"] as const).map((severity) =>
        groups[severity].length ? (
          <div key={severity} className="space-y-3">
            <div
              className={`rounded-3xl border p-4 ${
                severity === "error"
                  ? "border-rose-200 bg-rose-50"
                  : severity === "warning"
                    ? "border-amber-200 bg-amber-50"
                    : "border-emerald-200 bg-emerald-50"
              }`}
            >
              <div className="text-sm font-bold uppercase tracking-[0.18em] text-slate-900">
                {severity === "error"
                  ? "Blocking issues"
                  : severity === "warning"
                    ? "Warnings to review"
                    : "Informational notes"}
              </div>
              <div className="mt-1 text-sm leading-6 text-slate-700">
                {issueSummaryCopy(severity, groups[severity].length)}
              </div>
            </div>
            <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white/90">
              <div className="hidden grid-cols-[110px_110px_120px_120px_1fr_1fr] border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-500 lg:grid">
                <div>Severity</div>
                <div>Code</div>
                <div>Location</div>
                <div>Field</div>
                <div>What happened</div>
                <div>Next step</div>
              </div>
              {groups[severity].map((issue, index) => (
                <div
                  key={`${issue.code}-${issue.rowNumber ?? issue.lineNumber ?? index}`}
                  className="grid gap-3 border-t border-slate-100 px-4 py-4 first:border-t-0 lg:grid-cols-[110px_110px_120px_120px_1fr_1fr]"
                >
                  <Cell label="Severity">{severity}</Cell>
                  <Cell label="Code">{issue.code}</Cell>
                  <Cell label="Location">
                    {issue.rowNumber ? `Row ${issue.rowNumber}` : issue.lineNumber ? `Line ${issue.lineNumber}` : "—"}
                  </Cell>
                  <Cell label="Field">{issue.field ?? "—"}</Cell>
                  <Cell label="What happened">{issueDisplayMessage(issue)}</Cell>
                  <Cell label="Next step">{issueNextStepCopy(issue)}</Cell>
                </div>
              ))}
            </div>
          </div>
        ) : null
      )}
    </div>
  );
}

function BusyBar({ label }: { label: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-[#E7E3DB] bg-[#FCFBF9] p-4 shadow-none"
    >
      <div className="flex items-center gap-3">
        <div className="h-2 flex-1 overflow-hidden rounded-sm bg-[#F1EFEA]">
          <motion.div
            animate={{ x: ["-10%", "60%"] }}
            transition={{ repeat: Number.POSITIVE_INFINITY, duration: 1.8, ease: "easeInOut" }}
            className="h-full w-1/3 rounded-sm bg-[#F36B21]"
          />
        </div>
        <div className="text-sm font-medium text-[#4F4E48]">{label}</div>
      </div>
    </motion.div>
  );
}

function SectionIntro({
  eyebrow,
  title,
  body,
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <GlassCard className="border-t-2 border-t-[#F36B21]">
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-[#D95A16]">{eyebrow}</div>
      <h1 className="mt-3 text-3xl font-bold tracking-[-0.015em] text-[#1F1F1C]">{title}</h1>
      <p className="mt-3 max-w-3xl text-sm leading-7 text-[#4F4E48]">{body}</p>
    </GlassCard>
  );
}

function GlassCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-xl border border-[#E7E3DB] bg-white p-6 shadow-[0_1px_2px_rgba(31,31,28,0.06)] ${className}`}>
      {children}
    </div>
  );
}

function ArtifactCard({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action: React.ReactNode;
}) {
  return (
    <GlassCard className="space-y-4">
      <div className="text-lg font-semibold text-[#1F1F1C]">{title}</div>
      <p className="text-sm leading-6 text-[#4F4E48]">{body}</p>
      {action}
    </GlassCard>
  );
}

function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-[#E7E3DB] bg-[#F7F6F3] p-5">
      <div className="text-base font-semibold text-[#1F1F1C]">{title}</div>
      <p className="mt-2 text-sm leading-6 text-[#4F4E48]">{body}</p>
    </div>
  );
}

function FunnelCard({
  step,
  title,
  body,
}: {
  step: string;
  title: string;
  body: string;
}) {
  return (
    <GlassCard>
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-[#D95A16]">{step}</div>
      <div className="mt-3 text-lg font-semibold text-[#1F1F1C]">{title}</div>
      <p className="mt-2 text-sm leading-6 text-[#4F4E48]">{body}</p>
    </GlassCard>
  );
}

function WizardStep({
  active,
  done,
  index,
  title,
  body,
}: {
  active: boolean;
  done: boolean;
  index: number;
  title: string;
  body: string;
}) {
  return (
    <div
      className={`rounded-xl border p-5 ${
        active
          ? "border-[#F8B089] bg-[#FDE7DB]"
          : done
            ? "border-[#E7E3DB] bg-[#FCFBF9]"
            : "border-[#E7E3DB] bg-white"
      }`}
    >
      <div
        className={`inline-flex h-9 w-9 items-center justify-center rounded-md text-sm font-semibold ${
          active ? "bg-[#F36B21] text-white" : done ? "bg-[#1F1F1C] text-white" : "bg-[#F1EFEA] text-[#4F4E48]"
        }`}
      >
        {index}
      </div>
      <div className="mt-4 text-base font-semibold text-[#1F1F1C]">{title}</div>
      <p className="mt-2 text-sm leading-6 text-[#4F4E48]">{body}</p>
    </div>
  );
}

function StepBadge({ children }: { children: React.ReactNode }) {
  return (
    <div className="inline-flex rounded-md border border-[#F8B089] bg-[#FDE7DB] px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-[#D95A16]">
      {children}
    </div>
  );
}

function MetricGrid({
  items,
}: {
  items: { label: string; value: string }[];
}) {
  return (
    <div className="grid gap-3 md:grid-cols-4">
      {items.map((item) => (
        <div key={item.label} className="rounded-xl border border-[#E7E3DB] bg-white p-5">
          <div className="text-xs font-semibold uppercase tracking-[0.12em] text-[#76746B]">{item.label}</div>
          <div className="mt-3 text-2xl font-bold tracking-[-0.015em] text-[#1F1F1C]">{item.value}</div>
        </div>
      ))}
    </div>
  );
}

function FactGrid({ items }: { items: [string, string][] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-xl border border-[#E7E3DB] bg-[#FCFBF9] p-5">
          <div className="text-xs font-semibold uppercase tracking-[0.12em] text-[#76746B]">{label}</div>
          <div className="mt-3 break-words font-mono text-sm font-semibold text-[#1F1F1C]">{value}</div>
        </div>
      ))}
    </div>
  );
}

function DataTable({
  headers,
  rows,
}: {
  headers: string[];
  rows: string[][];
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-[#E7E3DB] bg-white">
      <table className="min-w-full divide-y divide-[#E7E3DB]">
        <thead className="bg-[#F7F6F3]">
          <tr>
            {headers.map((header) => (
              <th key={header} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.12em] text-[#76746B]">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#F1EFEA]">
          {rows.map((row, index) => (
            <tr key={index}>
              {row.map((cell, cellIndex) => (
                <td key={`${index}-${cellIndex}`} className="px-4 py-3 text-sm text-[#4F4E48]">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Cell({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#76746B] lg:hidden">
        {label}
      </div>
      <div className="text-sm leading-6 text-[#4F4E48]">{children}</div>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-2 block font-medium text-[#4F4E48]">{label}</span>
      <div className="rounded-lg border border-[#D7D2C7] bg-white px-4 py-3 [&_input]:w-full [&_input]:bg-transparent [&_input]:outline-none">
        {children}
      </div>
    </label>
  );
}

function PrimaryButton({
  children,
  onClick,
}: {
  children: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#F36B21] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#D95A16]"
    >
      {children}
    </button>
  );
}

function SecondaryButton({
  children,
  onClick,
}: {
  children: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-[#D7D2C7] bg-white px-6 py-3 text-sm font-medium text-[#1F1F1C] transition hover:bg-[#FCFBF9]"
    >
      {children}
    </button>
  );
}

function DisabledButton({ children }: { children: React.ReactNode }) {
  return (
    <button
      type="button"
      disabled
      className="inline-flex min-h-12 items-center justify-center rounded-lg border border-[#E7E3DB] bg-[#F7F6F3] px-6 py-3 text-sm font-medium text-[#A8A293]"
    >
      {children}
    </button>
  );
}

function currency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function downloadText(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  downloadBlob(filename, blob);
}

function downloadBytes(filename: string, bytes: Uint8Array, mime: string) {
  const arrayBuffer = bytes.buffer.slice(
    bytes.byteOffset,
    bytes.byteOffset + bytes.byteLength
  ) as ArrayBuffer;
  const blob = new Blob([arrayBuffer], { type: mime });
  downloadBlob(filename, blob);
}

function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
