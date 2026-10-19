import { EVA_BEDROCK_MODEL_IDS } from "./evaBedrockModels";

export const BEDROCK_MODELS = EVA_BEDROCK_MODEL_IDS;
export const DEFAULT_MODEL = "gpt-5-nano";

export function formatModelLabel(model: string) {
  return model.replace(/^us\./, "").replace(/-v\d+:\d+$/, "");
}
