interface Props {
  activeTab: string;
  onChange: (tab: string) => void;
}

const tabs = [
  "Blog",
  "Plan",
  "Evidence",
  "Images",
  "Logs",
];

export default function Tabs({
  activeTab,
  onChange,
}: Props) {
  return (
    <div className="mb-6 flex gap-2 border-b border-gray-800">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onChange(tab)}
          className={`px-4 py-3 text-sm font-medium transition
            ${
              activeTab === tab
                ? "border-b-2 border-blue-500 text-white"
                : "text-gray-400 hover:text-white"
            }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}