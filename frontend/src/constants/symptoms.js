export const INITIAL_SYMPTOMS = {
  duration: "",
  location: "",
  spreading: null,
  itching: null,
  pain: null,
  burning: null,
  swelling: null,
  bleeding: null,
  discharge: null,
  blisters: null,
  fever: null,
  sensitiveArea: null,
  previousOccurrence: null,
  newExposure: null,
};

export const BOOLEAN_QUESTIONS = [
  {
    group: "Sensations & Progression",
    questions: [
      { key: "spreading", label: "Is the condition spreading or expanding?" },
      { key: "itching", label: "Is it itchy?" },
      { key: "pain", label: "Is it painful or tender?" },
      { key: "burning", label: "Is there a burning or stinging sensation?" },
      { key: "swelling", label: "Is there swelling or puffiness?" },
    ],
  },
  {
    group: "Lesion Characteristics",
    questions: [
      { key: "bleeding", label: "Is there bleeding or skin breakdown?" },
      { key: "discharge", label: "Is there discharge, pus, or weeping?" },
      { key: "blisters", label: "Are there blisters or fluid-filled bumps?" },
    ],
  },
  {
    group: "Context & Systemic Signs",
    questions: [
      { key: "fever", label: "Do you have a fever or chills?" },
      { key: "sensitiveArea", label: "Does it involve sensitive areas (eyes, mouth, lips, genitals)?" },
      { key: "previousOccurrence", label: "Has this condition occurred before?" },
      { key: "newExposure", label: "Was there a new product, medication, or chemical exposure?" },
    ],
  },
];

export function countAnsweredSymptoms(symptoms) {
  if (!symptoms) return 0;
  let count = 0;
  if (typeof symptoms.duration === "string" && symptoms.duration.trim()) count++;
  if (typeof symptoms.location === "string" && symptoms.location.trim()) count++;

  const boolKeys = [
    "spreading", "itching", "pain", "burning", "swelling", "bleeding",
    "discharge", "blisters", "fever", "sensitiveArea", "previousOccurrence", "newExposure"
  ];
  for (const key of boolKeys) {
    if (symptoms[key] === true || symptoms[key] === false) {
      count++;
    }
  }
  return count;
}
