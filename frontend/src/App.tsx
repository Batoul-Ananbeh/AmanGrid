import { useEffect, useState } from "react";

type ConnectionState = "checking" | "connected" | "unavailable";
type AnalysisState = "loading" | "ready" | "error";

interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

interface AnalysisDecision {
  contract_version: string;
  analysis_id: string;
  classification: {
    level: string;
    confidence: number;
  };
  sensitive_findings: Array<{
    type: string;
    count: number;
  }>;
  energy_context: {
    scada_ot_relevant: boolean;
  };
  risk: {
    final_score: number;
    level: string;
  };
  policy: {
    recommendations: Array<{
      action: string;
      execution_mode: "RECOMMENDED" | "SIMULATED";
      is_primary: boolean;
    }>;
    human_review_required: boolean;
  };
}

const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

const classificationLabels: Record<string, string> = {
  Public: "عام",
  Internal: "داخلي",
  Confidential: "سري",
  Restricted: "مقيّد",
};

const riskLabels: Record<string, string> = {
  Low: "منخفض",
  Medium: "متوسط",
  High: "مرتفع",
  Critical: "حرج",
};

const findingLabels: Record<string, string> = {
  SCADA_OT: "بيانات تشغيلية OT/SCADA",
  INTERNAL_IP: "عنوان شبكة داخلي",
  CREDENTIAL: "بيانات اعتماد",
};

const actionLabels: Record<string, string> = {
  QUARANTINE: "عزل المستند",
  ENCRYPT: "تشفير المحتوى",
  RESTRICT_ACCESS: "تقييد الوصول",
  ALERT: "تنبيه فريق الأمن",
  HUMAN_REVIEW: "مراجعة بشرية",
};

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 48 48">
        <path className="brand-mark__frame" d="M7 7h34v34H7z" />
        <path className="brand-mark__grid" d="M16 7v34M32 7v34M7 16h34M7 32h34" />
        <path className="brand-mark__pulse" d="m10 25 8-1 3-7 5 14 3-7 9-1" />
      </svg>
    </span>
  );
}

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3.25 19 6v5.25c0 4.25-2.8 7.93-7 9.5-4.2-1.57-7-5.25-7-9.5V6l7-2.75Z" />
      <path d="m8.8 12.1 2.05 2.05 4.5-4.55" />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 3.5h7l4 4V20H7z" />
      <path d="M14 3.5V8h4M10 12h5M10 15.5h5" />
    </svg>
  );
}

function FindingsIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 6h14M5 12h14M5 18h14" />
      <path d="M8 4v4M15 10v4M11 16v4" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 6v5h-5" />
      <path d="M18.1 16a8 8 0 1 1 .5-7.45L20 11" />
    </svg>
  );
}

function ConnectionStatus({
  connection,
  apiVersion,
}: {
  connection: ConnectionState;
  apiVersion?: string;
}) {
  return (
    <div className={`connection connection--${connection}`} role="status">
      <span className="connection__dot" aria-hidden="true" />
      <span>
        {connection === "checking" && "جاري التحقق"}
        {connection === "connected" && "الخدمات متصلة"}
        {connection === "unavailable" && "الخدمات غير متاحة"}
      </span>
      {connection === "connected" && apiVersion && <small>v{apiVersion}</small>}
    </div>
  );
}

export default function App() {
  const [connection, setConnection] = useState<ConnectionState>("checking");
  const [apiVersion, setApiVersion] = useState<string>();
  const [analysisState, setAnalysisState] = useState<AnalysisState>("loading");
  const [analysis, setAnalysis] = useState<AnalysisDecision>();

  async function loadDemoAnalysis(signal?: AbortSignal) {
    setAnalysisState("loading");

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/demo/analysis`, {
        headers: { Accept: "application/json" },
        signal,
      });
      if (!response.ok) {
        throw new Error("Demo analysis failed.");
      }

      setAnalysis((await response.json()) as AnalysisDecision);
      setAnalysisState("ready");
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setAnalysisState("error");
    }
  }

  useEffect(() => {
    const controller = new AbortController();

    async function initializeApplication() {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/health`, {
          headers: { Accept: "application/json" },
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error("Health check failed.");
        }

        const health = (await response.json()) as HealthResponse;
        if (health.status !== "ok") {
          throw new Error("API is not healthy.");
        }

        setApiVersion(health.version);
        setConnection("connected");
        await loadDemoAnalysis(controller.signal);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setConnection("unavailable");
        setAnalysisState("error");
      }
    }

    void initializeApplication();
    return () => controller.abort();
  }, []);

  const primaryRecommendation = analysis?.policy.recommendations.find(
    (recommendation) => recommendation.is_primary,
  );
  const totalFindings = analysis?.sensitive_findings.reduce(
    (total, finding) => total + finding.count,
    0,
  );

  return (
    <div className="app-shell" dir="rtl">
      <aside className="app-sidebar">
        <div className="sidebar-brand" aria-label="AmanGrid">
          <BrandMark />
          <span>
            <strong>AmanGrid</strong>
            <small>تطبيق أمن بيانات الطاقة</small>
          </span>
        </div>

        <nav className="sidebar-nav" aria-label="أقسام الفحص">
          <a className="is-active" href="#analysis-overview">
            <DocumentIcon />
            <span>ملخص الفحص</span>
          </a>
          <a href="#findings">
            <FindingsIcon />
            <span>المؤشرات</span>
          </a>
          <a href="#recommendations">
            <ShieldIcon />
            <span>التوصيات</span>
          </a>
        </nav>

        <div className="sidebar-footer">
          <ConnectionStatus connection={connection} apiVersion={apiVersion} />
          <span className="test-data-label">بيانات اختبارية آمنة فقط</span>
        </div>
      </aside>

      <div className="mobile-header">
        <div className="mobile-brand">
          <BrandMark />
          <strong>AmanGrid</strong>
        </div>
        <ConnectionStatus connection={connection} />
      </div>

      <div className="app-main">
        <header className="app-toolbar">
          <div>
            <span>الفحص الحالي</span>
            <h1>مراجعة أمن المستند</h1>
          </div>
          <button
            className="toolbar-button"
            type="button"
            onClick={() => void loadDemoAnalysis()}
            disabled={analysisState === "loading" || connection !== "connected"}
          >
            <RefreshIcon />
            <span>تحديث الفحص</span>
          </button>
        </header>

        <div className="safety-strip">
          <ShieldIcon />
          <span>
            التطبيق يعرض توصيات ومحاكاة فقط؛ ولا ينفذ إجراءات حماية تلقائياً.
          </span>
        </div>

        <main className="app-content">
          <section className="case-heading" id="analysis-overview">
            <div>
              <span className="case-heading__label">عينة تحقق تشغيلية</span>
              <h2>نتيجة تحليل المحتوى الحالية</h2>
              <p>
                {analysis?.analysis_id
                  ? `رقم الفحص: ${analysis.analysis_id}`
                  : "يتم تحميل رقم الفحص…"}
              </p>
            </div>
            <span className="review-badge">
              <span aria-hidden="true" />
              بانتظار قرار الموظف
            </span>
          </section>

          {analysisState === "loading" && (
            <section className="state-card" aria-live="polite">
              <span className="loading-indicator" aria-hidden="true" />
              <div>
                <strong>جاري تجهيز نتيجة الفحص</strong>
                <p>يتم التحقق من سلامة الاتصال والعقد المشترك.</p>
              </div>
            </section>
          )}

          {analysisState === "error" && (
            <section className="state-card state-card--error" role="alert">
              <div>
                <strong>تعذّر عرض نتيجة الفحص</strong>
                <p>تأكد من تشغيل خدمات التطبيق ثم أعد المحاولة.</p>
              </div>
              <button type="button" onClick={() => void loadDemoAnalysis()}>
                إعادة المحاولة
              </button>
            </section>
          )}

          {analysisState === "ready" && analysis && (
            <div className="application-grid">
              <div className="primary-column">
                <section className="app-card overview-card" aria-labelledby="overview-title">
                  <header className="card-header">
                    <div>
                      <span className="card-label">النتيجة المختصرة</span>
                      <h2 id="overview-title">التصنيف ومستوى المخاطر</h2>
                    </div>
                    <span className="contract-label">
                      عقد البيانات {analysis.contract_version}
                    </span>
                  </header>

                  <div className="overview-body">
                    <div className="risk-panel">
                      <span>مؤشر المخاطر</span>
                      <div className="risk-meter">
                        <svg viewBox="0 0 120 120" aria-hidden="true">
                          <circle className="risk-meter__track" cx="60" cy="60" r="48" />
                          <circle
                            className="risk-meter__value"
                            cx="60"
                            cy="60"
                            r="48"
                            pathLength="100"
                            strokeDasharray={`${analysis.risk.final_score} 100`}
                          />
                        </svg>
                        <strong>{analysis.risk.final_score}</strong>
                      </div>
                      <b>{riskLabels[analysis.risk.level] ?? analysis.risk.level}</b>
                      <small>يتطلب معالجة ذات أولوية</small>
                    </div>

                    <div className="classification-panel">
                      <div className="classification-value">
                        <span>
                          <small>التصنيف الأمني</small>
                          <strong>
                            {classificationLabels[analysis.classification.level] ??
                              analysis.classification.level}
                          </strong>
                        </span>
                        <b>{analysis.classification.confidence}% ثقة</b>
                      </div>
                      <p>
                        يجمع المحتوى بين معلومات تشغيلية وبيانات شبكة داخلية
                        ومؤشر لبيانات اعتماد؛ لذلك يلزم تقييد تداوله.
                      </p>

                      <dl className="quick-facts">
                        <div>
                          <dt>إجمالي المؤشرات</dt>
                          <dd>{totalFindings}</dd>
                        </div>
                        <div>
                          <dt>سياق OT/SCADA</dt>
                          <dd>{analysis.energy_context.scada_ot_relevant ? "نعم" : "لا"}</dd>
                        </div>
                        <div>
                          <dt>المراجعة البشرية</dt>
                          <dd>
                            {analysis.policy.human_review_required ? "مطلوبة" : "غير مطلوبة"}
                          </dd>
                        </div>
                      </dl>
                    </div>
                  </div>
                </section>

                <section className="app-card findings-card" id="findings" aria-labelledby="findings-title">
                  <header className="card-header">
                    <div>
                      <span className="card-label">تفاصيل الكشف</span>
                      <h2 id="findings-title">المؤشرات الحساسة</h2>
                    </div>
                    <span className="count-badge">{totalFindings} مؤشرات</span>
                  </header>

                  <div className="findings-table" role="table" aria-label="المؤشرات الحساسة">
                    <div className="findings-table__head" role="row">
                      <span role="columnheader">نوع المؤشر</span>
                      <span role="columnheader">العدد</span>
                      <span role="columnheader">حالة الدليل</span>
                    </div>
                    {analysis.sensitive_findings.map((finding) => (
                      <div className="findings-table__row" role="row" key={finding.type}>
                        <span className="finding-name" role="cell">
                          <i aria-hidden="true" />
                          {findingLabels[finding.type] ?? finding.type}
                        </span>
                        <strong role="cell">{finding.count}</strong>
                        <span className="masked-label" role="cell">
                          القيم محجوبة
                        </span>
                      </div>
                    ))}
                  </div>
                </section>

                {primaryRecommendation && (
                  <section
                    className="app-card recommendation-card"
                    id="recommendations"
                    aria-labelledby="recommendations-title"
                  >
                    <header className="card-header">
                      <div>
                        <span className="card-label">قرار السياسة</span>
                        <h2 id="recommendations-title">الإجراء المقترح</h2>
                      </div>
                      <span className="simulation-badge">محاكاة</span>
                    </header>

                    <div className="primary-action">
                      <span className="primary-action__icon">
                        <ShieldIcon />
                      </span>
                      <div>
                        <strong>
                          {actionLabels[primaryRecommendation.action] ??
                            primaryRecommendation.action}
                        </strong>
                        <p>
                          عزل المستند مؤقتاً وإحالته إلى فريق الأمن للمراجعة
                          قبل أي مشاركة خارجية.
                        </p>
                      </div>
                    </div>

                    <div className="secondary-actions" aria-label="توصيات إضافية">
                      {analysis.policy.recommendations
                        .filter((recommendation) => !recommendation.is_primary)
                        .map((recommendation) => (
                          <span key={recommendation.action}>
                            {actionLabels[recommendation.action] ?? recommendation.action}
                          </span>
                        ))}
                    </div>
                  </section>
                )}
              </div>

              <aside className="context-column" aria-label="حالة مسار الفحص">
                <section className="app-card progress-card">
                  <header className="card-header card-header--compact">
                    <div>
                      <span className="card-label">حالة العمل</span>
                      <h2>مسار الفحص</h2>
                    </div>
                  </header>
                  <ol className="progress-list">
                    <li className="is-complete">
                      <span>1</span>
                      <div>
                        <strong>فحص المحتوى</strong>
                        <small>اكتمل</small>
                      </div>
                    </li>
                    <li className="is-complete">
                      <span>2</span>
                      <div>
                        <strong>كشف المؤشرات</strong>
                        <small>اكتمل</small>
                      </div>
                    </li>
                    <li className="is-complete">
                      <span>3</span>
                      <div>
                        <strong>التصنيف والمخاطر</strong>
                        <small>اكتمل</small>
                      </div>
                    </li>
                    <li className="is-current">
                      <span>4</span>
                      <div>
                        <strong>قرار الموظف</strong>
                        <small>بانتظار المراجعة</small>
                      </div>
                    </li>
                  </ol>
                </section>

                <dl className="application-meta">
                  <div>
                    <dt>إصدار التطبيق</dt>
                    <dd>{apiVersion ? `v${apiVersion}` : "—"}</dd>
                  </div>
                  <div>
                    <dt>إصدار العقد</dt>
                    <dd>{analysis.contract_version}</dd>
                  </div>
                  <div>
                    <dt>البيانات</dt>
                    <dd>اختبارية وآمنة</dd>
                  </div>
                </dl>
              </aside>
            </div>
          )}
        </main>
      </div>

      <nav className="mobile-nav" aria-label="أقسام الفحص للجوال">
        <a className="is-active" href="#analysis-overview">
          <DocumentIcon />
          <span>الملخص</span>
        </a>
        <a href="#findings">
          <FindingsIcon />
          <span>المؤشرات</span>
        </a>
        <a href="#recommendations">
          <ShieldIcon />
          <span>التوصيات</span>
        </a>
      </nav>
    </div>
  );
}
