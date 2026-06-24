import { useState } from "react";
import { streamBlog } from "./blogApi";

interface Props {
  onLoadingChange: (loading: boolean) => void;
  onStreamEvent: (event: any) => void;
  isStreaming: boolean;
}

export default function GenerateBlogForm({
  onLoadingChange,
  onStreamEvent,
  isStreaming,
}: Props) {
  const [topic, setTopic] = useState("");
  const [asOf, setAsOf] = useState("");
  const isValid = topic.trim().length > 0 && asOf.length > 0;

  const handleSubmit = async () => {

      onLoadingChange(true);

      try {

        await streamBlog(
          {
            topic,
            as_of: asOf,
          },

          (event) => {

            onStreamEvent(event);
          }
        );

      } catch (error) {

        console.error(error);

        onLoadingChange(
          false
        );
      }
  };

  return (
  <div className="mb-8 flex gap-4">
    <input
      type="text"
      placeholder="Enter the Topic of the Blog"
      value={topic}
      onChange={(e) => setTopic(e.target.value)}
      className="flex-1 rounded-lg border border-gray-700 bg-gray-900 px-4 py-3 text-white"
    />

    <input
      type="date"
      value={asOf}
      onChange={(e) => setAsOf(e.target.value)}
      className="rounded-lg border border-gray-700 bg-gray-900 px-4 py-3 text-white"
    />

    <button
      onClick={handleSubmit}
      disabled={!isValid || isStreaming}
      className="rounded-lg bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-500 disabled:opacity-50"
    >
      {isStreaming
        ? "Generating..."
        : "Generate Blog"}
    </button>
  </div>
  );
}