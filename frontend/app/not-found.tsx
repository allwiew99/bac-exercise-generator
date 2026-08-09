import Link from "next/link";

export default function NotFound() {
  return (
    <section className="mx-auto max-w-md px-6 py-28 text-center">
      <div className="mx-auto mb-5 flex h-13 w-13 items-center justify-center rounded-2xl bg-[var(--color-danger-bg)] font-display text-xl font-bold text-[var(--color-danger)]">
        404
      </div>
      <h2 className="mb-2.5 font-display text-xl font-semibold">
        Pagina nu a fost găsită
      </h2>
      <p className="mb-6 text-sm leading-relaxed text-[var(--color-text-secondary)]">
        Pagina căutată nu există sau a fost mutată.
      </p>
      <Link
        href="/"
        className="inline-flex items-center justify-center rounded-lg bg-[var(--color-primary)] px-5.5 py-3 text-sm font-bold text-white no-underline hover:no-underline"
      >
        Înapoi la pagina principală
      </Link>
    </section>
  );
}
