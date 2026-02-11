/**
 * Mock data for TahalilAI results page.
 * Simulates a complete blood count (CBC) report analysis.
 */

export type TestStatus = "normal" | "warning" | "alert";

export interface TestResult {
  id: string;
  name: string;
  value: number;
  unit: string;
  normalRange: string;
  status: TestStatus;
  explanation: string;
}

export interface AnalysisResult {
  overallStatus: TestStatus;
  tests: TestResult[];
  summary: string;
}

export const mockResults: AnalysisResult = {
  overallStatus: "warning",
  tests: [
    {
      id: "hgb",
      name: "Hemoglobin (HGB)",
      value: 13.5,
      unit: "g/dL",
      normalRange: "12.0 – 17.5 g/dL",
      status: "normal",
      explanation:
        "Your hemoglobin level is within the normal range. Hemoglobin is the protein in your red blood cells that carries oxygen throughout your body. A normal level means your blood is carrying oxygen effectively.",
    },
    {
      id: "wbc",
      name: "White Blood Cells (WBC)",
      value: 11.8,
      unit: "×10³/µL",
      normalRange: "4.5 – 11.0 ×10³/µL",
      status: "warning",
      explanation:
        "Your white blood cell count is slightly above the normal range. White blood cells help your body fight infections. A mildly elevated count can sometimes be related to stress, recent exercise, or a minor infection. It's worth monitoring at your next check-up.",
    },
    {
      id: "plt",
      name: "Platelets (PLT)",
      value: 245,
      unit: "×10³/µL",
      normalRange: "150 – 400 ×10³/µL",
      status: "normal",
      explanation:
        "Your platelet count is within the normal range. Platelets help your blood clot properly. A normal count means your body's clotting ability is working as expected.",
    },
    {
      id: "rbc",
      name: "Red Blood Cells (RBC)",
      value: 4.9,
      unit: "×10⁶/µL",
      normalRange: "4.5 – 5.5 ×10⁶/µL",
      status: "normal",
      explanation:
        "Your red blood cell count is normal. Red blood cells carry oxygen from your lungs to the rest of your body. This level indicates healthy oxygen transport.",
    },
    {
      id: "glu",
      name: "Fasting Glucose",
      value: 108,
      unit: "mg/dL",
      normalRange: "70 – 100 mg/dL",
      status: "warning",
      explanation:
        "Your fasting glucose is slightly above the normal range. This doesn't necessarily mean a problem, but it may suggest pre-diabetic levels. It's a good idea to discuss this with your doctor and consider lifestyle factors like diet and exercise.",
    },
    {
      id: "chol",
      name: "Total Cholesterol",
      value: 242,
      unit: "mg/dL",
      normalRange: "< 200 mg/dL",
      status: "alert",
      explanation:
        "Your total cholesterol is above the recommended level. Cholesterol is a fat-like substance in your blood. Higher levels may increase the risk of heart-related conditions over time. We recommend discussing this result with your doctor, who can provide personalized guidance.",
    },
  ],
  summary:
    "Most of your results fall within the expected ranges, which is reassuring. A couple of values — your white blood cell count and fasting glucose — are slightly elevated. Your total cholesterol is above the recommended threshold. These findings don't indicate an emergency, but they are worth discussing with your healthcare provider at your next visit. Small lifestyle adjustments, such as a balanced diet and regular activity, can often help improve these numbers over time.",
};
