import assert from "node:assert/strict";
import test from "node:test";

import { createBrowserSpeechProvider } from "./browserSpeechProvider.js";

class MockSpeechSynthesisUtterance {
  constructor(text) {
    this.text = text;
    this.voice = null;
  }
}

function installSpeechEnvironment({ paused = false } = {}) {
  const events = [];
  const voices = [
    {
      default: true,
      lang: "zh-CN",
      localService: true,
      name: "Tingting",
    },
    {
      default: false,
      lang: "en-US",
      localService: true,
      name: "Samantha",
    },
  ];
  const speechSynthesis = {
    paused,
    pending: false,
    speaking: false,
    cancel() {
      events.push({ type: "cancel" });
      this.pending = false;
      this.speaking = false;
    },
    getVoices() {
      return voices;
    },
    resume() {
      events.push({ type: "resume" });
      this.paused = false;
    },
    speak(utterance) {
      events.push({
        text: utterance.text,
        type: "speak",
        voice: utterance.voice,
      });

      if (utterance.text === ".") {
        utterance.onend?.();
        return;
      }

      this.speaking = true;
      utterance.onstart?.();
    },
  };

  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    value: { userAgent: "Mozilla/5.0 (iPhone) Safari/605.1.15" },
  });
  globalThis.SpeechSynthesisUtterance = MockSpeechSynthesisUtterance;
  globalThis.window = {
    clearTimeout,
    setTimeout,
    speechSynthesis,
  };

  return { events, speechSynthesis, voices };
}

test("prepares once and speaks the question once without forcing resume", () => {
  const { events, voices } = installSpeechEnvironment();
  const provider = createBrowserSpeechProvider();

  provider.prepareOutput();
  provider.prepareOutput();
  provider.speak({ text: "hello" });

  const spokenEvents = events.filter((event) => event.type === "speak");
  assert.deepEqual(
    spokenEvents.map((event) => event.text),
    [".", "hello"]
  );
  assert.equal(spokenEvents[1].voice, voices[1]);
  assert.equal(events.filter((event) => event.type === "resume").length, 0);
  assert.equal(events.filter((event) => event.type === "cancel").length, 0);

  provider.stopSpeaking();
});

test("ignores a duplicate request while the same question is speaking", () => {
  const { events } = installSpeechEnvironment();
  const provider = createBrowserSpeechProvider();

  provider.speak({ text: "Do you work or are you a student?" });
  provider.speak({ text: "Do you work or are you a student?" });

  assert.equal(
    events.filter(
      (event) =>
        event.type === "speak" &&
        event.text === "Do you work or are you a student?"
    ).length,
    1
  );

  provider.stopSpeaking();
});

test("resumes only when the synthesis engine is actually paused", () => {
  const { events } = installSpeechEnvironment({ paused: true });
  const provider = createBrowserSpeechProvider();

  provider.speak({ text: "hello" });

  assert.equal(events.filter((event) => event.type === "resume").length, 1);
  provider.stopSpeaking();
});
