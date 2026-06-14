import { createBrowserSpeechProvider } from "./browserSpeechProvider";

// Future BosonAI integration can replace this provider export without changing
// the conversation UI.
export const speechProvider = createBrowserSpeechProvider();
