const DEFAULT_LANGUAGE = "en-US";
const RECOGNITION_ERROR_MESSAGES = {
  "audio-capture": "没有检测到可用麦克风",
  "not-allowed": "麦克风权限被拒绝，请在浏览器里允许麦克风",
  "no-speech": "没有识别到语音，请再说一次",
  network: "语音识别网络连接失败",
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

  const getCapabilities = () => ({
    input: Boolean(getSpeechRecognitionConstructor()),
    output: Boolean(getSpeechSynthesis()),
  });

  const startListening = ({
    language = DEFAULT_LANGUAGE,
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

    if (recognition) {
      recognition.stop();
      recognition = null;
    }

    recognition = new SpeechRecognition();
    recognition.lang = language;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      onStart?.();
    };

    recognition.onresult = (event) => {
      const result = event.results?.[0]?.[0];
      if (result?.transcript) {
        onResult?.(result.transcript);
      }
    };

    recognition.onerror = (event) => {
      onError?.(
        RECOGNITION_ERROR_MESSAGES[event.error] ||
          event.error ||
          "语音输入失败"
      );
    };

    recognition.onend = () => {
      recognition = null;
      onEnd?.();
    };

    recognition.start();
  };

  const stopListening = () => {
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
