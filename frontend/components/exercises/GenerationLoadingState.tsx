export function GenerationLoadingState() {
  return (
    <section className="mx-auto max-w-[480px] px-6 py-35 text-center">
      <div
        className="mx-auto h-10 w-10 rounded-full border-[3px] border-[var(--color-border)]"
        style={{
          borderTopColor: "var(--color-primary)",
          animation: "spin 0.8s linear infinite",
        }}
      />
      <h2 className="mt-7 mb-2 font-display text-[19px] font-semibold">
        Generăm și validăm exercițiul...
      </h2>
      <p className="text-sm leading-relaxed text-[var(--color-text-secondary)]">
        Poate dura până la un minut — soluția C++ este compilată și rulată pe
        cazuri de test înainte să fie afișată.
      </p>
    </section>
  );
}
