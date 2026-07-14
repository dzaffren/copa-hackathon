import { SOURCE_TYPE_DOT, SOURCE_TYPE_LABEL } from "@/lib/labels";
import type { SourceType } from "@/lib/types";

/** A coloured dot keying a source to its type; the legend and rail share it. */
export function SourceTypeDot({ type }: { type: SourceType }) {
  return (
    <span
      className={`inline-block h-2.5 w-2.5 shrink-0 rounded-full ${SOURCE_TYPE_DOT[type]}`}
      role="img"
      aria-label={SOURCE_TYPE_LABEL[type]}
      title={SOURCE_TYPE_LABEL[type]}
    />
  );
}
