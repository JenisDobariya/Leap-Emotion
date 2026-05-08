/* ---- Nav scroll shadow ---- */
const nav = document.getElementById('main-nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 20);
});

/* ---- Demo widget emotion data ---- */
const emotions = {
  joy: {
    bars: { joy: 82, surprise: 45, neutral: 20, sadness: 5, anger: 3 },
    mouth: "M48 82 Q65 97 82 82",
    browL: "M38 43 Q46 39 54 43",
    browR: "M76 43 Q84 39 92 43",
    cheek: "0.65",
    insight: "Subject displays strong positive engagement. Confidence: 94%. Micro-expressions suggest genuine emotional response rather than performed happiness."
  },
  sadness: {
    bars: { joy: 8, surprise: 12, neutral: 25, sadness: 78, anger: 10 },
    mouth: "M48 88 Q65 78 82 88",
    browL: "M38 47 Q46 43 54 45",
    browR: "M76 45 Q84 43 92 47",
    cheek: "0.08",
    insight: "Downward lip corners and reduced brow tension detected. Emotional profile consistent with sadness and low mood. Confidence: 89%."
  },
  anger: {
    bars: { joy: 5, surprise: 15, neutral: 12, sadness: 8, anger: 88 },
    mouth: "M48 86 Q65 82 82 86",
    browL: "M38 46 Q46 41 54 47",
    browR: "M76 47 Q84 41 92 46",
    cheek: "0.12",
    insight: "Elevated stress markers detected. Brow furrowing and jaw tension indicate heightened frustration or anger. Confidence: 91%."
  },
  surprise: {
    bars: { joy: 35, surprise: 85, neutral: 15, sadness: 5, anger: 2 },
    mouth: "M50 80 Q65 95 80 80",
    browL: "M36 39 Q46 33 54 39",
    browR: "M76 39 Q84 33 94 39",
    cheek: "0.25",
    insight: "Strong surprise response detected. Raised brows and parted lips indicate reaction to an unexpected stimulus. Confidence: 92%."
  },
  fear: {
    bars: { joy: 4, surprise: 60, neutral: 18, sadness: 30, anger: 6 },
    mouth: "M50 86 Q65 80 80 86",
    browL: "M36 40 Q46 35 54 41",
    browR: "M76 41 Q84 35 94 40",
    cheek: "0.05",
    insight: "Fear and anxiety markers present. Wide eye aperture with raised inner brow is a classic fear indicator. Confidence: 87%."
  },
  neutral: {
    bars: { joy: 18, surprise: 10, neutral: 82, sadness: 12, anger: 6 },
    mouth: "M48 84 Q65 86 82 84",
    browL: "M38 43 Q46 41 54 43",
    browR: "M76 43 Q84 41 92 43",
    cheek: "0.04",
    insight: "Neutral baseline detected. No strong emotional indicators present. Subject appears relaxed and attentive. Confidence: 96%."
  }
};

function setEmo(name, btn) {
  document.querySelectorAll('.emo-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const e = emotions[name];
  Object.keys(e.bars).forEach(k => {
    const bar = document.getElementById('b-' + k);
    const pct = document.getElementById('p-' + k);
    if (bar) bar.style.width = e.bars[k] + '%';
    if (pct) pct.textContent = e.bars[k] + '%';
  });
  document.getElementById('mouth').setAttribute('d', e.mouth);
  document.getElementById('brow-l').setAttribute('d', e.browL);
  document.getElementById('brow-r').setAttribute('d', e.browR);
  document.getElementById('cheek-l').style.opacity = e.cheek;
  document.getElementById('cheek-r').style.opacity = e.cheek;
  document.getElementById('insight-text').textContent = e.insight;
}