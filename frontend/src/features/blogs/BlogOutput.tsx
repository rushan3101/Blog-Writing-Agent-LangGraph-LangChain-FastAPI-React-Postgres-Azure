import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";

interface Props {
  content?: string;
  isLoading?: boolean;

  onSave?: () => void;
  onDelete?: () => void;

  isSaving?: boolean;
  isSaved?: boolean;
  deleted?: boolean;
}

export default function BlogOutput({
  content,
  isLoading = false,
  onSave,
  onDelete,
  isSaving,
  isSaved,
  deleted,
}: Props) {

  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {

      if (!content) return;

      await navigator.clipboard.writeText(
        content
      );

      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 2000);
    };

  if (isLoading) {
    return (
      <div className="min-h-150 rounded-xl border border-gray-800 bg-gray-900 p-10">
        <div className="space-y-5">
          <div className="h-10 w-3/4 animate-pulse rounded bg-gray-800" />

          <div className="h-4 w-1/4 animate-pulse rounded bg-gray-800" />

          <div className="mt-10 h-4 animate-pulse rounded bg-gray-800" />
          <div className="h-4 animate-pulse rounded bg-gray-800" />
          <div className="h-4 w-5/6 animate-pulse rounded bg-gray-800" />

          <div className="mt-8 h-8 w-1/2 animate-pulse rounded bg-gray-800" />

          <div className="h-4 animate-pulse rounded bg-gray-800" />
          <div className="h-4 animate-pulse rounded bg-gray-800" />
          <div className="h-4 w-2/3 animate-pulse rounded bg-gray-800" />

          <div className="mt-8 h-8 w-1/3 animate-pulse rounded bg-gray-800" />

          <div className="h-4 animate-pulse rounded bg-gray-800" />
          <div className="h-4 animate-pulse rounded bg-gray-800" />
          <div className="h-4 w-4/5 animate-pulse rounded bg-gray-800" />
        </div>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 text-gray-400">
        Generate a blog to see the result.
      </div>
    );
  }

  return (
  <div className="rounded-xl border border-gray-800 bg-gray-900">

      <div className="flex items-center justify-between border-b border-gray-800 p-4">

        <h2 className="text-lg font-semibold text-white">
          Generated Blog
        </h2>

        <div className="flex gap-2">

          <button
            onClick={handleCopy}
            className="rounded-lg bg-gray-700 px-4 py-2 text-sm text-white hover:bg-gray-600"
          >
            {copied ? "Copied ✓" : "Copy"}
          </button>

          <button
            onClick={onSave}
            disabled={isSaving}
            className="rounded-lg bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-500 disabled:opacity-50"
          >
            {isSaving
              ? "Saving..."
              : isSaved
                ? "Saved ✓"
                : "Save"}
          </button>

          <button
            onClick={onDelete}

            disabled={deleted}

            className="
              rounded-lg
              bg-red-600
              px-4
              py-2
              text-white
              hover:bg-red-500
              disabled:opacity-50
            "
          >

            {deleted
              ? "Deleted ✓"
              : "Delete"}

          </button>

        </div>

      </div>

      <div className="prose prose-invert max-w-none min-h-150 p-10">

        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{

                img: ({ src, alt }) => (
                  <img
                    src={src}
                    alt={alt}
                    className="mx-auto my-2 mb-2 w-0.8 rounded-xl border-2 border-gray-700"
                  />
                ),
              }}
        >
          {content}
        </ReactMarkdown>

      </div>

    </div>
  );
}