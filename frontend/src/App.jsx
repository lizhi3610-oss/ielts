import { useEffect, useState } from "react";
import "./App.css";
import {
  finishExam,
  finishPracticeSession,
  getQuestions,
  startExam,
  startPracticeSession,
  submitAnswer,
  submitPracticeAnswer,
} from "./api";

const ROUTES = ["/", "/practice", "/mock", "/records"];

function getRouteFromLocation() {
  const path = window.location.pathname;
  return ROUTES.includes(path) ? path : "/";
}

function getDefaultFlow(route) {
  if (route === "/practice") {
    return "part-selection";
  }

  if (route === "/mock") {
    return "mock-start";
  }

  return "idle";
}

function getPartNumber(partLabel) {
  return Number(partLabel.replace("Part ", ""));
}

function App() {
  const initialRoute = getRouteFromLocation();

  const [route, setRoute] = useState(initialRoute);
  const [flow, setFlow] = useState(getDefaultFlow(initialRoute));
  const [mode, setMode] = useState(null);
  const [selectedPart, setSelectedPart] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [currentAnswer, setCurrentAnswer] = useState("");
  const [isFinished, setIsFinished] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handlePopState = () => {
      const nextRoute = getRouteFromLocation();
      setRoute(nextRoute);
      setFlow(getDefaultFlow(nextRoute));
      resetSessionState();
      setError(null);
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const resetSessionState = () => {
    setMode(null);
    setSelectedPart(null);
    setSelectedTopic(null);
    setQuestions([]);
    setSessionId(null);
    setMessages([]);
    setCurrentAnswer("");
    setIsFinished(false);
    setResult(null);
  };

  const navigateTo = (nextRoute) => {
    window.history.pushState({}, "", nextRoute);
    setRoute(nextRoute);
    setFlow(getDefaultFlow(nextRoute));
    resetSessionState();
    setError(null);
  };

  const loadQuestions = async (part = null, nextFlow = "question-selection") => {
    setLoading(true);
    setError(null);

    try {
      const data = await getQuestions();
      const nextQuestions = part
        ? data.filter((question) => question.part === part)
        : data;

      setQuestions(nextQuestions);
      setFlow(nextFlow);
    } catch (err) {
      setError("加载题目失败，请检查后端服务是否启动");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPracticePart = (part) => {
    setMode("practice");
    setSelectedPart(part);
    setSelectedTopic(null);
    loadQuestions(part, "topic-selection");
  };

  const handleStartMock = () => {
    setMode("mock");
    setSelectedPart(null);
    setSelectedTopic(null);
    loadQuestions();
  };

  const handleStartPracticeSession = async (topic = null) => {
    if (!selectedPart) {
      setError("请先选择练习 Part");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await startPracticeSession(getPartNumber(selectedPart), topic);
      setSessionId(data.session_id);
      setSelectedTopic(data.topic);
      setMessages([
        {
          role: "examiner",
          content: data.current_question,
        },
      ]);
      setCurrentAnswer("");
      setIsFinished(false);
      setResult(null);
      setFlow("conversation");
    } catch (err) {
      setError("开始练习失败");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectMockQuestion = async (questionId) => {
    setLoading(true);
    setError(null);

    try {
      const data = await startExam(questionId);
      setSessionId(data.session_id);
      setMessages([
        {
          role: "examiner",
          content: data.current_question,
        },
      ]);
      setCurrentAnswer("");
      setIsFinished(false);
      setResult(null);
      setFlow("conversation");
    } catch (err) {
      setError("开始模拟考试失败");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!currentAnswer.trim()) {
      setError("请输入回答内容");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const userMessage = {
        role: "user",
        content: currentAnswer,
      };
      setMessages((prev) => [...prev, userMessage]);

      if (mode === "practice") {
        const data = await submitPracticeAnswer(sessionId, currentAnswer);
        setCurrentAnswer("");
        setSelectedTopic(data.topic);
        setMessages((prev) => [
          ...prev,
          {
            role: "examiner",
            content: data.next_question,
          },
        ]);
        return;
      }

      const data = await submitAnswer(sessionId, currentAnswer);
      setCurrentAnswer("");

      if (data.is_finished) {
        setIsFinished(true);
      } else {
        const examinerMessage = {
          role: "examiner",
          content: data.next_question,
        };
        setMessages((prev) => [...prev, examinerMessage]);
      }
    } catch (err) {
      setError("提交回答失败");
    } finally {
      setLoading(false);
    }
  };

  const handleFinishSession = async () => {
    setLoading(true);
    setError(null);

    try {
      const data =
        mode === "practice"
          ? await finishPracticeSession(sessionId)
          : await finishExam(sessionId);
      setResult(data);
      setFlow("result");
    } catch (err) {
      setError("获取评分失败");
    } finally {
      setLoading(false);
    }
  };

  const handleBackToRouteStart = () => {
    resetSessionState();
    setFlow(getDefaultFlow(route));
    setError(null);
  };

  const pageTitle =
    mode === "practice" ? "练习对话进行中" : "模拟考试进行中";
  const topicOptions = Array.from(
    new Map(questions.map((question) => [question.topic, question])).values()
  );

  return (
    <div className="app">
      <div className="container">
        <nav className="top-nav" aria-label="Main navigation">
          <button
            className={route === "/" ? "nav-link active" : "nav-link"}
            onClick={() => navigateTo("/")}
            type="button"
          >
            Home
          </button>
          <button
            className={route === "/practice" ? "nav-link active" : "nav-link"}
            onClick={() => navigateTo("/practice")}
            type="button"
          >
            Practice
          </button>
          <button
            className={route === "/mock" ? "nav-link active" : "nav-link"}
            onClick={() => navigateTo("/mock")}
            type="button"
          >
            Mock Exam
          </button>
          <button
            className={route === "/records" ? "nav-link active" : "nav-link"}
            onClick={() => navigateTo("/records")}
            type="button"
          >
            Records
          </button>
        </nav>

        {error && <div className="error">{error}</div>}

        {route === "/" && (
          <section className="home">
            <p className="eyebrow">IELTS Speaking Coach</p>
            <h1>选择今天的练习方式</h1>
            <p className="page-copy">
              从单项练习开始，或进入一套模拟考试流程。
            </p>

            <div className="entry-grid">
              <button
                className="entry-option"
                onClick={() => navigateTo("/practice")}
                type="button"
              >
                <span>练习模式</span>
                <strong>Practice Mode</strong>
              </button>

              <button
                className="entry-option"
                onClick={() => navigateTo("/mock")}
                type="button"
              >
                <span>模拟考试</span>
                <strong>Mock Exam</strong>
              </button>
            </div>

            <button
              className="text-link"
              onClick={() => navigateTo("/records")}
              type="button"
            >
              查看历史记录
            </button>
          </section>
        )}

        {route === "/practice" && flow === "part-selection" && (
          <section className="page-section">
            <p className="eyebrow">Practice Mode</p>
            <h1>选择练习 Part</h1>
            <p className="page-copy">
              先选择 Part 1、Part 2 或 Part 3，再进入题目列表。
            </p>

            <div className="part-grid">
              {["Part 1", "Part 2", "Part 3"].map((part) => (
                <button
                  className="part-option"
                  key={part}
                  onClick={() => handleSelectPracticePart(part)}
                  type="button"
                >
                  {part}
                </button>
              ))}
            </div>
          </section>
        )}

        {route === "/practice" && flow === "topic-selection" && (
          <section className="questions">
            <p className="eyebrow">Practice Mode - {selectedPart}</p>
            <h1>选择 Topic</h1>
            <p className="page-copy">
              选择一个已有 topic，或让系统默认生成本次练习 topic。
            </p>

            <div className="topic-actions">
              <button
                className="btn-primary"
                onClick={() => handleStartPracticeSession(null)}
                disabled={loading}
                type="button"
              >
                {loading ? "启动中..." : "默认生成 Topic"}
              </button>
            </div>

            {loading ? (
              <div className="loading">加载中...</div>
            ) : (
              <div className="question-list">
                {topicOptions.map((question) => (
                  <button
                    className="question-card"
                    key={question.id}
                    onClick={() => handleStartPracticeSession(question.topic)}
                    type="button"
                  >
                    <span>
                      {question.part} - {question.topic}
                    </span>
                    <strong>{question.content}</strong>
                  </button>
                ))}
              </div>
            )}

            <button
              className="btn-secondary"
              onClick={handleBackToRouteStart}
              type="button"
            >
              返回
            </button>
          </section>
        )}

        {route === "/mock" && flow === "mock-start" && (
          <section className="page-section">
            <p className="eyebrow">Mock Exam</p>
            <h1>模拟考试</h1>
            <p className="page-copy">
              后续会按照 IELTS Speaking 的 Part 1、Part 2、Part 3
              完整流程推进；当前阶段先接入已有对话流程。
            </p>

            {loading ? (
              <div className="loading">加载中...</div>
            ) : (
              <button className="btn-primary" onClick={handleStartMock}>
                开始模拟考试
              </button>
            )}
          </section>
        )}

        {route === "/mock" && flow === "question-selection" && (
            <section className="questions">
              <p className="eyebrow">Mock Exam</p>
              <h1>选择一道题目</h1>

              {loading ? (
                <div className="loading">加载中...</div>
              ) : (
                <div className="question-list">
                  {questions.map((question) => (
                    <button
                      className="question-card"
                      key={question.id}
                      onClick={() => handleSelectMockQuestion(question.id)}
                      type="button"
                    >
                      <span>
                        {question.part} - {question.topic}
                      </span>
                      <strong>{question.content}</strong>
                    </button>
                  ))}
                </div>
              )}

              <button
                className="btn-secondary"
                onClick={handleBackToRouteStart}
                type="button"
              >
                返回
              </button>
            </section>
          )}

        {(route === "/practice" || route === "/mock") &&
          flow === "conversation" && (
            <section className="exam">
              <p className="eyebrow">
                {mode === "practice"
                  ? `${selectedPart} - ${selectedTopic}`
                  : "Mock Exam"}
              </p>
              <h1>{pageTitle}</h1>
              <p className="round-info">
                {mode === "practice"
                  ? `已完成 ${messages.filter((message) => message.role === "user").length} 轮回答`
                  : `已完成 ${Math.floor(messages.length / 2)} / 3 轮对话`}
              </p>

              <div className="conversation">
                {messages.map((message, index) => (
                  <div key={index} className={`message ${message.role}`}>
                    <div className="message-role">
                      {message.role === "examiner" ? "考官" : "你"}
                    </div>
                    <div className="message-content">{message.content}</div>
                  </div>
                ))}
              </div>

              {!isFinished ? (
                <>
                  <div className="input-area">
                    <textarea
                      value={currentAnswer}
                      onChange={(event) => setCurrentAnswer(event.target.value)}
                      placeholder="请输入你的回答..."
                      disabled={loading}
                    />
                  </div>
                  <div className="button-group">
                    <button
                      className="btn-primary"
                      onClick={handleSubmitAnswer}
                      disabled={loading}
                      type="button"
                    >
                      {loading ? "提交中..." : "提交回答"}
                    </button>
                    {mode === "practice" && (
                      <button
                        className="btn-secondary"
                        onClick={handleFinishSession}
                        disabled={loading}
                        type="button"
                      >
                        结束练习
                      </button>
                    )}
                  </div>
                </>
              ) : (
                <div className="button-group">
                  <button
                    className="btn-primary"
                    onClick={handleFinishSession}
                    type="button"
                  >
                    查看评分报告
                  </button>
                </div>
              )}
            </section>
          )}

        {(route === "/practice" || route === "/mock") &&
          flow === "result" &&
          result && (
            <section className="result">
              <p className="eyebrow">
                {mode === "practice"
                  ? `${selectedPart} - ${selectedTopic}`
                  : "Mock Exam"}
              </p>
              <h1>{mode === "practice" ? "练习评价" : "评分报告"}</h1>

              {mode === "practice" ? (
                <>
                  <div className="score-grid practice-score">
                    <div className="score-card">
                      <h2>Overall Score</h2>
                      <div className="score">{result.overall_score}</div>
                    </div>
                  </div>

                  <div className="feedback-section">
                    <h2>Fluency Feedback</h2>
                    <p>{result.fluency_feedback}</p>
                  </div>

                  <div className="feedback-section">
                    <h2>Lexical Feedback</h2>
                    <p>{result.lexical_feedback}</p>
                  </div>

                  <div className="feedback-section">
                    <h2>Grammar Feedback</h2>
                    <p>{result.grammar_feedback}</p>
                  </div>

                  <div className="feedback-section">
                    <h2>Suggestions</h2>
                    <p>{result.suggestions}</p>
                  </div>

                  <div className="feedback-section">
                    <h2>Improved Sample Answer</h2>
                    <p>{result.improved_sample_answer}</p>
                  </div>
                </>
              ) : (
                <>
                  <div className="score-grid">
                    <div className="score-card">
                      <h2>总分</h2>
                      <div className="score">{result.overall_score}</div>
                    </div>
                    <div className="score-card">
                      <h2>流利度</h2>
                      <div className="score">{result.fluency_score}</div>
                    </div>
                    <div className="score-card">
                      <h2>词汇</h2>
                      <div className="score">{result.lexical_score}</div>
                    </div>
                    <div className="score-card">
                      <h2>语法</h2>
                      <div className="score">{result.grammar_score}</div>
                    </div>
                  </div>

                  <div className="feedback-section">
                    <h2>反馈</h2>
                    <p>{result.feedback}</p>
                  </div>

                  <div className="feedback-section">
                    <h2>建议</h2>
                    <p>{result.suggestions}</p>
                  </div>
                </>
              )}

              <div className="button-group">
                <button
                  className="btn-secondary"
                  onClick={() => navigateTo("/")}
                  type="button"
                >
                  返回首页
                </button>
              </div>
            </section>
          )}

        {route === "/records" && (
          <section className="page-section">
            <p className="eyebrow">Records</p>
            <h1>历史记录</h1>
            <div className="empty-state">
              历史记录页面已预留，后续阶段会接入练习记录和模拟考试记录。
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

export default App;
