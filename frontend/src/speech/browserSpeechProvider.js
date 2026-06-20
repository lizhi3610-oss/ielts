const DEFAULT_LANGUAGE = "en-US";
const MOBILE_NO_RESULT_TIMEOUT_MS = 18000;
const DESKTOP_NO_RESULT_TIMEOUT_MS = 24000;
const RECOGNITION_ERROR_MESSAGES = {
  "audio-capture": "没有检测到可用麦克风",
  "language-not-supported": "当前浏览器不支持英文语音识别",
  "no-speech": "没有识别到语音，请再说一次",
  "not-allowed": "麦克风权限被拒绝，请在浏览器里允许麦克风",
  network: "语音识别网络连接失败",
  "service-not-allowed": "当前浏览器的语音识别服务不可用，请换 Chrome 或 Edge 再试",
};

function getSpeechRecognitionConstructor() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function getSpeechSynthesis() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.speechSynthesis || null;
}

function isMobileBrowser() {
  if (typeof navigator === "undefined") {
    return false;
  }

  return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || "");
}

function getNoResultTimeoutMs() {
  return isMobileBrowser()
    ? MOBILE_NO_RESULT_TIMEOUT_MS
    : DESKTOP_NO_RESULT_TIMEOUT_MS;
}

function appendTranscript(currentText, transcript) {
  const cleanTranscript = transcript.trim();
  if (!cleanTranscript) {
    return currentText;
  }

  const cleanCurrentText = currentText.trim();
  return cleanCurrentText
    ? `${cleanCurrentText} ${cleanTranscript}`
    : cleanTranscript;
}

export function createBrowserSpeechProvider() {
  let recognition = null;
  let stopActiveRecognition = null;

  const getCapabilities = () => ({
    input: Boolean(getSpeechRecognitionConstructor()),
    output: Boolean(getSpeechSynthesis()),
  });

  const startListening = ({
    language = DEFAULT_LANGUAGE,
    onPartialResult,
    onResult,
    onStart,
    onEnd,
    onError,
  }) => {
    const SpeechRecognition = getSpeechRecognitionConstructor();
    if (!SpeechRecognition) {
      onError?.("当前浏览器不支持语音输入");
      return;
    }

    let noResultTimer = null;
    let hasRecognitionError = false;
    let hasAnyTranscript = false;
    let latestInterimTranscript = "";
    let stoppedManually = false;

    const clearNoResultTimer = () => {
      if (noResultTimer) {
        window.clearTimeout(noResultTimer);
        noResultTimer = null;
      }
    };

    const stopExistingRecognition = () => {
      if (stopActiveRecognition) {
        stopActiveRecognition();
        return;
      }

      if (recognition) {
        recognition.stop();
        recognition = null;
      }
    };

    stopExistingRecognition();

    const currentRecognition = new SpeechRecognition();
    recognition = currentRecognition;
    currentRecognition.lang = language;
    currentRecognition.continuous = !isMobileBrowser();
    currentRecognition.interimResults = true;
    currentRecognition.maxAlternatives = 1;

    const stopCurrentRecognition = () => {
      stoppedManually = true;
      clearNoResultTimer();
      if (recognition === currentRecognition) {
        try {
          currentRecognition.stop();
        } catch (err) {
          recognition = null;
        }
        recognition = null;
      }
    };

    stopActiveRecognition = stopCurrentRecognition;

    currentRecognition.onstart = () => {
      onStart?.();
      noResultTimer = window.setTimeout(() => {
        if (!hasAnyTranscript && recognition === currentRecognition) {
          hasRecognitionError = true;
          onError?.("还没有识别到声音，请靠近麦克风再说一次");
          currentRecognition.stop();
        }
      }, getNoResultTimeoutMs());
    };

    currentRecognition.onresult = (event) => {
      const finalTranscripts = [];
      const interimTranscripts = [];
      const startIndex = event.resultIndex ?? 0;

      for (let index = startIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        const transcript = result?.[0]?.transcript?.trim();
        if (!transcript) {
          continue;
        }

        hasAnyTranscript = true;
        clearNoResultTimer();

        if (result.isFinal) {
          finalTranscripts.push(transcript);
        } else {
          interimTranscripts.push(transcript);
        }
      }

      if (interimTranscripts.length > 0) {
        latestInterimTranscript = interimTranscripts.join(" ");
        onPartialResult?.(latestInterimTranscript);
      }

      if (finalTranscripts.length > 0) {
        latestInterimTranscript = "";
        onPartialResult?.("");
        onResult?.(finalTranscripts.join(" "));
      }
    };

    currentRecognition.onerror = (event) => {
      clearNoResultTimer();
      if (stoppedManually || event.error === "aborted") {
        return;
      }

      hasRecognitionError = true;
      const message =
        RECOGNITION_ERROR_MESSAGES[event.error] ||
        event.error ||
        "语音输入失败";

      onError?.(message);
    };

    currentRecognition.onnomatch = () => {
      onError?.("没有听清这段回答，请再说一次");
    };

    currentRecognition.onend = () => {
      clearNoResultTimer();
      if (latestInterimTranscript) {
        onResult?.(latestInterimTranscript);
      } else if (
        !hasAnyTranscript &&
        !hasRecognitionError &&
        !stoppedManually
      ) {
        onError?.("没有识别到语音，请再说一次");
      }

      if (recognition === currentRecognition) {
        recognition = null;
      }
      if (stopActiveRecognition === stopCurrentRecognition) {
        stopActiveRecognition = null;
      }
      onEnd?.();
    };

    try {
      currentRecognition.start();
    } catch (err) {
      clearNoResultTimer();
      if (recognition === currentRecognition) {
        recognition = null;
      }
      if (stopActiveRecognition === stopCurrentRecognition) {
        stopActiveRecognition = null;
      }
      onError?.("语音输入启动失败，请刷新页面后再试");
    }
  };

  const stopListening = () => {
    if (stopActiveRecognition) {
      stopActiveRecognition();
      return;
    }

    if (recognition) {
      recognition.stop();
      recognition = null;
    }
  };

  const speak = ({
    text,
    language = DEFAULT_LANGUAGE,
    onStart,
    onEnd,
    onError,
  }) => {
    const speechSynthesis = getSpeechSynthesis();
    const cleanText = text?.trim();
    if (!speechSynthesis || !cleanText) {
      onError?.("当前浏览器不支持语音朗读");
      return;
    }

    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = language;
    utterance.rate = 0.92;
    utterance.pitch = 1;

    utterance.onstart = () => {
      onStart?.();
    };
    utterance.onend = () => {
      onEnd?.();
    };
    utterance.onerror = (event) => {
      if (event.error === "interrupted" || event.error === "canceled") {
        return;
      }

      onError?.("语音朗读失败");
    };

    speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    const speechSynthesis = getSpeechSynthesis();
    if (speechSynthesis) {
      speechSynthesis.cancel();
    }
  };

  return {
    appendTranscript,
    getCapabilities,
    speak,
    startListening,
    stopListening,
    stopSpeaking,
  };
}
