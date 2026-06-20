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
const WECHAT_BROWSER_NOTICE =
  "微信内置浏览器不支持稳定语音识别，请点右上角在浏览器打开";
const QUARK_BROWSER_NOTICE =
  "夸克浏览器暂不支持本页语音识别，请复制链接到 Chrome 或 Safari 打开";

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

function getBrowserEnvironment() {
  if (typeof navigator === "undefined") {
    return {
      isQuark: false,
      isWeChat: false,
    };
  }

  const userAgent = navigator.userAgent || "";
  return {
    isQuark: /Quark|UCBrowser|UCWEB/i.test(userAgent),
    isWeChat: /MicroMessenger/i.test(userAgent),
  };
}

function getBrowserNotice() {
  const browser = getBrowserEnvironment();
  if (browser.isWeChat) {
    return WECHAT_BROWSER_NOTICE;
  }

  if (browser.isQuark) {
    return QUARK_BROWSER_NOTICE;
  }

  return null;
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
  let hasPreparedOutput = false;

  const getCapabilities = () => ({
    browserNotice: getBrowserNotice(),
    input:
      Boolean(getSpeechRecognitionConstructor()) && Boolean(!getBrowserNotice()),
    output: Boolean(getSpeechSynthesis()),
  });

  const prepareOutput = ({ language = DEFAULT_LANGUAGE } = {}) => {
    const speechSynthesis = getSpeechSynthesis();
    if (!speechSynthesis) {
      return false;
    }

    if (hasPreparedOutput) {
      speechSynthesis.resume?.();
      return true;
    }

    try {
      const utterance = new SpeechSynthesisUtterance(".");
      utterance.lang = language;
      utterance.volume = 0;
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.onend = () => {
        hasPreparedOutput = true;
      };
      utterance.onerror = () => {
        hasPreparedOutput = false;
      };

      speechSynthesis.resume?.();
      speechSynthesis.speak(utterance);
      window.setTimeout(() => speechSynthesis.resume?.(), 0);

      // Some mobile browsers do not fire callbacks for muted utterances.
      hasPreparedOutput = true;
      return true;
    } catch (err) {
      hasPreparedOutput = false;
      return false;
    }
  };

  const startListening = ({
    language = DEFAULT_LANGUAGE,
    onPartialResult,
    onResult,
    onStart,
    onEnd,
    onError,
  }) => {
    const browserNotice = getBrowserNotice();
    if (browserNotice) {
      onError?.(browserNotice);
      return;
    }

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
    speechSynthesis.resume?.();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = language;
    utterance.rate = 0.92;
    utterance.pitch = 1;
    let hasStarted = false;
    let startTimer = null;

    const clearStartTimer = () => {
      if (startTimer) {
        window.clearTimeout(startTimer);
        startTimer = null;
      }
    };

    utterance.onstart = () => {
      hasStarted = true;
      clearStartTimer();
      onStart?.();
    };
    utterance.onend = () => {
      clearStartTimer();
      onEnd?.();
    };
    utterance.onerror = (event) => {
      clearStartTimer();
      if (event.error === "interrupted" || event.error === "canceled") {
        return;
      }

      onError?.("语音朗读失败，请点一次朗读考官问题");
    };

    speechSynthesis.speak(utterance);
    window.setTimeout(() => speechSynthesis.resume?.(), 0);
    window.setTimeout(() => speechSynthesis.resume?.(), 250);

    startTimer = window.setTimeout(() => {
      if (
        !hasStarted &&
        !speechSynthesis.speaking &&
        !speechSynthesis.pending
      ) {
        onError?.("自动朗读被浏览器拦截，请点一次朗读考官问题");
      }
    }, 2500);
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
    prepareOutput,
    speak,
    startListening,
    stopListening,
    stopSpeaking,
  };
}
