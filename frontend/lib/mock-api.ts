import type { ApiError } from "@/lib/api-errors";
import type {
  Difficulty,
  ExerciseSafe,
  GenerateExerciseRequest,
  GeneratedExercise,
} from "@/schemas/exercise";
import type {
  OfficialSolution,
  Submission,
  SubmitSolutionRequest,
} from "@/schemas/submission";


type FullExerciseFixture = {
  id: number;
  topic: string;
  difficulty: Difficulty;
  created_at: string;
  statement: string;
  solution: string;
  explanation: string;
  test_cases: { input: string; expected_output: string }[];
};

const MOCK_EXERCISES: FullExerciseFixture[] = [
  {
    id: 1,
    topic: "vectori",
    difficulty: "medium",
    created_at: "2026-08-01T09:12:00",
    statement:
      "Se citește un vector cu n numere întregi (1 ≤ n ≤ 1000). Determinați a doua cea mai mare valoare distinctă din vector. Dacă vectorul are mai puțin de două valori distincte, afișați -1.",
    solution:
      '#include <iostream>\nusing namespace std;\n\nint main() {\n    int n;\n    cin >> n;\n    int v[1000];\n    for (int i = 0; i < n; i++) cin >> v[i];\n\n    int first = -1, second = -1;\n    for (int i = 0; i < n; i++) {\n        if (v[i] > first) {\n            second = first;\n            first = v[i];\n        } else if (v[i] > second && v[i] != first) {\n            second = v[i];\n        }\n    }\n\n    cout << second << endl;\n    return 0;\n}',
    explanation:
      "Parcurgem vectorul o singură dată, ținând evidența celei mai mari valori (first) și a celei de-a doua celei mai mari valori distincte (second). La fiecare element comparăm cu first și second și actualizăm corespunzător. Complexitate O(n), fără a fi nevoie de sortare.",
    test_cases: [
      { input: "5\n3 7 7 2 9", expected_output: "7" },
      { input: "3\n5 5 5", expected_output: "-1" },
    ],
  },
  {
    id: 2,
    topic: "recursivitate",
    difficulty: "hard",
    created_at: "2026-07-28T16:40:00",
    statement:
      "Scrieți o funcție recursivă care calculează numărul de cifre impare dintr-un număr natural n (0 ≤ n ≤ 10^9), fără a folosi variabile globale sau statice.",
    solution:
      "#include <iostream>\nusing namespace std;\n\nint countOdd(long long n) {\n    if (n == 0) return 0;\n    int digit = n % 10;\n    return (digit % 2 != 0 ? 1 : 0) + countOdd(n / 10);\n}\n\nint main() {\n    long long n;\n    cin >> n;\n    if (n == 0) {\n        cout << 0 << endl;\n        return 0;\n    }\n    cout << countOdd(n) << endl;\n    return 0;\n}",
    explanation:
      "Funcția countOdd extrage ultima cifră a lui n prin n % 10, verifică paritatea ei și apelează recursiv pentru restul numărului (n / 10). Cazul de bază oprește recursivitatea când n devine 0. Cazul n = 0 este tratat separat pentru a afișa corect 0 cifre.",
    test_cases: [
      { input: "13579", expected_output: "5" },
      { input: "2468", expected_output: "0" },
    ],
  },
  {
    id: 3,
    topic: "matrice",
    difficulty: "easy",
    created_at: "2026-07-20T11:05:00",
    statement:
      "Se citește o matrice pătratică de dimensiune n (1 ≤ n ≤ 100) cu numere întregi. Calculați suma elementelor de pe diagonala principală și suma elementelor de pe diagonala secundară.",
    solution:
      '#include <iostream>\nusing namespace std;\n\nint main() {\n    int n;\n    cin >> n;\n    int a[100][100];\n    for (int i = 0; i < n; i++)\n        for (int j = 0; j < n; j++)\n            cin >> a[i][j];\n\n    long long mainSum = 0, secSum = 0;\n    for (int i = 0; i < n; i++) {\n        mainSum += a[i][i];\n        secSum += a[i][n - 1 - i];\n    }\n\n    cout << mainSum << " " << secSum << endl;\n    return 0;\n}',
    explanation:
      "Pentru un element de pe diagonala principală, indicii de linie și coloană sunt egali (a[i][i]). Pentru diagonala secundară, suma dintre linie și coloană este constantă și egală cu n - 1, deci elementul este a[i][n-1-i]. Ambele sume se calculează într-o singură parcurgere.",
    test_cases: [
      { input: "3\n1 2 3\n4 5 6\n7 8 9", expected_output: "15 15" },
      { input: "2\n1 0\n0 1", expected_output: "2 0" },
    ],
  },
  {
    id: 4,
    topic: "șiruri de caractere",
    difficulty: "medium",
    created_at: "2026-08-06T14:22:00",
    statement:
      "Se citește un șir de caractere s format din litere mici ale alfabetului englez (1 ≤ lungime ≤ 200). Verificați dacă șirul este palindrom, ignorând spațiile, și afișați DA sau NU.",
    solution:
      '#include <iostream>\n#include <string>\nusing namespace std;\n\nint main() {\n    string s;\n    getline(cin, s);\n\n    string clean;\n    for (char c : s)\n        if (c != \' \') clean += c;\n\n    int i = 0, j = clean.size() - 1;\n    bool ok = true;\n    while (i < j) {\n        if (clean[i] != clean[j]) { ok = false; break; }\n        i++; j--;\n    }\n\n    cout << (ok ? "DA" : "NU") << endl;\n    return 0;\n}',
    explanation:
      "Construim mai întâi șirul clean fără spații. Apoi folosim doi indici, unul de la început (i) și unul de la sfârșit (j), comparând caracterele simetric față de centrul șirului. Dacă găsim o pereche diferită, șirul nu este palindrom.",
    test_cases: [
      { input: "a p a", expected_output: "DA" },
      { input: "bacalaureat", expected_output: "NU" },
    ],
  },
];

let mockHistory: FullExerciseFixture[] = [...MOCK_EXERCISES];
let nextMockId = 1000;
let nextSubmissionId = 1;
const mockSubmissionsByExercise = new Map<number, Submission[]>();

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function notFound(id: number): ApiError {
  return {
    status: 404,
    code: "not_found",
    detail: `Exercițiul cu id-ul ${id} nu există sau a fost șters.`,
  };
}

function forbidden(detail: string): ApiError {
  return { status: 403, code: "forbidden", detail };
}


function toSafeView(fixture: FullExerciseFixture): ExerciseSafe {
  const submissions = mockSubmissionsByExercise.get(fixture.id) ?? [];
  return {
    id: fixture.id,
    topic: fixture.topic,
    difficulty: fixture.difficulty,
    statement: fixture.statement,
    created_at: fixture.created_at,
    sample_test_cases: fixture.test_cases.slice(0, 1),
    has_submitted: submissions.length > 0,
    submission_count: submissions.length,
    latest_score: submissions.at(-1)?.score,
    completed: submissions.some((s) => s.status === "passed"),
  };
}

function evaluateSubmission(
  fixture: FullExerciseFixture,
  code: string,
): Omit<Submission, "id" | "exercise_id" | "created_at"> {
  const total = fixture.test_cases.length;

  if (code.includes("FAIL_COMPILE")) {
    return {
      score: 0,
      passed_tests: 0,
      total_tests: total,
      status: "compilation_error",
      feedback: "error: expected ';' before '}' token (linia 7)",
    };
  }
  if (code.includes("FAIL_RUNTIME")) {
    return {
      score: 0,
      passed_tests: 0,
      total_tests: total,
      status: "runtime_error",
      feedback: "Programul s-a oprit neașteptat la testul 2 (segmentation fault).",
    };
  }
  if (code.includes("FAIL_ALL")) {
    return {
      score: 0,
      passed_tests: 0,
      total_tests: total,
      status: "failed",
      feedback: "Rezultatele obținute nu corespund cu cele așteptate.",
    };
  }
  if (code.includes("PARTIAL")) {
    const passed = Math.max(1, Math.floor(total / 2));
    return {
      score: Math.round((passed / total) * 100),
      passed_tests: passed,
      total_tests: total,
      status: "partial",
      feedback: `Ai trecut ${passed} din ${total} teste. Verifică și cazurile limită.`,
    };
  }
  if (!/int\s+main/.test(code)) {
    return {
      score: 0,
      passed_tests: 0,
      total_tests: total,
      status: "compilation_error",
      feedback: "error: lipsește funcția 'main'.",
    };
  }

  return {
    score: 100,
    passed_tests: total,
    total_tests: total,
    status: "passed",
    feedback: null,
  };
}

export const mockApi = {
  async generateExercise(
    req: GenerateExerciseRequest,
  ): Promise<GeneratedExercise> {
    await delay(1200);
    const lower = req.topic.toLowerCase();
    const template =
      MOCK_EXERCISES.find((e) => lower.includes(e.topic.split(" ")[0]!)) ??
      MOCK_EXERCISES[Math.floor(Math.random() * MOCK_EXERCISES.length)]!;
    const fixture: FullExerciseFixture = {
      ...template,
      id: nextMockId++,
      topic: req.topic,
      difficulty: req.difficulty as Difficulty,
      created_at: new Date().toISOString(),
    };
    mockHistory = [fixture, ...mockHistory];
    return toSafeView(fixture);
  },

  async listExercises(): Promise<ExerciseSafe[]> {
    await delay(500);
    return mockHistory.map(toSafeView);
  },

  async getExerciseById(id: number): Promise<ExerciseSafe> {
    await delay(500);
    const found = mockHistory.find((e) => e.id === id);
    if (!found) {
      throw notFound(id);
    }
    return toSafeView(found);
  },

  async submitSolution(
    exerciseId: number,
    body: SubmitSolutionRequest,
  ): Promise<Submission> {
    await delay(1500);
    const fixture = mockHistory.find((e) => e.id === exerciseId);
    if (!fixture) {
      throw notFound(exerciseId);
    }

    const evaluation = evaluateSubmission(fixture, body.code);
    const submission: Submission = {
      id: nextSubmissionId++,
      exercise_id: exerciseId,
      created_at: new Date().toISOString(),
      ...evaluation,
    };

    const existing = mockSubmissionsByExercise.get(exerciseId) ?? [];
    mockSubmissionsByExercise.set(exerciseId, [...existing, submission]);

    return submission;
  },

  async getOfficialSolution(exerciseId: number): Promise<OfficialSolution> {
    await delay(400);
    const fixture = mockHistory.find((e) => e.id === exerciseId);
    if (!fixture) {
      throw notFound(exerciseId);
    }
    const submissions = mockSubmissionsByExercise.get(exerciseId) ?? [];
    if (submissions.length === 0) {
      throw forbidden(
        "Soluția oficială devine disponibilă după prima ta trimitere.",
      );
    }
    return { solution: fixture.solution, explanation: fixture.explanation };
  },
};
