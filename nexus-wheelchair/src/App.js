import React, { useState, useRef } from "react";
import "./App.css";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState("auto");
  const [isListening, setIsListening] = useState(false);
  const chatRef = useRef(null);

  const speak = (text, lang) => {
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = lang === "hi" ? "hi-IN" : "en-IN";
    utter.rate = 1;
    window.speechSynthesis.speak(utter);
  };

  const appendMessage = (role, text) => {
    setMessages((prev) => [...prev, { role, text }]);
    setTimeout(() => {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }, 100);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    const query = input.trim();
    appendMessage("user", query);
    setInput("");

    appendMessage("bot", "Thinking...");

    try {
      const res = await fetch("http://127.0.0.1:5000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, history: [], language }),
      });

      const data = await res.json();
      const reply = data.response || "Sorry, I didn’t understand that.";

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].text = reply;
        return updated;
      });

      speak(reply, language);
    } catch (err) {
      console.error(err);
    }
  };

  const startVoiceInput = () => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = language === "hi" ? "hi-IN" : "en-IN";
    setIsListening(true);
    recognition.start();

    recognition.onresult = (event) => {
      const voiceText = event.results[0][0].transcript;
      setInput(voiceText);
      setIsListening(false);
      sendMessage();
    };

    recognition.onerror = (err) => {
      console.error("Voice error:", err);
      setIsListening(false);
    };
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-br from-blue-100 via-white to-blue-50">
      <div className="bg-white shadow-xl rounded-2xl w-[95%] md:w-[400px] p-5 flex flex-col border border-blue-100">
        <h1 className="text-2xl font-bold text-blue-700 text-center mb-2">
          Nexus – Smart Wheelchair Assistant
        </h1>
        <p className="text-sm text-gray-500 text-center mb-4">
          Voice-enabled bilingual chatbot for the visually impaired
        </p>

        <div
          ref={chatRef}
          className="flex-1 border rounded-lg p-3 mb-3 overflow-y-auto h-80 bg-gray-50"
        >
          {messages.map((m, i) => (
            <div
              key={i}
              className={`my-1 p-2 rounded-lg w-fit max-w-[80%] ${
                m.role === "user"
                  ? "ml-auto bg-blue-100 text-right"
                  : "mr-auto bg-green-100 text-left"
              }`}
            >
              {m.text}
            </div>
          ))}
        </div>

        <div className="flex mb-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            className="flex-1 border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder={
              language === "hi"
                ? "Apna sawal likhiye ya boliye..."
                : "Type or speak your query..."
            }
          />
          <button
            onClick={sendMessage}
            className="ml-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg"
          >
            Send
          </button>
          <button
            onClick={startVoiceInput}
            className={`ml-2 px-3 py-2 rounded-lg ${
              isListening
                ? "bg-green-700 animate-pulse text-white"
                : "bg-green-600 hover:bg-green-700 text-white"
            }`}
          >
            🎤
          </button>
        </div>

        <div className="flex justify-center gap-3">
          <button
            onClick={() => setLanguage("en")}
            className={`px-3 py-1 rounded-full text-sm font-semibold ${
              language === "en"
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-700"
            }`}
          >
            English
          </button>
          <button
            onClick={() => setLanguage("hi")}
            className={`px-3 py-1 rounded-full text-sm font-semibold ${
              language === "hi"
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-700"
            }`}
          >
            हिंदी
          </button>
        </div>
      </div>
    </div>
  );
}
