import { useState } from "react";
import {
  BookOpen,
  Info,
  ShieldAlert,
  Brain,
  Camera,
  Layers,
  ChevronRight,
  Search,
  X,
} from "lucide-react";

const SUPPORTED_CONDITIONS = [
  {
    id: "acne_vulgaris",
    name: "Acne Vulgaris",
    overview: "A common inflammatory dermatosis of the pilosebaceous units characterized by comedones, papules, pustules, and potential cyst formation.",
    distribution: "Face, neck, chest, upper back, and shoulders.",
    keyPoints: [
      "Driven by follicular hyperkeratinization, excess sebum production, and Cutibacterium acnes colonization.",
      "Varies from mild comedonal acne to severe nodulocystic disease with scarring risk.",
    ],
  },
  {
    id: "impetigo",
    name: "Impetigo",
    overview: "A highly contagious superficial bacterial skin infection typically caused by Staphylococcus aureus or Streptococcus pyogenes.",
    distribution: "Frequently around the mouth, nose, and exposed extremities.",
    keyPoints: [
      "Classical 'honey-colored' crusting overlying erythematous superficial erosions.",
      "Readily transmissible through direct contact; requires clinical medical evaluation for topical or oral antibiotics.",
    ],
  },
  {
    id: "molluscum_contagiosum",
    name: "Molluscum Contagiosum",
    overview: "A benign viral infection of the epidermis caused by a poxvirus (Molluscum Contagiosum Virus).",
    distribution: "Trunk, axillae, antecubital fossae, and extremities.",
    keyPoints: [
      "Discrete, firm, dome-shaped papules with characteristic central umbilication.",
      "Self-limiting over months to years, though spread is accelerated by scratching or eczema.",
    ],
  },
  {
    id: "psoriasis",
    name: "Psoriasis",
    overview: "A chronic, immune-mediated inflammatory skin disorder characterized by accelerated epidermal cell proliferation.",
    distribution: "Extensor surfaces (elbows, knees), scalp, sacrum, and nails.",
    keyPoints: [
      "Sharply demarcated erythematous plaques covered by silvery-white micaceous scales.",
      "May be associated with systemic inflammatory comorbidities including psoriatic arthritis.",
    ],
  },
  {
    id: "urticaria",
    name: "Urticaria (Hives)",
    overview: "A vascular reaction pattern presenting with transient, pruritic, erythematous edematous wheals.",
    distribution: "Generalized; can appear on any bodily surface and rapidly shifts in distribution.",
    keyPoints: [
      "Individual wheals typically resolve within 24 hours without leaving permanent marks.",
      "If accompanied by lip/tongue swelling, stridor, or difficulty breathing (anaphylaxis), urgent emergency care is mandatory.",
    ],
  },
  {
    id: "vitiligo",
    name: "Vitiligo",
    overview: "An acquired autoimmune disorder resulting in the progressive destruction of melanocytes and loss of epidermal pigment.",
    distribution: "Periorificial areas (eyes, mouth), hands, wrists, feet, and extensor surfaces.",
    keyPoints: [
      "Well-demarcated, depigmented (chalk-white) macules and patches without surface scaling.",
      "Non-contagious; psychological impact and sun protection on depigmented skin are primary considerations.",
    ],
  },
  {
    id: "warts",
    name: "Warts (Verrucae)",
    overview: "Benign epidermal proliferations caused by infection with various subtypes of the Human Papillomavirus (HPV).",
    distribution: "Fingers, hands, periungual regions, soles of feet (plantar warts), and knees.",
    keyPoints: [
      "Hyperkeratotic, verrucous papules with characteristic pinpoint black dots (thrombosed capillary loops).",
      "Spread via micro-abrasions in the skin; harmless but frequently persistent.",
    ],
  },
];

export default function LearnView() {
  const [selectedCondition, setSelectedCondition] = useState(SUPPORTED_CONDITIONS[0]);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredConditions = SUPPORTED_CONDITIONS.filter((cond) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      cond.name.toLowerCase().includes(q) ||
      cond.overview.toLowerCase().includes(q) ||
      cond.distribution.toLowerCase().includes(q)
    );
  });

  const activeCondition =
    filteredConditions.find((c) => c.id === selectedCondition.id) ||
    filteredConditions[0] ||
    SUPPORTED_CONDITIONS[0];

  return (
    <div className="learn-container">
      {/* Editorial Header */}
      <div className="learn-header">
        <div className="learn-badge">
          <BookOpen size={15} />
          <span>CLINICAL KNOWLEDGE BASE</span>
        </div>
        <h2>Dermatological Education & AI Literacy</h2>
        <p>
          Understand the 7 supported skin condition categories, interpret model explainability,
          and learn when professional clinical consultation is essential.
        </p>
      </div>

      {/* Guide Pillars */}
      <div className="learn-pillars-grid">
        <div className="pillar-card">
          <div className="pillar-icon-box">
            <Brain size={20} />
          </div>
          <h4>Model Boundaries</h4>
          <p>
            The EfficientNet-B0 network is trained exclusively on seven skin condition classes.
            It cannot detect conditions outside this scope (e.g. melanoma, basal cell carcinoma, or eczema).
          </p>
        </div>

        <div className="pillar-card">
          <div className="pillar-icon-box">
            <Layers size={20} />
          </div>
          <h4>Grad-CAM Explainability</h4>
          <p>
            Gradient-weighted Class Activation Mapping displays visual heatmaps of pixels that most influenced
            the neural network. It does not demarcate exact biopsy boundaries.
          </p>
        </div>

        <div className="pillar-card">
          <div className="pillar-icon-box">
            <Camera size={20} />
          </div>
          <h4>Quality & Optical Factors</h4>
          <p>
            Lens blur, low lighting, and digital compression directly degrade classification reliability.
            Clear, focused macro photography ensures consistent computational feature extraction.
          </p>
        </div>

        <div className="pillar-card pillar-card-alert">
          <div className="pillar-icon-box icon-box-alert">
            <ShieldAlert size={20} />
          </div>
          <h4>Emergency Red Flags</h4>
          <p>
            Lesions accompanied by high fever, rapid mucosal or facial swelling, difficulty breathing,
            or spreading cellulitis require immediate emergency medical evaluation.
          </p>
        </div>
      </div>

      {/* Interactive Condition Catalog */}
      <div className="learn-catalog-section">
        <div className="catalog-section-header">
          <div>
            <span className="section-eyebrow">DIAGNOSTIC SCOPE</span>
            <h3 className="section-title">The 7 Supported Condition Classes</h3>
          </div>
          <p className="catalog-subtitle">
            Select a condition below to review clinical descriptions, typical anatomical distributions, and key features.
          </p>

          <div className="learn-search-bar">
            <Search size={15} className="search-icon" aria-hidden="true" />
            <input
              type="text"
              placeholder="Search conditions, descriptions, or distribution..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Filter supported conditions"
            />
            {searchQuery && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={() => setSearchQuery("")}
                aria-label="Clear search"
              >
                <X size={14} aria-hidden="true" />
              </button>
            )}
          </div>
        </div>

        <div className="catalog-layout">
          <div className="catalog-nav-list" role="tablist" aria-label="Supported skin conditions">
            {filteredConditions.length === 0 ? (
              <p className="no-conditions-found">No conditions match "{searchQuery}".</p>
            ) : (
              filteredConditions.map((cond) => {
                const isSelected = activeCondition.id === cond.id;
                return (
                  <button
                    key={cond.id}
                    type="button"
                    role="tab"
                    aria-selected={isSelected}
                    className={`catalog-tab-btn ${isSelected ? "active" : ""}`}
                    onClick={() => setSelectedCondition(cond)}
                  >
                    <div className="tab-btn-content">
                      <strong>{cond.name}</strong>
                      <span>{cond.distribution}</span>
                    </div>
                    <ChevronRight size={16} className="tab-arrow" />
                  </button>
                );
              })
            )}
          </div>

          <div className="catalog-detail-panel" role="tabpanel">
            <div className="detail-panel-header">
              <span className="detail-panel-tag">Condition Profile</span>
              <h3>{activeCondition.name}</h3>
            </div>

            <div className="detail-block">
              <h5>Clinical Overview</h5>
              <p>{activeCondition.overview}</p>
            </div>

            <div className="detail-block">
              <h5>Typical Anatomical Locations</h5>
              <p>{activeCondition.distribution}</p>
            </div>

            <div className="detail-block">
              <h5>Key Clinical Observations</h5>
              <ul className="detail-bullet-list">
                {activeCondition.keyPoints.map((pt, idx) => (
                  <li key={idx}>{pt}</li>
                ))}
              </ul>
            </div>

            <div className="detail-notice-box">
              <Info size={16} />
              <span>
                Educational reference only. A definitive dermatological diagnosis requires in-person clinical examination,
                dermoscopy, and histopathology when indicated.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
