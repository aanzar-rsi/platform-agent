export const TOOL_BUCKET_ALL_ID = "__all__";
/** User changed individual tools; selection may not match a saved bucket. */
export const TOOL_BUCKET_MIXED_ID = "__mixed__";
export const LS_TOOL_BUCKETS = "eva_tool_buckets_v1";
export const LS_ACTIVE_TOOL_BUCKET = "eva_active_tool_bucket_v1";

export interface ToolBucketDef {
  id: string;
  name: string;
  toolNames: string[];
}
