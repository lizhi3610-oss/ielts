const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? "http://localhost:8000" : "");

function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

export async function getQuestions() {
  const response = await fetch(apiUrl("/questions"));
  if (!response.ok) {
    throw new Error("Failed to fetch questions");
  }
  return response.json();
}

export async function startPracticeSession(part, topic = null) {
  const response = await fetch(apiUrl("/practice/sessions"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ part, topic }),
  });
  if (!response.ok) {
    throw new Error("Failed to start practice session");
  }
  return response.json();
}

export async function submitPracticeAnswer(sessionId, answer) {
  const response = await fetch(
    apiUrl(`/practice/sessions/${sessionId}/answer`),
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ answer }),
    }
  );
  if (!response.ok) {
    throw new Error("Failed to submit practice answer");
  }
  return response.json();
}

export async function finishPracticeSession(sessionId) {
  const response = await fetch(
    apiUrl(`/practice/sessions/${sessionId}/finish`),
    {
      method: "POST",
    }
  );
  if (!response.ok) {
    throw new Error("Failed to finish practice session");
  }
  return response.json();
}

export async function startExam(questionId) {
  const response = await fetch(apiUrl("/exam/start"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question_id: questionId }),
  });
  if (!response.ok) {
    throw new Error("Failed to start exam");
  }
  return response.json();
}

export async function submitAnswer(sessionId, answer) {
  const response = await fetch(apiUrl("/exam/answer"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ session_id: sessionId, answer }),
  });
  if (!response.ok) {
    throw new Error("Failed to submit answer");
  }
  return response.json();
}

export async function finishExam(sessionId) {
  const response = await fetch(apiUrl(`/exam/finish?session_id=${sessionId}`), {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to finish exam");
  }
  return response.json();
}
