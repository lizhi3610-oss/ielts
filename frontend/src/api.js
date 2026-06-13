const API_BASE_URL = "http://localhost:8000";

export async function getQuestions() {
  const response = await fetch(`${API_BASE_URL}/questions`);
  if (!response.ok) {
    throw new Error("Failed to fetch questions");
  }
  return response.json();
}

export async function startPracticeSession(part, topic = null) {
  const response = await fetch(`${API_BASE_URL}/practice/sessions`, {
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
    `${API_BASE_URL}/practice/sessions/${sessionId}/answer`,
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
    `${API_BASE_URL}/practice/sessions/${sessionId}/finish`,
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
  const response = await fetch(`${API_BASE_URL}/exam/start`, {
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
  const response = await fetch(`${API_BASE_URL}/exam/answer`, {
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
  const response = await fetch(`${API_BASE_URL}/exam/finish?session_id=${sessionId}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to finish exam");
  }
  return response.json();
}
