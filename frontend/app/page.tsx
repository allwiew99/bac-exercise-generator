import { Footer } from "@/components/layout/Footer";
import { LandingCtas } from "@/components/marketing/LandingCtas";

const PIPELINE_STEPS = [
  {
    number: "01",
    title: "AI generează",
    description:
      "Enunțul, soluția C++ și cazurile de test sunt generate de model.",
  },
  {
    number: "02",
    title: "Soluția e compilată",
    description:
      "Codul C++ generat este compilat automat, fără intervenție manuală.",
  },
  {
    number: "03",
    title: "Testele sunt rulate",
    description:
      "Fiecare caz de test este executat, iar rezultatul comparat cu cel așteptat.",
  },
  {
    number: "04",
    title: "Doar cele validate rămân",
    description:
      "Exercițiile care nu trec testele sunt respinse, nu ajung la tine.",
  },
];

export default function LandingPage() {
  return (
    <>
      <section className="mx-auto max-w-[800px] px-6 pt-24 pb-16 text-center">
        <div className="mb-6 inline-block rounded-[20px] bg-[var(--color-accent-bg)] px-3.5 py-1.5 text-[13px] font-semibold text-[var(--color-primary)]">
          Bacalaureat · Informatică
        </div>
        <h1 className="mb-5 font-display text-[48px] leading-[1.1] font-bold tracking-tight">
          Exerciții de informatică generate și verificate automat
        </h1>
        <p className="mb-9 text-lg leading-relaxed text-[var(--color-text-secondary)]">
          Alege un subiect și un nivel de dificultate. Un model AI generează
          enunțul și soluția C++, iar fiecare exercițiu este compilat și
          testat înainte să ajungă la tine.
        </p>
        <LandingCtas />
      </section>

      <section className="mx-auto max-w-[1120px] px-6 pt-10 pb-25">
        <h2 className="mb-10 text-center font-display text-[22px] font-semibold">
          Fiecare exercițiu trece printr-un pipeline de validare
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PIPELINE_STEPS.map((step) => (
            <div
              key={step.number}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6"
            >
              <div className="mb-2.5 font-display text-[13px] font-bold text-[var(--color-primary)]">
                {step.number}
              </div>
              <div className="mb-2 font-semibold">{step.title}</div>
              <div className="text-sm leading-relaxed text-[var(--color-text-secondary)]">
                {step.description}
              </div>
            </div>
          ))}
        </div>
      </section>

      <Footer />
    </>
  );
}
